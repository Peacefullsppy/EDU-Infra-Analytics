import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {
  Activity, AlertCircle, AlertTriangle, ArrowDownToLine, ArrowRight, BarChart3,
  Bell, BookOpenCheck, CalendarDays, Check, CheckCircle2, ChevronDown, ChevronRight,
  ClipboardCheck, Clock3, Cpu, Database, Download, Edit3, Eye, FileBarChart2,
  FileText, Gauge, HardDrive, Info, KeyRound, LayoutDashboard, LockKeyhole,
  LogOut, Menu, Monitor, MoreHorizontal, Plus, Power, RefreshCw, RotateCcw,
  Save, Search, Server, Settings2, ShieldCheck, Trash2, TrendingUp, UploadCloud,
  UserRound, Users, Wifi, WifiOff, X
} from 'lucide-react';
import {getToken, setToken, request, download} from './api.js';
import Brand from './components/Brand.jsx';
import {number, dateTime, clockTime, Empty, Badge, StatCard, DonutChart, MetricTrend, LaboratoryBars, ScoreTrend} from './components/Visuals.jsx';

const NAV = [
  ['dashboard','Dashboard',LayoutDashboard],
  ['laboratories','Laboratórios',Server],
  ['computers','Computadores',Monitor],
  ['indicators','Indicadores',TrendingUp],
  ['alerts','Alertas',Bell],
  ['reports','Relatórios',FileText],
  ['settings','Configurações',Settings2],
  ['users','Usuários',Users],
];
const ROLES={ADMIN:'Administrador',TECNICO:'Técnico',GESTOR:'Gestor'};
const canEdit=user=>['ADMIN','TECNICO'].includes(user?.role);
const message=e=>e?.message || 'Não foi possível concluir a operação.';
const friendlyDate=()=>new Date().toLocaleDateString('pt-BR',{day:'numeric',month:'long',year:'numeric'});
const clamp=n=>Math.min(100,Math.max(0,Number(n)||0));
const statusCounts=pcs=>({
  online:pcs.filter(c=>c.status==='online').length,
  offline:pcs.filter(c=>c.status==='offline').length,
  unknown:pcs.filter(c=>c.status==='sem_coleta').length,
  inactive:pcs.filter(c=>c.status==='inactive').length
});
const computerHealth=(computer,settings)=>{
  if(computer.status!=='online'||!computer.latest_metric)return computer.status;
  const m=computer.latest_metric;
  const v=[m.cpu_percent,m.memory_percent,m.disk_percent].map(Number);
  if(v.some(n=>n>=97))return 'critico';
  const lim=[settings?.cpu_alert_threshold??90,settings?.memory_alert_threshold??90,settings?.disk_alert_threshold??90];
  if(v.some((n,i)=>n>=lim[i]))return 'atencao';
  return 'online';
};

