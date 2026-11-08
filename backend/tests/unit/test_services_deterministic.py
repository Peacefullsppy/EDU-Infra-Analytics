"""Cenários determinísticos de status, limites, IIE, cobertura e alertas."""
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select
from app.core import utcnow
from app.models import Laboratory, Computer, Metric, Alert, SystemSetting
from app.services import computer_status, indicator, system_settings, latest_metric, update_alerts

T0=datetime(2026,10,1,12,0,tzinfo=timezone.utc)


@pytest.mark.unit
@pytest.mark.parametrize('active,seconds_ago,stale,expected', [
    (False,None,600,'inactive'),(False,5,600,'inactive'),(True,None,600,'sem_coleta'),
    (True,0,600,'online'),(True,1,600,'online'),(True,599,600,'online'),
    (True,600,600,'online'),(True,601,600,'offline'),(True,10000,600,'offline'),
    (True,61,60,'offline'),(True,59,60,'online'),
])
def test_computer_status_boundaries(active,seconds_ago,stale,expected):
    pc=Computer(name='PC',hostname='vm',laboratory_id=1,active=active,
                last_seen_at=T0-timedelta(seconds=seconds_ago) if seconds_ago is not None else None)
    assert computer_status(pc,stale,now=T0) == expected


@pytest.mark.unit
@pytest.mark.parametrize('cpu,ram,disk,expected', [
    (0,0,0,100.0), (100,100,100,40.0), (20,40,60,76.6),
    (100,0,0,79.0), (0,100,0,79.0), (0,0,100,82.0),
])
def test_indicator_math_exact(client,cpu,ram,disk,expected):
    from app.models import SystemSetting
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala')
        db.add(lab);db.flush()
        pc=Computer(laboratory_id=lab.id,name='VM',hostname='VM1',active=True,last_seen_at=T0)
        db.add(pc);db.flush()
        db.add(Metric(computer_id=pc.id,cpu_percent=cpu,memory_percent=ram,disk_percent=disk,
                      uptime_seconds=10,os_name='Linux',collected_at=T0))
        db.commit()
        result=indicator(db,lab,now=T0)
        assert result['score']==pytest.approx(expected)
        assert result['coverage']==100
        assert result['online']==1


@pytest.mark.unit
@pytest.mark.parametrize('active_count,online_count', [(1,0),(2,1),(3,2),(4,1)])
def test_indicator_coverage_counts_only_observed_online(client,active_count,online_count):
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala')
        db.add(lab);db.flush()
        for index in range(active_count):
            online=index < online_count
            pc=Computer(laboratory_id=lab.id,name=f'pc {index}',hostname=f'vm{index}',active=True,
                        last_seen_at=T0 if online else None)
            db.add(pc);db.flush()
            if online:
                db.add(Metric(computer_id=pc.id,cpu_percent=40,memory_percent=40,disk_percent=40,
                              uptime_seconds=10,os_name='Linux',collected_at=T0))
        db.commit()
        result=indicator(db,lab,now=T0)
        assert result['online']==online_count
        assert result['sem_coleta']==active_count-online_count
        assert result['coverage']==round(100*online_count/active_count,2)
        if online_count==0: assert result['score'] is None
        else: assert result['score'] == pytest.approx(round((40+36)*online_count/active_count,2))


@pytest.mark.unit
@pytest.mark.parametrize('cpu,ram,disk,classification', [
    (0,0,0,'adequado'),(40,40,40,'adequado'),
    (75,75,75,'atencao'), (100,100,100,'critico'),
])
def test_indicator_classification(client,cpu,ram,disk,classification):
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala')
        db.add(lab);db.flush()
        pc=Computer(laboratory_id=lab.id,name='vm',hostname='vm',last_seen_at=T0)
        db.add(pc);db.flush()
        db.add(Metric(computer_id=pc.id,cpu_percent=cpu,memory_percent=ram,disk_percent=disk,
                      uptime_seconds=1,os_name='Linux',collected_at=T0));db.commit()
        # With one online computer, score minimum is 40; critical at 100 usage.
        assert indicator(db,lab,now=T0)['classification'] == classification


@pytest.mark.unit
def test_indicator_no_labs_and_no_devices(client):
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala')
        db.add(lab);db.commit()
        item=indicator(db,lab,now=T0)
        assert item['score'] is None and item['total']==0 and item['classification']=='sem_dados'


@pytest.mark.unit
def test_system_settings_can_recreate_defaults(client):
    with client.Session() as db:
        db.delete(db.get(SystemSetting,1));db.commit()
        cfg=system_settings(db)
        assert cfg.cpu_alert_threshold == 90
        assert cfg.stale_after_seconds == 600
        db.commit()
        assert db.get(SystemSetting,1) is not None


@pytest.mark.unit
def test_latest_metric_uses_collection_time_not_insert_order(client):
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala');db.add(lab);db.flush()
        pc=Computer(laboratory_id=lab.id,name='vm',hostname='vm');db.add(pc);db.flush()
        db.add(Metric(computer_id=pc.id,cpu_percent=20,memory_percent=20,disk_percent=20,uptime_seconds=10,os_name='Linux',collected_at=T0))
        db.add(Metric(computer_id=pc.id,cpu_percent=90,memory_percent=20,disk_percent=20,uptime_seconds=10,os_name='Linux',collected_at=T0-timedelta(hours=2)))
        db.commit()
        assert latest_metric(db,pc.id).cpu_percent==20


@pytest.mark.unit
@pytest.mark.parametrize('kind,value,expected_severity', [
    ('cpu',90,'warning'),('cpu',96.9,'warning'),('cpu',97,'critical'),
    ('memory',90,'warning'),('memory',99,'critical'),('disk',100,'critical')
])
def test_alert_severity_boundaries(client,kind,value,expected_severity):
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala');db.add(lab);db.flush()
        pc=Computer(laboratory_id=lab.id,name='VM',hostname='vm');db.add(pc);db.flush()
        m=Metric(computer_id=pc.id,cpu_percent=20,memory_percent=20,disk_percent=20,
                 uptime_seconds=20,os_name='Linux',collected_at=T0)
        setattr(m,{'cpu':'cpu_percent','memory':'memory_percent','disk':'disk_percent'}[kind],value)
        update_alerts(db,pc.id,m);db.flush()
        alerts=db.scalars(select(Alert)).all()
        assert len(alerts)==1 and alerts[0].type==kind and alerts[0].severity==expected_severity


@pytest.mark.unit
@pytest.mark.parametrize('recovery,expected_state', [(89.9,'open'),(85,'open'),(84.9,'resolved'),(0,'resolved')])
def test_alert_hysteresis_prevents_flapping(client,recovery,expected_state):
    with client.Session() as db:
        lab=Laboratory(name='Lab',location='Sala',name_key='lab',location_key='sala');db.add(lab);db.flush()
        pc=Computer(laboratory_id=lab.id,name='VM',hostname='vm');db.add(pc);db.flush()
        def metric(cpu):
            return Metric(computer_id=pc.id,cpu_percent=cpu,memory_percent=10,disk_percent=10,uptime_seconds=10,os_name='Linux',collected_at=T0)
        update_alerts(db,pc.id,metric(99));db.flush()
        update_alerts(db,pc.id,metric(recovery));db.flush()
        a=db.scalars(select(Alert)).one()
        assert a.status==expected_state
