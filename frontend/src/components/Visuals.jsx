import React from 'react';
import { Activity, Database, Monitor, Server } from 'lucide-react';

export const number = value => value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : new Intl.NumberFormat('pt-BR', {maximumFractionDigits: 1}).format(value);
export const dateTime = value => value ? new Date(value).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'}) : '—';
export const clockTime = value => value ? new Date(value).toLocaleTimeString('pt-BR', {hour:'2-digit',minute:'2-digit'}) : '—';
export const shortDate = value => value ? new Date(value).toLocaleDateString('pt-BR', {day:'2-digit', month:'2-digit'}) : '—';

export function Empty({title='Nenhum registro disponível', description='Quando os dados forem recebidos, aparecerão aqui.', icon: Icon=Database, compact=false}) {
  return <div className={`empty-state ${compact ? 'compact' : ''}`}><span className="empty-icon"><Icon size={24}/></span><strong>{title}</strong><p>{description}</p></div>;
}

export function Badge({status}) {
  const statuses = {
    online:['Online','good'], offline:['Offline','bad'], inactive:['Inativo','muted'], sem_coleta:['Sem coleta','muted'],
    adequado:['Saudável','good'], atencao:['Atenção','warn'], critico:['Crítico','bad'], sem_dados:['Sem dados','muted'],
    open:['Aberto','bad'], acknowledged:['Reconhecido','warn'], resolved:['Resolvido','good'],
    active:['Ativo','good'], maintenance:['Manutenção','muted']
  };
  const [label,tone] = statuses[status] || [status || '—', 'muted'];
  return <span className={`status-badge ${tone}`}><span className="status-dot"/>{label}</span>;
}

export function StatCard({label,value,caption,icon:Icon=Activity,tone='blue'}) {
  return <article className={`stat-card tone-${tone}`}>
    <div className="stat-copy"><div className="stat-heading">{label}</div><div className="stat-number">{value}</div>{caption && <div className="stat-caption">{caption}</div>}</div>
    <div className="stat-icon"><Icon size={29} strokeWidth={2.2}/></div>
  </article>;
}

export function DonutChart({online=0,offline=0,unknown=0,inactive=0}) {
  const total = online+offline+unknown+inactive;
  const values = [online,offline,unknown,inactive];
  const colors = ['#20a35b','#f13e47','#cdd4df','#8191ae'];
  const items = [{name:'Online',value:online},{name:'Offline',value:offline},{name:'Sem coleta',value:unknown},{name:'Inativos',value:inactive}];
  let offset=0;
  const stops=values.map((v,i)=>{
    const start=offset; offset+=total ? (100*v/total) : 0;
    return `${colors[i]} ${start}% ${offset}%`;
  }).join(', ');
  const bg=total ? `conic-gradient(${stops})` : 'conic-gradient(#e9eef5 0 100%)';
  return <div className="donut-layout">
    <div className="donut-chart" role="img" aria-label={`Distribuição: ${online} online, ${offline} offline, ${unknown} sem coleta, ${inactive} inativos`} style={{background:bg}}><div className="donut-hole"><strong>{total}</strong><span>equipamentos</span></div></div>
    <div className="donut-legend">{items.map((item,i)=><div className="donut-legend-item" key={item.name}><span className="legend-key"><i style={{backgroundColor:colors[i]}}/>{item.name}</span><strong>{item.value} <small>({total ? Math.round(item.value/total*100) : 0}%)</small></strong></div>)}</div>
  </div>;
}