function useApiData(paths,interval=0){
  const key=paths.join('|');
  const [state,setState]=useState({data:null,error:'',loading:true});
  const load=useCallback(async({silent=false}={})=>{
    if(!silent)setState(s=>({...s,loading:true,error:''}));
    try {const data=await Promise.all(key.split('|').map(url=>request(url)));setState({data,error:'',loading:false});}
    catch(e){setState(s=>({...s,error:message(e),loading:false}));}
  },[key]);
  useEffect(()=>{load();if(!interval)return;const id=setInterval(()=>load({silent:true}),interval);return()=>clearInterval(id)},[load,interval]);
  return {...state,load};
}
function useHistory(computerId){
  const [data,setData]=useState([]);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  useEffect(()=>{
    if(!computerId){setData([]);return;}
    let live=true;setLoading(true);setData([]);setError('');
    request(`/api/computers/${computerId}/metrics?limit=100`).then(result=>{if(live)setData(result)}).catch(e=>{if(live)setError(message(e))}).finally(()=>{if(live)setLoading(false)});
    return()=>{live=false};
  },[computerId]);
  return {data,loading,error};
}
function Button({children,icon:Icon,kind='primary',className='',...props}){
  return <button className={`btn btn-${kind} ${className}`} {...props}>{Icon&&<Icon size={17}/>}<span>{children}</span></button>;
}
function Banner({children,type='error',onClose}){
  if(!children)return null;
  return <div className={`feedback feedback-${type}`} role={type==='error'?'alert':'status'}><span>{children}</span>{onClose&&<button className="small-icon" aria-label="Dispensar mensagem" onClick={onClose}><X size={16}/></button>}</div>;
}
function Field({label,children,hint}){
  return <label className="field"><span>{label}</span>{children}{hint&&<small>{hint}</small>}</label>;
}
function Modal({title,children,onClose,wide=false}){
  useEffect(()=>{const fn=e=>{if(e.key==='Escape')onClose()};window.addEventListener('keydown',fn);return()=>window.removeEventListener('keydown',fn)},[onClose]);
  return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose()}}><div className={`modal ${wide?'wide':''}`} role="dialog" aria-modal="true" aria-label={title}>
    <header className="modal-head"><h2>{title}</h2><button type="button" className="icon-btn" onClick={onClose} aria-label="Fechar janela"><X size={20}/></button></header>{children}
  </div></div>;
}
function PageTitle({title,description,action,eyebrow}){
  return <header className="page-title"><div><p className="page-eyebrow">{eyebrow||'EDU-INFRA ANALYTICS 1.6'}</p><h1>{title}</h1>{description&&<p className="page-description">{description}</p>}</div><div className="page-title-right"><span className="date-chip"><CalendarDays size={17}/>{friendlyDate()}<ChevronDown size={14}/></span>{action&&<div className="page-actions">{action}</div>}</div></header>;
}
function Panel({title,description,action,children,className=''}){
  return <section className={`panel ${className}`}><div className="panel-header"><div><h2>{title}</h2>{description&&<p>{description}</p>}</div>{action&&<div className="panel-actions">{action}</div>}</div>{children}</section>;
}
function PanelLink({children,onClick}){return <button type="button" className="panel-link" onClick={onClick}>{children}<ChevronRight size={16}/></button>}
function PanelLoader({loading}){return loading?<div className="loading-layer"><span className="loading-spinner"/> Carregando dados...</div>:null}
function SearchBox({value,onChange,placeholder='Pesquisar...'}){
  return <label className="search-control"><Search size={18}/><input aria-label="Pesquisar" placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}/></label>;
}
function LabSummaryTable({items=[],navigate}){
  return items.length?<div className="table-scroll"><table className="data-table lab-summary-table"><thead><tr><th>Laboratório</th><th>Equipamentos</th><th>Online</th><th>Problemas</th><th>IIE</th><th>Status</th></tr></thead><tbody>{items.map(l=><tr key={l.laboratory_id} className={navigate?'clickable-row':''} onClick={navigate?()=>navigate('laboratories'):undefined}><td><div className="lab-cell"><span className="lab-cell-icon"><Server size={19}/></span><strong>{l.laboratory}</strong></div></td><td>{l.total}</td><td><strong>{l.online}</strong><span className="cell-second">({l.total?Math.round(l.online/l.total*100):0}%)</span></td><td className={(l.offline+l.sem_coleta)>0?'text-red':''}>{l.offline+l.sem_coleta}</td><td className={l.score==null?'text-muted':l.score>=75?'text-green':l.score>=50?'text-orange':'text-red'}><strong>{number(l.score)}</strong></td><td><Badge status={l.classification}/></td></tr>)}</tbody></table></div>
  :<Empty compact icon={Server} title="Sem laboratórios" description="Cadastre ambientes para acompanhar a infraestrutura."/>;
}
function AlertFeed({alerts=[],pcs=[],onAll}){
  const names=new Map(pcs.map(c=>[c.id,c.name]));
  return <div className="alert-feed">{alerts.length?alerts.slice(0,5).map(a=><article className="alert-feed-row" key={a.id}><span className={`alert-bubble ${a.severity==='critical'?'critical':'warning'}`}><AlertTriangle size={22}/></span><div><strong>{names.get(a.computer_id)||`Computador #${a.computer_id}`}</strong><p>{a.message}</p></div><time>{clockTime(a.created_at)}</time></article>):<Empty compact icon={CheckCircle2} title="Nenhum alerta recente" description="As ocorrências aparecerão quando algum limite for atingido."/>}{onAll&&<div className="feed-footer"><PanelLink onClick={onAll}>Ver todos os alertas</PanelLink></div>}</div>;
}
function AvailabilityPanel({pcs=[]}){
  return <Panel title="Distribuição por status"><DonutChart {...statusCounts(pcs)}/></Panel>;
}
function MetricPanel({pcs=[]}){
  const available=pcs.filter(c=>c.latest_metric);
  const [selected,setSelected]=useState('');
  useEffect(()=>{if(available.length&&!available.some(p=>String(p.id)===String(selected)))setSelected(String(available[0].id));if(!available.length)setSelected('')},[pcs,selected]);
  const {data,loading,error}=useHistory(selected);
  return <Panel title="Desempenho dos equipamentos" description="Histórico real do equipamento selecionado" action={available.length>0&&<select className="mini-select" aria-label="Selecionar equipamento para o gráfico" value={selected} onChange={e=>setSelected(e.target.value)}>{available.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select>}>
    <Banner>{error}</Banner><PanelLoader loading={loading}/><MetricTrend samples={data}/>
  </Panel>;
}

function Dashboard({navigate}){
  const {data,error,loading,load}=useApiData(['/api/dashboard/summary','/api/computers','/api/alerts'],60000);
  const summary=data?.[0],pcs=data?.[1]||[],alerts=data?.[2]||[];
  const activeAlerts=alerts.filter(a=>a.status!=='resolved');
  const info=summary?.indicators||[];
  return <>
    <PageTitle title="Dashboard" description="Visão geral da infraestrutura tecnológica" action={<Button kind="ghost" icon={RefreshCw} onClick={()=>load()}>Atualizar</Button>}/>
    <Banner>{error}</Banner><PanelLoader loading={loading}/>
    <div className="stats-grid">
      <StatCard label="IIE Geral" value={summary?.iie_average==null?'—':`${number(summary.iie_average)} / 100`} caption="Índice de condição técnica" icon={ShieldCheck} tone="green"/>
      <StatCard label="Computadores Online" value={summary?.online??'—'} caption={summary?`de ${summary.computers} equipamentos`:'Aguardando dados'} icon={Monitor} tone="blue"/>
      <StatCard label="Computadores Offline" value={summary?.offline??'—'} caption={summary?.computers?`${Math.round(summary.offline/summary.computers*100)}% da infraestrutura`:'Aguardando dados'} icon={Power} tone="red"/>
      <StatCard label="Alertas" value={summary?.open_alerts??'—'} caption="Ocorrências pendentes" icon={Bell} tone="orange"/>
    </div>
    <div className="content-grid prominent-grid">
      <Panel title="Situação dos Laboratórios" action={<PanelLink onClick={()=>navigate('laboratories')}>Ver todos</PanelLink>} className="no-body-padding"><LabSummaryTable items={info} navigate={navigate}/></Panel>
      <Panel title="Alertas recentes"><AlertFeed alerts={activeAlerts} pcs={pcs} onAll={()=>navigate('alerts')}/></Panel>
    </div>
    <div className="content-grid lower-grid"><MetricPanel pcs={pcs}/><AvailabilityPanel pcs={pcs}/></div>
    <p className="data-disclaimer"><Info size={15}/> Os painéis utilizam cadastros e medições reais. Sem dados coletados, não são exibidos valores simulados.</p>
  </>;
}

function Laboratories({user}){
  const [query,setQuery]=useState('');const [status,setStatus]=useState('all');const [editing,setEditing]=useState(null);const [error,setError]=useState('');
  const {data,error:loadError,loading,load}=useApiData(['/api/laboratories','/api/computers','/api/indicators'],60000);
  const labs=data?.[0]||[],pcs=data?.[1]||[],indicators=data?.[2]||[];
  const shown=labs.filter(l=>(`${l.name} ${l.location}`).toLowerCase().includes(query.toLowerCase())&&(status==='all'||String(l.active)===status));
  const states=statusCounts(pcs);
  const problems=pcs.filter(c=>c.status==='offline'||(c.status==='online'&&c.latest_metric&&Math.max(c.latest_metric.cpu_percent,c.latest_metric.memory_percent,c.latest_metric.disk_percent)>=90)).length;
  const scored=indicators.filter(i=>i.score!==null);
  const average=scored.length?scored.reduce((n,i)=>n+i.score,0)/scored.length:null;
  const best=[...scored].sort((a,b)=>b.score-a.score)[0];
  const weakest=[...scored].sort((a,b)=>a.score-b.score)[0];
  const maintenance=[...indicators].sort((a,b)=>(b.offline+b.sem_coleta)-(a.offline+a.sem_coleta))[0];
  const remove=async lab=>{if(!window.confirm(`Excluir o laboratório “${lab.name}”? Não é possível excluir um laboratório com computadores vinculados.`))return;try{await request(`/api/laboratories/${lab.id}`,{method:'DELETE'});load()}catch(e){setError(message(e))}};
  return <>
    <PageTitle title="Laboratórios" description="Gerencie e acompanhe os laboratórios da instituição" action={<>{canEdit(user)&&<Button icon={Plus} onClick={()=>setEditing({})}>Novo laboratório</Button>}<Button kind="ghost" icon={RefreshCw} onClick={()=>load()}>Atualizar</Button></>}/>
    <Banner onClose={()=>setError('')}>{error||loadError}</Banner><PanelLoader loading={loading}/>
    <div className="stats-grid"><StatCard label="Total de laboratórios" value={data?labs.length:'—'} icon={Server}/><StatCard label="Equipamentos" value={data?pcs.length:'—'} icon={Monitor} tone="blue"/><StatCard label="Disponíveis" value={data?states.online:'—'} caption="Com coleta recente" icon={CheckCircle2} tone="green"/><StatCard label="Com problemas" value={data?problems:'—'} caption="Offline ou acima de 90%" icon={AlertTriangle} tone="red"/></div>
    <div className="content-grid prominent-grid labs-main">
      <Panel title="Situação dos Laboratórios" className="no-body-padding"><div className="lab-toolbar"><SearchBox value={query} onChange={setQuery} placeholder="Buscar laboratório ou localização"/><select aria-label="Filtrar laboratórios por situação" value={status} onChange={e=>setStatus(e.target.value)}><option value="all">Todos os laboratórios</option><option value="true">Ativos</option><option value="false">Inativos</option></select></div>
        {shown.length?<div className="table-scroll"><table className="data-table lab-page-table"><thead><tr><th>Laboratório</th><th>Equipamentos</th><th>Online</th><th>Problemas</th><th>IIE</th><th>Status</th>{canEdit(user)&&<th>Ações</th>}</tr></thead><tbody>{shown.map(l=>{const i=indicators.find(x=>x.laboratory_id===l.id);return <tr key={l.id}><td><div className="lab-cell"><span className="lab-cell-icon"><Server size={21}/></span><div><strong>{l.name}</strong><span className="cell-second">{l.location}</span></div></div></td><td>{i?.total??0}</td><td><b>{i?.online??0}</b><span className="cell-second">({i?.total?Math.round(i.online/i.total*100):0}%)</span></td><td className={(i?.offline||0)+(i?.sem_coleta||0)?'text-orange':''}>{(i?.offline||0)+(i?.sem_coleta||0)}</td><td className={i?.score==null?'text-muted':i.score>=75?'text-green':i.score>=50?'text-orange':'text-red'}><b>{number(i?.score)}</b></td><td><Badge status={l.active?i?.classification:'inactive'}/></td>{canEdit(user)&&<td><div className="row-actions"><button title="Editar laboratório" onClick={()=>setEditing(l)}><Edit3 size={16}/></button><button title="Excluir laboratório" className="danger" onClick={()=>remove(l)}><Trash2 size={16}/></button></div></td>}</tr>})}</tbody></table></div>:<Empty compact icon={Server} title="Nenhum laboratório encontrado" description="Tente outros filtros ou cadastre seu primeiro laboratório."/>}
      </Panel>
      <Panel title="Resumo rápido" className="quick-panel"><div className="quick-list">
        <div className="quick-row"><span className="quick-icon green"><TrendingUp size={22}/></span><div><small>Melhor desempenho</small><strong>{best?.laboratory||'Sem dados'}</strong></div></div>
        <div className="quick-row"><span className="quick-icon orange"><AlertCircle size={22}/></span><div><small>Maior atenção (IIE)</small><strong>{weakest?.laboratory||'Sem dados'}</strong></div></div>
        <div className="quick-row"><span className="quick-icon red"><Server size={22}/></span><div><small>Prioridade de manutenção</small><strong>{maintenance && (maintenance.offline+maintenance.sem_coleta)>0?maintenance.laboratory:'Sem pendências'}</strong></div></div>
        <div className="quick-row"><span className="quick-icon blue"><BarChart3 size={22}/></span><div><small>IIE médio institucional</small><strong className="quick-score">{number(average)}</strong></div></div>
      </div></Panel>
    </div>
    <div className="content-grid lower-grid"><Panel title="Capacidade e disponibilidade"><LaboratoryBars items={indicators}/></Panel><AvailabilityPanel pcs={pcs}/></div>
    {editing&&<LaboratoryForm data={editing} onClose={()=>setEditing(null)} onSaved={()=>{setEditing(null);load()}}/>}
  </>;
}
function LaboratoryForm({data,onClose,onSaved}){
  const [form,setForm]=useState({name:data.name||'',location:data.location||'',active:data.active??true});const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  const change=(key,value)=>setForm(x=>({...x,[key]:value}));
  const save=async e=>{e.preventDefault();setBusy(true);setError('');try{await request(data.id?`/api/laboratories/${data.id}`:'/api/laboratories',{method:data.id?'PUT':'POST',body:form});onSaved()}catch(e){setError(message(e))}finally{setBusy(false)}};
  return <Modal title={data.id?'Editar laboratório':'Novo laboratório'} onClose={onClose}><form className="modal-body form-stack" onSubmit={save}><Field label="Nome do laboratório"><input required minLength={2} maxLength={120} placeholder="Ex.: Laboratório de Informática 01" value={form.name} onChange={e=>change('name',e.target.value)}/></Field><Field label="Localização"><input required minLength={2} maxLength={180} placeholder="Ex.: Bloco A · Sala 12" value={form.location} onChange={e=>change('location',e.target.value)}/></Field><label className="check-line"><input type="checkbox" checked={form.active} onChange={e=>change('active',e.target.checked)}/> Laboratório ativo</label><Banner>{error}</Banner><div className="modal-footer"><Button kind="secondary" type="button" onClick={onClose}>Cancelar</Button><Button type="submit" icon={Save} disabled={busy}>{busy?'Salvando...':'Salvar laboratório'}</Button></div></form></Modal>;
}

function Computers({user}){
  const [query,setQuery]=useState('');const [lab,setLab]=useState('');const [status,setStatus]=useState('all');
  const [editing,setEditing]=useState(null);const [history,setHistory]=useState(null);const [actionPc,setActionPc]=useState(null);const [tokenInfo,setTokenInfo]=useState(null);const [importing,setImporting]=useState(false);const [error,setError]=useState('');
  const {data,error:loadError,loading,load}=useApiData(['/api/computers','/api/laboratories','/api/alerts','/api/settings'],60000);
  const pcs=data?.[0]||[],labs=data?.[1]||[],alerts=data?.[2]||[],cfg=data?.[3];
  const counts=statusCounts(pcs);
  const attention=pcs.filter(c=>['atencao','critico'].includes(computerHealth(c,cfg))).length;
  const shown=pcs.filter(pc=>{
    const matches=(`${pc.name} ${pc.hostname}`).toLowerCase().includes(query.toLowerCase());
    const health=computerHealth(pc,cfg);
    return matches&&(!lab||pc.laboratory_id===Number(lab))&&(status==='all'||(status==='atencao'?['atencao','critico'].includes(health):status==='online'?pc.status==='online':pc.status===status));
  });
  const deleteComputer=async pc=>{if(!window.confirm(`Excluir “${pc.name}”? Suas métricas e alertas também serão removidos permanentemente.`))return;try{await request(`/api/computers/${pc.id}`,{method:'DELETE'});load()}catch(e){setError(message(e))}};
  const generateToken=async pc=>{if(!window.confirm(`Gerar um novo token para “${pc.name}”? O token anterior será invalidado.`))return;try{const answer=await request(`/api/computers/${pc.id}/token`,{method:'POST'});setTokenInfo({...answer,name:pc.name,id:pc.id})}catch(e){setError(message(e))}};
  return <>
    <PageTitle title="Computadores" description="Monitore os equipamentos cadastrados nos laboratórios" action={<>{canEdit(user)&&<><Button kind="secondary" icon={UploadCloud} onClick={()=>setImporting(true)}>Inventário Hyper-V</Button><Button icon={Plus} onClick={()=>setEditing({})}>Novo computador</Button></>}<Button kind="ghost" icon={RefreshCw} onClick={()=>load()}>Atualizar</Button></>}/>
    <Banner onClose={()=>setError('')}>{error||loadError}</Banner><PanelLoader loading={loading}/>
    <div className="stats-grid"><StatCard label="Total de equipamentos" value={data?pcs.length:'—'} icon={Monitor} tone="blue"/><StatCard label="Online" value={data?counts.online:'—'} caption="Coleta recente" icon={CheckCircle2} tone="green"/><StatCard label="Offline" value={data?counts.offline:'—'} caption="Sem coleta no prazo" icon={Power} tone="red"/><StatCard label="Em atenção" value={data?attention:'—'} caption="Consumo acima do limite" icon={AlertTriangle} tone="orange"/></div>
    <div className="content-grid prominent-grid computers-main">
      <Panel title="Equipamentos monitorados" className="no-body-padding"><div className="table-toolbar"><SearchBox value={query} onChange={setQuery} placeholder="Pesquisar equipamento..."/><select value={lab} onChange={e=>setLab(e.target.value)} aria-label="Filtrar por laboratório"><option value="">Todos os laboratórios</option>{labs.map(l=><option key={l.id} value={l.id}>{l.name}</option>)}</select><select value={status} onChange={e=>setStatus(e.target.value)} aria-label="Filtrar por status"><option value="all">Todos os status</option><option value="online">Online</option><option value="offline">Offline</option><option value="sem_coleta">Sem coleta</option><option value="atencao">Em atenção</option><option value="inactive">Inativos</option></select></div>
        {shown.length?<div className="table-scroll"><table className="data-table computers-table"><thead><tr><th>Computador</th><th>Laboratório</th><th>Status</th><th>CPU</th><th>RAM</th><th>Disco</th><th>Última coleta</th><th>Detalhes</th>{canEdit(user)&&<th>Ações</th>}</tr></thead><tbody>{shown.map(pc=>{
          const health=computerHealth(pc,cfg);const metric=pc.latest_metric;
          return <tr key={pc.id}><td><strong>{pc.name}</strong><span className="cell-second">{pc.hostname} {pc.source==='hyperv'?'· Hyper-V':''}</span><span className="cell-id">ID #{pc.id}</span></td><td>{labs.find(l=>l.id===pc.laboratory_id)?.name||'—'}</td><td><Badge status={health}/></td><td>{metric?`${number(metric.cpu_percent)}%`:'—'}</td><td>{metric?`${number(metric.memory_percent)}%`:'—'}</td><td>{metric?`${number(metric.disk_percent)}%`:'—'}</td><td>{pc.last_seen_at?clockTime(pc.last_seen_at):'—'}</td><td><button className="table-chevron" title={`Ver histórico de ${pc.name}`} aria-label={`Ver histórico de ${pc.name}`} onClick={()=>setHistory(pc)}><ChevronRight size={20}/></button></td>{canEdit(user)&&<td><button type="button" className="table-chevron" title={`Ações para ${pc.name}`} aria-label={`Ações para ${pc.name}`} onClick={()=>setActionPc(pc)}><MoreHorizontal size={20}/></button></td>}</tr>})}</tbody></table></div>:<Empty compact icon={Monitor} title="Nenhum equipamento encontrado" description="Cadastre um computador ou ajuste os filtros."/>}
      </Panel>
      <Panel title="Alertas recentes"><AlertFeed alerts={alerts.filter(a=>a.status!=='resolved')} pcs={pcs}/></Panel>
    </div>
    <div className="content-grid lower-grid"><MetricPanel pcs={pcs}/><AvailabilityPanel pcs={pcs}/></div>
    {editing&&<ComputerForm data={editing} labs={labs} onClose={()=>setEditing(null)} onSaved={()=>{setEditing(null);load()}}/>}
    {history&&<ComputerHistory computer={history} onClose={()=>setHistory(null)}/>}
    {actionPc&&<Modal title={`Ações · ${actionPc.name}`} onClose={()=>setActionPc(null)}><div className="modal-body action-modal-list"><Button kind="secondary" icon={Eye} onClick={()=>{setHistory(actionPc);setActionPc(null)}}>Visualizar histórico</Button><Button kind="secondary" icon={KeyRound} onClick={()=>{generateToken(actionPc);setActionPc(null)}}>Gerar novo token</Button><Button kind="secondary" icon={Edit3} onClick={()=>{setEditing(actionPc);setActionPc(null)}}>Editar computador</Button><Button kind="danger" icon={Trash2} onClick={()=>{deleteComputer(actionPc);setActionPc(null)}}>Excluir computador</Button></div></Modal>}
    {tokenInfo&&<Modal title={`Token do agente · ${tokenInfo.name}`} onClose={()=>setTokenInfo(null)}><div className="modal-body form-stack"><div className="notice"><LockKeyhole size={18}/> Copie o token agora. Ele será exibido somente nesta janela. A credencial anterior deixou de funcionar.</div><Field label={`ID do computador: ${tokenInfo.id}`}><textarea rows={3} className="mono" readOnly value={tokenInfo.agent_token}/></Field><Button kind="secondary" icon={ClipboardCheck} onClick={()=>navigator.clipboard.writeText(tokenInfo.agent_token).catch(()=>setError('Não foi possível copiar automaticamente. Selecione o texto do token.'))}>Copiar token</Button><div className="modal-footer"><Button onClick={()=>setTokenInfo(null)}>Concluído</Button></div></div></Modal>}
    {importing&&<HyperVImport labs={labs} onClose={()=>setImporting(false)} onSaved={()=>{setImporting(false);load()}}/>}
  </>;
}
function ComputerForm({data,labs,onClose,onSaved}){
  const [form,setForm]=useState({laboratory_id:data.laboratory_id||labs[0]?.id||'',name:data.name||'',hostname:data.hostname||'',ip_address:data.ip_address||'',active:data.active??true});const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const change=(key,value)=>setForm(s=>({...s,[key]:value}));
  const save=async e=>{e.preventDefault();setBusy(true);setError('');try{await request(data.id?`/api/computers/${data.id}`:'/api/computers',{method:data.id?'PUT':'POST',body:{...form,laboratory_id:Number(form.laboratory_id),ip_address:form.ip_address||null}});onSaved()}catch(e){setError(message(e))}finally{setBusy(false)}};
  return <Modal title={data.id?'Editar computador':'Novo computador'} onClose={onClose}><form className="modal-body form-stack" onSubmit={save}><Field label="Laboratório"><select required value={form.laboratory_id} onChange={e=>change('laboratory_id',e.target.value)}><option value="">Selecione o laboratório</option>{labs.map(l=><option key={l.id} value={l.id}>{l.name}</option>)}</select></Field><Field label="Nome de exibição"><input required minLength={2} maxLength={120} placeholder="Ex.: Computador do Laboratório 01" value={form.name} onChange={e=>change('name',e.target.value)}/></Field><Field label="Hostname"><input required maxLength={120} placeholder="Ex.: LAB01-PC01" value={form.hostname} onChange={e=>change('hostname',e.target.value)}/></Field><Field label="Endereço IPv4/IPv6 (opcional)"><input placeholder="Ex.: 192.168.1.10" value={form.ip_address} onChange={e=>change('ip_address',e.target.value)}/></Field><label className="check-line"><input type="checkbox" checked={form.active} onChange={e=>change('active',e.target.checked)}/> Computador ativo</label><Banner>{error}</Banner><div className="modal-footer"><Button type="button" kind="secondary" onClick={onClose}>Cancelar</Button><Button disabled={busy||!labs.length} type="submit" icon={Save}>{busy?'Salvando...':'Salvar computador'}</Button></div></form></Modal>;
}
function ComputerHistory({computer,onClose}){
  const {data,loading,error}=useHistory(computer.id);
  return <Modal wide title={`Histórico de métricas · ${computer.name}`} onClose={onClose}><div className="modal-body"><Banner>{error}</Banner><PanelLoader loading={loading}/>{data.length?<><div className="metric-overview"><StatCard label="CPU" value={`${number(data[0].cpu_percent)}%`} icon={Cpu}/><StatCard label="Memória" value={`${number(data[0].memory_percent)}%`} icon={Activity} tone="green"/><StatCard label="Disco" value={`${number(data[0].disk_percent)}%`} icon={HardDrive} tone="orange"/></div><MetricTrend samples={data}/><div className="table-scroll history-scroll"><table className="data-table"><thead><tr><th>Data da coleta</th><th>CPU</th><th>RAM</th><th>Disco</th><th>Sistema</th></tr></thead><tbody>{data.map(m=><tr key={m.id}><td>{dateTime(m.collected_at)}</td><td>{number(m.cpu_percent)}%</td><td>{number(m.memory_percent)}%</td><td>{number(m.disk_percent)}%</td><td>{m.os_name}</td></tr>)}</tbody></table></div></>:!loading&&<Empty title="Este equipamento ainda não enviou métricas" description="Instale o agente na máquina ou VM e configure o ID e token exclusivos."/>}</div></Modal>;
}
function HyperVImport({labs,onClose,onSaved}){
  const [lab,setLab]=useState(labs[0]?.id||'');const [json,setJson]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const save=async e=>{e.preventDefault();setBusy(true);setError('');try{const vms=JSON.parse(json);if(!Array.isArray(vms))throw new Error('O inventário precisa ser uma lista JSON.');await request('/api/hyperv/import',{method:'POST',body:{laboratory_id:Number(lab),vms}});onSaved()}catch(e){setError(message(e))}finally{setBusy(false)}};
  return <Modal title="Importar inventário do Hyper-V" wide onClose={onClose}><form className="modal-body form-stack" onSubmit={save}><div className="notice"><Info size={18}/> Execute <code>hyperv/Export-HyperVInventory.ps1</code> no host e cole aqui o JSON gerado. O inventário identifica as VMs; CPU, RAM e disco dependem do agente instalado dentro de cada VM.</div><Field label="Laboratório de destino"><select required value={lab} onChange={e=>setLab(e.target.value)}>{labs.map(l=><option key={l.id} value={l.id}>{l.name}</option>)}</select></Field><Field label="Inventário JSON"><textarea required spellCheck={false} className="mono" rows={9} value={json} onChange={e=>setJson(e.target.value)} placeholder={'[{"vm_id":"ID-DA-VM","name":"LAB-VM-01","state":"Running"}]'}/></Field><Banner>{error}</Banner><div className="modal-footer"><Button type="button" kind="secondary" onClick={onClose}>Cancelar</Button><Button disabled={busy||!lab} type="submit" icon={UploadCloud}>{busy?'Importando...':'Importar VMs'}</Button></div></form></Modal>;
}

function Alerts({user}){
  const [filter,setFilter]=useState('all');const [error,setError]=useState('');
  const {data,loading,error:loadError,load}=useApiData(['/api/alerts','/api/computers'],60000);
  const alerts=data?.[0]||[],pcs=data?.[1]||[];
  const shown=alerts.filter(x=>filter==='all'||x.status===filter);
  const names=new Map(pcs.map(c=>[c.id,c.name]));
  const acknowledge=async a=>{try{await request(`/api/alerts/${a.id}/acknowledge`,{method:'PATCH'});load()}catch(e){setError(message(e))}};
  const open=alerts.filter(x=>x.status==='open');
  return <><PageTitle title="Alertas" description="Acompanhe ocorrências e equipamentos que precisam de atenção" action={<Button icon={RefreshCw} kind="ghost" onClick={()=>load()}>Atualizar</Button>}/><Banner>{error||loadError}</Banner><PanelLoader loading={loading}/>
    <div className="stats-grid stats-grid-three"><StatCard label="Alertas abertos" value={data?open.length:'—'} icon={Bell} tone="red"/><StatCard label="Críticos" value={data?open.filter(x=>x.severity==='critical').length:'—'} icon={AlertTriangle} tone="orange"/><StatCard label="Reconhecidos" value={data?alerts.filter(x=>x.status==='acknowledged').length:'—'} icon={CheckCircle2} tone="green"/></div>
    <Panel title="Ocorrências registradas" className="no-body-padding"><div className="table-toolbar"><select value={filter} onChange={e=>setFilter(e.target.value)} aria-label="Filtrar alertas"><option value="all">Todos os alertas</option><option value="open">Abertos</option><option value="acknowledged">Reconhecidos</option><option value="resolved">Resolvidos</option></select></div>{shown.length?<div className="alerts-page-list">{shown.map(a=><div className="alert-large-row" key={a.id}><span className={`alert-bubble ${a.severity==='critical'?'critical':'warning'}`}><AlertTriangle size={22}/></span><div className="alert-description"><strong>{names.get(a.computer_id)||`Computador #${a.computer_id}`}</strong><p>{a.message}</p><span>{dateTime(a.created_at)}</span></div><Badge status={a.status}/>{canEdit(user)&&a.status==='open'&&<Button kind="secondary" icon={Check} onClick={()=>acknowledge(a)}>Reconhecer</Button>}</div>)}</div>:<Empty icon={CheckCircle2} title="Nenhum alerta neste filtro" description="Alertas são gerados automaticamente a partir das medições reais dos computadores."/>}</Panel>
  </>;
}
function Indicators(){
  const {data,loading,error,load}=useApiData(['/api/indicators'],60000);
  const labs=data?.[0]||[];
  const [selected,setSelected]=useState(null);const [history,setHistory]=useState([]);const [historyError,setHistoryError]=useState('');
  useEffect(()=>{if(!selected)return;let live=true;setHistory([]);request(`/api/indicators/${selected.laboratory_id}/history`).then(r=>{if(live)setHistory(r)}).catch(e=>{if(live)setHistoryError(message(e))});return()=>{live=false}},[selected]);
  const scored=labs.filter(l=>l.score!==null);const average=scored.length?scored.reduce((n,l)=>n+l.score,0)/scored.length:null;
  return <><PageTitle title="Indicadores" description="Índice experimental da condição técnica dos laboratórios" action={<Button icon={RefreshCw} kind="ghost" onClick={()=>load()}>Atualizar</Button>}/><Banner>{error}</Banner><PanelLoader loading={loading}/>
    <div className="info-strip"><Info size={20}/><span>O IIE é um indicador operacional heurístico (0 a 100), baseado em disponibilidade, cobertura da coleta e utilização de recursos. <strong>Não mede diretamente a qualidade do ensino ou o desempenho dos alunos.</strong></span></div>
    <div className="stats-grid stats-grid-three"><StatCard label="IIE médio" value={number(average)} icon={Gauge} tone="blue"/><StatCard label="Laboratórios adequados" value={data?labs.filter(l=>l.classification==='adequado').length:'—'} icon={CheckCircle2} tone="green"/><StatCard label="Exigem atenção" value={data?labs.filter(l=>['atencao','critico'].includes(l.classification)).length:'—'} icon={AlertTriangle} tone="orange"/></div>
    <div className="indicator-cards">{labs.length?labs.map(l=><button type="button" className="indicator-card" key={l.laboratory_id} onClick={()=>{setHistoryError('');setSelected(l)}}><div className="indicator-card-top"><span className="lab-cell-icon"><Server size={21}/></span><Badge status={l.classification}/></div><strong>{l.laboratory}</strong><div className="indicator-large-score">{number(l.score)}<span> / 100</span></div><div className="progress-track"><span style={{width:`${clamp(l.score)}%`}}/></div><div className="indicator-card-meta"><span>Cobertura <b>{number(l.coverage)}%</b></span><span>Online <b>{l.online}/{l.total}</b></span></div><span className="indicator-link">Ver histórico <ArrowRight size={16}/></span></button>):<div className="full-width"><Empty icon={Gauge} title="Nenhum indicador disponível" description="Cadastre laboratórios e configure os agentes de monitoramento."/></div>}</div>
    {selected&&<Modal wide title={`Histórico do IIE · ${selected.laboratory}`} onClose={()=>setSelected(null)}><div className="modal-body"><Banner>{historyError}</Banner><ScoreTrend samples={history}/>{history.length>0&&<div className="table-scroll history-scroll"><table className="data-table"><thead><tr><th>Data</th><th>IIE</th><th>Cobertura</th><th>Online / Total</th></tr></thead><tbody>{history.map((x,i)=><tr key={i}><td>{dateTime(x.calculated_at)}</td><td>{number(x.score)}</td><td>{number(x.coverage)}%</td><td>{x.online}/{x.total}</td></tr>)}</tbody></table></div>}</div></Modal>}
  </>;
}
function Reports(){
  const [busy,setBusy]=useState('');const [error,setError]=useState('');
  const run=async type=>{setBusy(type);setError('');try{await download(type==='metrics'?'/api/reports/metrics.csv':'/api/reports/indicators.csv',type==='metrics'?'metricas_eduinfra.csv':'indicadores_eduinfra.csv')}catch(e){setError(message(e))}finally{setBusy('')}};
  return <><PageTitle title="Relatórios" description="Exporte dados históricos e indicadores da infraestrutura"/><Banner>{error}</Banner><div className="reports-grid"><article className="report-card"><span className="report-icon blue"><Activity size={29}/></span><span className="report-kicker">MONITORAMENTO</span><h2>Histórico de métricas</h2><p>Exporte CPU, memória, disco, tempo de atividade, sistema operacional e data de coleta dos equipamentos monitorados.</p><span className="report-format"><FileText size={17}/> Formato CSV · Até 10.000 medições recentes</span><Button icon={ArrowDownToLine} disabled={!!busy} onClick={()=>run('metrics')}>{busy==='metrics'?'Preparando...':'Exportar métricas'}</Button></article>
    <article className="report-card"><span className="report-icon green"><Gauge size={29}/></span><span className="report-kicker">DESEMPENHO</span><h2>Indicadores de infraestrutura</h2><p>Exporte o IIE calculado, a cobertura de coleta e a disponibilidade de equipamentos por laboratório.</p><span className="report-format"><FileText size={17}/> Formato CSV · Indicadores atuais</span><Button icon={ArrowDownToLine} disabled={!!busy} onClick={()=>run('indicators')}>{busy==='indicators'?'Preparando...':'Exportar indicadores'}</Button></article></div><div className="info-strip"><Info size={20}/><span>Os relatórios contêm somente dados cadastrados e coletados. A aplicação não gera medições fictícias.</span></div></>;
}

function Settings({user}){
  const paths=['/api/settings','/api/terms/current',...(user.role==='ADMIN'?['/api/audit']:[])];
  const {data,loading,error:loadError,load}=useApiData(paths);
  const [form,setForm]=useState(null);const [error,setError]=useState('');const [success,setSuccess]=useState('');const [showTerms,setShowTerms]=useState(false);const [publish,setPublish]=useState(false);
  const settings=data?.[0],terms=data?.[1],audit=data?.[2]||[];
  useEffect(()=>{if(settings)setForm(settings)},[settings]);
  const change=(key,value)=>setForm(f=>({...f,[key]:Number(value)}));
  const save=async e=>{e.preventDefault();setError('');setSuccess('');try{await request('/api/settings',{method:'PUT',body:form});setSuccess('Configurações salvas com sucesso.');load()}catch(e){setError(message(e))}};
  return <><PageTitle title="Configurações" description="Administre os parâmetros de monitoramento e a plataforma"/><Banner>{error||loadError}</Banner><Banner type="success">{success}</Banner><PanelLoader loading={loading}/>
    <div className="settings-grid"><Panel title="Limiares de monitoramento" description="Parâmetros utilizados na geração de alertas"><form onSubmit={save} className="settings-form">{form&&<><Field label="CPU crítica (%)"><input disabled={user.role!=='ADMIN'} type="number" min={50} max={100} required value={form.cpu_alert_threshold} onChange={e=>change('cpu_alert_threshold',e.target.value)}/></Field><Field label="Memória crítica (%)"><input disabled={user.role!=='ADMIN'} type="number" min={50} max={100} required value={form.memory_alert_threshold} onChange={e=>change('memory_alert_threshold',e.target.value)}/></Field><Field label="Disco crítico (%)"><input disabled={user.role!=='ADMIN'} type="number" min={50} max={100} required value={form.disk_alert_threshold} onChange={e=>change('disk_alert_threshold',e.target.value)}/></Field><Field label="Máximo sem coleta (segundos)"><input disabled={user.role!=='ADMIN'} type="number" min={60} max={86400} required value={form.stale_after_seconds} onChange={e=>change('stale_after_seconds',e.target.value)}/></Field>{user.role==='ADMIN'&&<div className="settings-submit"><Button type="submit" icon={Save}>Salvar configurações</Button></div>}</>}</form></Panel>
      <Panel title="Termos e Condições" description="Documento vigente e registros de aceite"><div className="terms-settings"><span className="terms-settings-symbol"><BookOpenCheck size={30}/></span><h3>{terms?.title||'Termos e Condições'}</h3><p>Versão vigente: <strong>{terms?.version||'—'}</strong></p><p>Publicado em: <strong>{dateTime(terms?.published_at)}</strong></p><span className="terms-current"><CheckCircle2 size={17}/> Acesso sujeito ao aceite da versão vigente</span><Button kind="secondary" icon={Eye} onClick={()=>setShowTerms(true)}>Ler termos vigentes</Button>{user.role==='ADMIN'&&<Button kind="ghost" icon={RotateCcw} onClick={()=>setPublish(true)}>Publicar nova versão</Button>}</div></Panel>
    </div>
    {user.role==='ADMIN'&&<Panel title="Auditoria recente" description="Registro de operações e alterações administrativas" className="audit-panel no-body-padding">{audit.length?<div className="table-scroll"><table className="data-table"><thead><tr><th>Data</th><th>Ação</th><th>Entidade</th><th>Usuário</th></tr></thead><tbody>{audit.slice(0,25).map(a=><tr key={a.id}><td>{dateTime(a.created_at)}</td><td>{a.action}</td><td>{a.entity} {a.entity_id?`#${a.entity_id}`:''}</td><td>{a.actor_id||'—'}</td></tr>)}</tbody></table></div>:<Empty icon={ShieldCheck} compact title="Sem registros de auditoria" description="Os eventos administrativos aparecerão aqui."/>}</Panel>}
    {showTerms&&<Modal wide title={terms?.title||'Termos e Condições'} onClose={()=>setShowTerms(false)}><div className="terms-article">{terms?.content?.split('\n').map((line,i)=><p key={i}>{line||'\u00a0'}</p>)}</div><div className="modal-footer"><Button onClick={()=>setShowTerms(false)}>Fechar</Button></div></Modal>}
    {publish&&<PublishTerms onClose={()=>setPublish(false)} onSaved={()=>{setPublish(false);load()}}/>}
  </>;
}
function PublishTerms({onClose,onSaved}){
  const [form,setForm]=useState({version:'',title:'Termos e Condições de Uso',content:''});const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  const change=(k,v)=>setForm(s=>({...s,[k]:v}));
  const save=async e=>{e.preventDefault();if(!window.confirm('Esta ação exigirá que todos os usuários aceitem a nova versão dos Termos. Continuar?'))return;setBusy(true);setError('');try{await request('/api/terms/publish',{method:'POST',body:form});onSaved()}catch(e){setError(message(e))}finally{setBusy(false)}};
  return <Modal title="Publicar nova versão de Termos" wide onClose={onClose}><form className="modal-body form-stack" onSubmit={save}><div className="notice"><ShieldCheck size={20}/> Ao publicar, todos os usuários precisarão aceitar os novos Termos antes de acessar o painel, inclusive administradores.</div><Field label="Versão"><input required pattern="[0-9A-Za-z._-]+" maxLength={32} placeholder="Ex.: 2.1" value={form.version} onChange={e=>change('version',e.target.value)}/></Field><Field label="Título"><input required minLength={5} maxLength={180} value={form.title} onChange={e=>change('title',e.target.value)}/></Field><Field label="Conteúdo completo (mínimo 150 caracteres)"><textarea required minLength={150} maxLength={50000} rows={13} value={form.content} onChange={e=>change('content',e.target.value)}/></Field><Banner>{error}</Banner><div className="modal-footer"><Button type="button" kind="secondary" onClick={onClose}>Cancelar</Button><Button disabled={busy} type="submit" icon={BookOpenCheck}>{busy?'Publicando...':'Publicar termos'}</Button></div></form></Modal>;
}
function UsersPage(){
  const [editing,setEditing]=useState(false);const [error,setError]=useState('');const {data,loading,error:loadError,load}=useApiData(['/api/users']);const users=data?.[0]||[];
  const changeStatus=async item=>{if(!window.confirm(`${item.active?'Desativar':'Ativar'} o acesso de ${item.name}?`))return;try{await request(`/api/users/${item.id}/status?active=${!item.active}`,{method:'PATCH'});load()}catch(e){setError(message(e))}};
  return <><PageTitle title="Usuários" description="Gerencie usuários e permissões de acesso" action={<Button icon={Plus} onClick={()=>setEditing(true)}>Novo usuário</Button>}/><Banner>{error||loadError}</Banner><PanelLoader loading={loading}/><Panel title="Usuários cadastrados" className="no-body-padding">{users.length?<div className="table-scroll"><table className="data-table"><thead><tr><th>Usuário</th><th>E-mail</th><th>Perfil</th><th>Situação</th><th>Ação</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td><div className="lab-cell"><span className="lab-cell-icon"><UserRound size={19}/></span><strong>{u.name}</strong></div></td><td>{u.email}</td><td>{ROLES[u.role]||u.role}</td><td><Badge status={u.active?'active':'inactive'}/></td><td><Button kind="secondary" icon={u.active?Power:Check} onClick={()=>changeStatus(u)}>{u.active?'Desativar':'Ativar'}</Button></td></tr>)}</tbody></table></div>:<Empty compact icon={Users} title="Nenhum usuário cadastrado"/>}</Panel>{editing&&<UserForm onClose={()=>setEditing(false)} onSaved={()=>{setEditing(false);load()}}/>}</>;
}
function UserForm({onClose,onSaved}){
  const [form,setForm]=useState({name:'',email:'',password:'',role:'GESTOR'});const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  const change=(k,v)=>setForm(s=>({...s,[k]:v}));
  const save=async e=>{e.preventDefault();setBusy(true);setError('');try{await request('/api/users',{method:'POST',body:form});onSaved()}catch(e){setError(message(e))}finally{setBusy(false)}};
  return <Modal title="Novo usuário" onClose={onClose}><form className="modal-body form-stack" onSubmit={save}><Field label="Nome completo"><input required minLength={2} maxLength={120} value={form.name} onChange={e=>change('name',e.target.value)}/></Field><Field label="E-mail institucional"><input required type="email" value={form.email} onChange={e=>change('email',e.target.value)}/></Field><Field label="Senha inicial (mínimo 12 caracteres)"><input required type="password" minLength={12} maxLength={128} autoComplete="new-password" value={form.password} onChange={e=>change('password',e.target.value)}/></Field><Field label="Perfil de acesso"><select value={form.role} onChange={e=>change('role',e.target.value)}><option value="GESTOR">Gestor — leitura</option><option value="TECNICO">Técnico — operação</option><option value="ADMIN">Administrador — gestão completa</option></select></Field><Banner>{error}</Banner><div className="modal-footer"><Button type="button" kind="secondary" onClick={onClose}>Cancelar</Button><Button disabled={busy} type="submit" icon={Plus}>{busy?'Criando...':'Criar usuário'}</Button></div></form></Modal>;
}

function LegalText({content}) {
  return <div className="legal-document">{(content || '').split('\n').map((line,i) => {
    const heading = /^\d{1,2}\.\s+[A-ZÁÉÍÓÚÃÕÂÊÔÇ]/u.test(line);
    const title = i === 0;
    const warning = /^(AVISO PRÉVIO|AVISO DE PUBLICAÇÃO)/.test(line);
    if (!line.trim()) return <div className="legal-gap" key={i}/>;
    if (title) return <h2 className="legal-main-title" key={i}>{line}</h2>;
    if (heading) return <h3 className="legal-section-title" key={i}>{line}</h3>;
    if (warning) return <p className="legal-warning" key={i}>{line}</p>;
    return <p className="legal-paragraph" key={i}>{line}</p>;
  })}</div>;
}

function PrivacyNoticeModal({onClose}) {
  const [doc,setDoc]=useState(null);
  const [error,setError]=useState('');
  useEffect(()=>{let live=true;request('/api/public/privacy-notice').then(r=>{if(live)setDoc(r)}).catch(e=>{if(live)setError(message(e))});return ()=>{live=false}},[]);
  return <Modal wide title="Aviso de Privacidade e LGPD" onClose={onClose}>
    <Banner>{error}</Banner>
    {doc?<div className="terms-article"><LegalText content={doc.content}/></div>:<div className="modal-body"><PanelLoader loading/></div>}
    <div className="modal-footer"><Button onClick={onClose}>Fechar</Button></div>
  </Modal>;
}

function CurrentTermsModal({onClose}){
  const [doc,setDoc]=useState(null);const [error,setError]=useState('');
  useEffect(()=>{let live=true;request('/api/terms/current').then(x=>{if(live)setDoc(x)}).catch(e=>{if(live)setError(message(e))});return()=>{live=false}},[]);
  return <Modal wide title="Termos e Condições" onClose={onClose}><Banner>{error}</Banner>{doc?<div className="terms-article"><LegalText content={doc.content}/></div>:<div className="modal-body"><PanelLoader loading/></div>}<div className="modal-footer"><Button onClick={onClose}>Fechar</Button></div></Modal>;
}

function LoginScreen({onLogin}){
  const [email,setEmail]=useState('');const [password,setPassword]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [terms,setTerms]=useState(null);const [privacyOpen,setPrivacyOpen]=useState(false);
  const save=async e=>{e.preventDefault();setBusy(true);setError('');try{await onLogin(email,password)}catch(e){setError(message(e))}finally{setBusy(false)}};
  const openTerms=async()=>{try{setTerms(await request('/api/public/terms/current'))}catch(e){setError(message(e))}};
  return <div className="login-page"><div className="login-art"><div className="login-art-top"><Brand compact/></div><img className="login-illustration" src="/edu-infra-visual.png" alt="Identidade visual EDU-Infra Analytics com escola, computadores, gráficos e escudo"/><div className="login-art-content"><p>TECNOLOGIA A SERVIÇO DA EDUCAÇÃO</p><h1>Transforme dados da infraestrutura em <em>decisões mais inteligentes.</em></h1><div className="login-features"><span><Cpu size={18}/> CPU e memória</span><span><Server size={18}/> Laboratórios</span><span><ShieldCheck size={18}/> Gestão responsável</span></div></div><footer>EDU-Infra Analytics 1.6 · Engenharia de Software</footer></div>
    <div className="login-form-side"><div className="login-form-card"><div className="login-mobile-brand"><Brand compact/></div><span className="login-lock"><LockKeyhole size={25}/></span><span className="overline">ACESSO À PLATAFORMA</span><h2>Bem-vindo de volta</h2><p className="login-subtitle">Entre com suas credenciais institucionais para continuar.</p><form className="form-stack" onSubmit={save}><Field label="E-mail institucional"><input type="email" required autoComplete="username" placeholder="seu.email@instituicao.edu.br" value={email} onChange={e=>setEmail(e.target.value)}/></Field><Field label="Senha"><input type="password" required autoComplete="current-password" placeholder="Digite sua senha" value={password} onChange={e=>setPassword(e.target.value)}/></Field><Banner>{error}</Banner><Button type="submit" className="login-submit" disabled={busy} icon={ArrowRight}>{busy?'Autenticando...':'Entrar no sistema'}</Button></form><div className="login-footer"><span><ShieldCheck size={16}/> Acesso autenticado e auditável</span><button type="button" onClick={openTerms}>Termos e Condições</button><button type="button" onClick={()=>setPrivacyOpen(true)}>Aviso de Privacidade</button></div></div></div>
    {privacyOpen&&<PrivacyNoticeModal onClose={()=>setPrivacyOpen(false)}/>}
    {terms&&<Modal title={terms.title||'Termos de uso'} wide onClose={()=>setTerms(null)}><div className="terms-article"><LegalText content={terms.content}/></div><div className="modal-footer"><Button onClick={()=>setTerms(null)}>Fechar</Button></div></Modal>}
  </div>;
}
function TermsGate({onAccepted,onLogout}){
  const [doc,setDoc]=useState(null);const [agree,setAgree]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [privacyOpen,setPrivacyOpen]=useState(false);
  useEffect(()=>{let active=true;request('/api/terms/current').then(r=>{if(active)setDoc(r)}).catch(e=>{if(active)setError(message(e))});return()=>{active=false}},[]);
  const accept=async()=>{if(!doc||!agree)return;setBusy(true);setError('');try{const res=await request('/api/terms/accept',{method:'POST',body:{version:doc.version,accepted:true}});setToken(res.access_token);onAccepted()}catch(e){setError(message(e));request('/api/terms/current').then(setDoc).catch(()=>{})}finally{setBusy(false)}};
  return <div className="terms-page"><header className="terms-topbar"><Brand compact/><button className="terms-logout" onClick={onLogout}><LogOut size={17}/> Sair da conta</button></header><div className="terms-gate-card"><div className="gate-steps"><span className="done">1. Login</span><span>→</span><span className="current">2. Termos e Condições</span><span>→</span><span>3. Painel</span></div><span className="terms-big-icon"><BookOpenCheck size={29}/></span><span className="overline">ETAPA OBRIGATÓRIA</span><h1>Antes de continuar</h1><p className="terms-gate-intro">Leia os Termos de Uso antes de acessar. O aceite contratual não substitui uma base legal de tratamento de dados pessoais.</p><div className="terms-doc-head"><div><strong>{doc?.title||'Carregando documento...'}</strong><span>Versão {doc?.version||'—'} · Publicado em {dateTime(doc?.published_at)}</span></div><span className="current-doc"><ShieldCheck size={16}/> Documento vigente</span></div><div className="terms-reader" tabIndex={0}>{doc?<LegalText content={doc.content}/>: 'Carregando o documento...'}</div><label className="terms-check"><input type="checkbox" checked={agree} onChange={e=>setAgree(e.target.checked)}/><span>Li e concordo com os Termos e Condições de Uso apresentados acima. Sei que esta confirmação não é consentimento genérico para tratamento de dados pessoais.</span></label><button type="button" className="privacy-link" onClick={()=>setPrivacyOpen(true)}><ShieldCheck size={16}/> Consultar Aviso de Privacidade e direitos LGPD</button><Banner>{error}</Banner><div className="terms-gate-actions"><Button kind="secondary" onClick={onLogout}>Sair</Button><Button disabled={!doc||!agree||busy} icon={CheckCircle2} onClick={accept}>{busy?'Registrando aceite...':'Aceitar e acessar painel'}</Button></div><p className="terms-footnote">O aceite é verificado pela API a cada sessão. A versão e a data da primeira aceitação ficam registradas no histórico.</p>{privacyOpen&&<PrivacyNoticeModal onClose={()=>setPrivacyOpen(false)}/>}</div></div>;
}

function AppShell({user,onLogout,onTerms,onPrivacy}){
  const [page,setPage]=useState('dashboard');const [drawer,setDrawer]=useState(false);
  const [renderKey,setRenderKey]=useState(0);
  const navigate=id=>{setPage(id);setDrawer(false);setRenderKey(k=>k+1);window.scrollTo?.(0,0)};
  const visible=NAV.filter(([id])=>id!=='users'||user.role==='ADMIN');
  const component={dashboard:<Dashboard navigate={navigate}/>,laboratories:<Laboratories user={user}/>,computers:<Computers user={user}/>,indicators:<Indicators/>,alerts:<Alerts user={user}/>,reports:<Reports/>,settings:<Settings user={user}/>,users:<UsersPage/>}[page]||<Dashboard navigate={navigate}/>;
  return <div className="app-shell">
    {drawer&&<button className="mobile-backdrop" onClick={()=>setDrawer(false)} aria-label="Fechar navegação"/>}
    <aside className={`sidebar ${drawer?'drawer-open':''}`}><div className="sidebar-brand"><Brand/></div><nav className="sidebar-nav" aria-label="Navegação principal">{visible.map(([id,label,Icon])=><button type="button" key={id} className={`nav-item ${page===id?'active':''}`} onClick={()=>navigate(id)} aria-current={page===id?'page':undefined}><Icon size={21} strokeWidth={1.9}/><span>{label}</span>{id==='alerts'&&<span className="nav-corner"/>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-separator"/><div className="sidebar-user"><span className="user-avatar"><UserRound size={23}/></span><div><strong>{user.name||ROLES[user.role]||'Usuário'}</strong><small>{user.email}</small></div></div><div className="sidebar-user-actions"><button type="button" onClick={onTerms} title="Ler Termos de uso"><BookOpenCheck size={17}/> Termos</button><button type="button" onClick={onPrivacy} title="Aviso de Privacidade"><ShieldCheck size={17}/> Privacidade</button><button type="button" onClick={onLogout} title="Sair do sistema"><LogOut size={17}/> Sair</button></div></div>
    </aside>
    <main className="app-main"><div className="mobile-topbar"><button type="button" aria-label="Abrir menu" onClick={()=>setDrawer(true)}><Menu size={23}/></button><Brand compact/><span className="mobile-role">{ROLES[user.role]||user.role}</span></div><div className="main-content" key={`${page}-${renderKey}`}>{component}</div><footer className="app-footer"><span>© {new Date().getFullYear()} EDU-Infra Analytics 1.6</span><span>Diagnóstico de infraestrutura tecnológica escolar • Dados reais de monitoramento</span></footer></main>
  </div>;
}

export default function App(){
  const [stage,setStage]=useState('checking');const [user,setUser]=useState(null);const [showTerms,setShowTerms]=useState(false);const [showPrivacy,setShowPrivacy]=useState(false);
  const logout=useCallback(()=>{setToken(null);setUser(null);setStage('login');setShowTerms(false);setShowPrivacy(false)},[]);
  const loadMe=useCallback(async()=>{const res=await request('/api/auth/me');setUser(res.user);setStage(res.terms_accepted?'app':'terms');return res},[]);
  useEffect(()=>{if(!getToken()){setStage('login');return;}loadMe().catch(logout)},[loadMe,logout]);
  useEffect(()=>{const terms=()=>{setShowTerms(false);setStage('terms')};const unauthorized=()=>logout();window.addEventListener('edu-terms-required',terms);window.addEventListener('edu-unauthorized',unauthorized);return()=>{window.removeEventListener('edu-terms-required',terms);window.removeEventListener('edu-unauthorized',unauthorized)}},[logout]);
  const login=async(email,password)=>{const result=await request('/api/auth/login',{method:'POST',body:{email,password}});setToken(result.access_token);await loadMe()};
  if(stage==='checking')return <div className="app-loading"><span className="loading-spinner"/> Validando sessão...</div>;
  if(stage==='login')return <LoginScreen onLogin={login}/>;
  if(stage==='terms')return <TermsGate onAccepted={()=>loadMe()} onLogout={logout}/>;
  return <><AppShell user={user} onLogout={logout} onTerms={()=>setShowTerms(true)} onPrivacy={()=>setShowPrivacy(true)}/>{showTerms&&<CurrentTermsModal onClose={()=>setShowTerms(false)}/>} {showPrivacy&&<PrivacyNoticeModal onClose={()=>setShowPrivacy(false)}/>}</>;
}
