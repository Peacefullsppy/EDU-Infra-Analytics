"""Restrições que devem ser executadas no PostgreSQL real, em DB descartável de CI."""
import os
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core import engine

pytestmark=[pytest.mark.integration,pytest.mark.postgres,
    pytest.mark.skipif(os.getenv('EDU_TEST_POSTGRES_DISPOSABLE')!='SIM' or engine.dialect.name!='postgresql',
        reason='Exige PostgreSQL descartável explicitamente autorizado')]


def add_lab(conn,name,location):
    return conn.execute(text('''INSERT INTO laboratories
        (name,location,name_key,location_key,active,created_at)
        VALUES (:name,:location,:nk,:lk,TRUE,CURRENT_TIMESTAMP) RETURNING id'''),
        {'name':name,'location':location,'nk':name.casefold(),'lk':location.casefold()}).scalar_one()


def add_computer(conn,lab_id,hostname,hyperv_vm_id=None):
    return conn.execute(text('''INSERT INTO computers
        (laboratory_id,name,hostname,active,source,hyperv_vm_id,created_at)
        VALUES (:lab,'CI Test Device',:host,TRUE,'manual',:vm,CURRENT_TIMESTAMP) RETURNING id'''),
        {'lab':lab_id,'host':hostname,'vm':hyperv_vm_id}).scalar_one()


@pytest.mark.parametrize('case', ['same-lab','same-lab-different-location'])
def test_postgres_lab_unique_composite_constraint(case):
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            add_lab(conn,'CI Unique Lab','Sala 1')
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    add_lab(conn,'CI Unique Lab','Sala 1')
            if case=='same-lab-different-location':
                assert add_lab(conn,'CI Unique Lab','Sala 2')>0
        finally:
            transaction.rollback()


def test_postgres_rejects_orphan_computer_foreign_key():
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    add_computer(conn,2147483647,'ci-orphan')
        finally:
            transaction.rollback()


def test_postgres_prevents_duplicate_hostname_per_lab():
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            lid=add_lab(conn,'CI Lab Host Unique','Sala A')
            add_computer(conn,lid,'ci-host-unique')
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    add_computer(conn,lid,'ci-host-unique')
        finally:
            transaction.rollback()


def test_postgres_protects_hyperv_guid_unique_across_labs():
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            a=add_lab(conn,'CI Lab VM A','Sala A')
            b=add_lab(conn,'CI Lab VM B','Sala B')
            vmid='ci-e2e-disposable-only-guid'
            add_computer(conn,a,'host-a',hyperv_vm_id=vmid)
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    add_computer(conn,b,'host-b',hyperv_vm_id=vmid)
        finally:
            transaction.rollback()


def test_postgres_restrict_lab_deletion_with_associated_device():
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            lid=add_lab(conn,'CI Lab FK Restrict','Sala')
            add_computer(conn,lid,'ci-device-fk')
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    conn.execute(text('DELETE FROM laboratories WHERE id=:id'),{'id':lid})
        finally:
            transaction.rollback()