const SERIES = [
  {key:'cpu_percent',label:'CPU',color:'#2478f2'},
  {key:'memory_percent',label:'RAM',color:'#21a366'},
  {key:'disk_percent',label:'Disco',color:'#ff7a14'}
];
export function MetricTrend({samples=[]}) {
  const data=[...samples].filter(x=>Number.isFinite(Number(x.cpu_percent)) && Number.isFinite(Number(x.memory_percent)) && Number.isFinite(Number(x.disk_percent))).sort((a,b)=>new Date(a.collected_at)-new Date(b.collected_at)).slice(-28);
  if(!data.length) return <Empty compact icon={Activity} title="Aguardando medições" description="Execute o agente para construir um gráfico com dados reais."/>;
  const w=780,h=260,l=42,r=14,t=20,b=36;
  const pw=w-l-r,ph=h-t-b;
  const px=i=>l+pw*(data.length===1?.5:i/(data.length-1));
  const py=v=>t+ph*(1-Math.min(100,Math.max(0,Number(v)))/100);
  const ticks=data.length<=6?data.map((_,i)=>i):[0,Math.floor((data.length-1)/4),Math.floor((data.length-1)/2),Math.floor(3*(data.length-1)/4),data.length-1];
  return <div className="trend-chart">
    <div className="chart-legend">{SERIES.map(s=><span key={s.key}><i style={{background:s.color}}/>{s.label}</span>)}</div>
    <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Gráfico de histórico de CPU, memória RAM e disco em porcentagem" preserveAspectRatio="xMidYMid meet">
      {[0,25,50,75,100].map(tick=><g key={tick}><line x1={l} x2={w-r} y1={py(tick)} y2={py(tick)} stroke="#e2e9f3" strokeDasharray="4 4"/><text x={l-10} y={py(tick)+4} textAnchor="end" fontSize="12" fill="#7a8aa5">{tick}%</text></g>)}
      {SERIES.map(s=><g key={s.key}><polyline fill="none" stroke={s.color} strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" points={data.map((d,i)=>`${px(i)},${py(d[s.key])}`).join(' ')}/>{data.length===1&&<circle cx={px(0)} cy={py(data[0][s.key])} r="5" fill={s.color}/>}</g>)}
      {ticks.map(i=><text key={i} x={px(i)} y={h-10} textAnchor="middle" fontSize="12" fill="#70809a">{clockTime(data[i]?.collected_at)}</text>)}
    </svg>
    <span className="chart-footnote">Últimas {data.length} leituras recebidas • horário local</span>
  </div>;
}

export function LaboratoryBars({items=[]}) {
  const values=items.filter(x=>x.total>0);
  if(!values.length)return <Empty compact icon={Server} title="Sem equipamentos cadastrados" description="Os gráficos aparecem quando houver computadores associados aos laboratórios."/>;
  const highest=Math.max(...values.map(x=>x.total),1);
  return <div className="bar-chart">
    <div className="bar-legend"><span><i className="total"/> Equipamentos totais</span><span><i className="online"/> Equipamentos online</span></div>
    <div className="bar-plot"><div className="bar-gridlines"><span>{highest}</span><span>{Math.round(highest/2)}</span><span>0</span></div><div className="bar-clusters">{values.map(lab=><div className="bar-cluster" key={lab.laboratory_id}><div className="bar-pair"><div className="bar-column total" title={`${lab.total} equipamentos`} style={{height:`${Math.max(2,lab.total/highest*100)}%`}}><b>{lab.total}</b></div><div className="bar-column online" title={`${lab.online} online`} style={{height:`${lab.online?Math.max(2,lab.online/highest*100):0}%`}}>{lab.online>0&&<b>{lab.online}</b>}</div></div><span title={lab.laboratory}>{lab.laboratory}</span></div>)}</div></div>
  </div>;
}

export function ScoreTrend({samples=[]}) {
  const data=[...samples].filter(x=>x.score!==null && x.score!==undefined).sort((a,b)=>new Date(a.calculated_at)-new Date(b.calculated_at)).slice(-30);
  if(!data.length)return <Empty icon={Activity} compact title="Sem histórico do indicador" description="Uma medição do agente iniciará o histórico de IIE."/>;
  const w=700,h=230,l=42,r=15,t=22,b=32;
  const px=i=>l+(w-l-r)*(data.length===1?.5:i/(data.length-1));
  const py=v=>t+(h-t-b)*(1-Number(v)/100);
  return <div className="trend-chart"><svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Evolução histórica do IIE">
    {[0,25,50,75,100].map(n=><g key={n}><line x1={l} x2={w-r} y1={py(n)} y2={py(n)} stroke="#e2e9f3" strokeDasharray="4 4"/><text x={l-9} y={py(n)+4} textAnchor="end" fontSize="11" fill="#7a8aa5">{n}</text></g>)}
    <polyline points={data.map((d,i)=>`${px(i)},${py(d.score)}`).join(' ')} fill="none" stroke="#2478f2" strokeWidth="3" strokeLinejoin="round"/>
    {data.length===1&&<circle cx={px(0)} cy={py(data[0].score)} r="5" fill="#2478f2"/>}
    {[0,Math.floor((data.length-1)/2),data.length-1].filter((x,i,a)=>a.indexOf(x)===i).map(i=><text key={i} x={px(i)} y={h-7} textAnchor="middle" fontSize="11" fill="#70809a">{shortDate(data[i]?.calculated_at)}</text>)}
  </svg></div>;
}
