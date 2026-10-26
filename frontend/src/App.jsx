import { useCallback, useEffect, useMemo, useState } from 'react';

const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '') + '/api/v1';

async function http(path, token, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (res.status === 204) return null;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg).join('; ') : 'Não foi possível completar a operação.';
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }
  return body;
}

function useLoad(loader, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [tick, setTick] = useState(0);
  const reload = useCallback(() => setTick(x => x + 1), []);
  useEffect(() => {
    let current = true;
    setError('');
    loader().then(value => current && setData(value)).catch(err => current && setError(err.message));
    return () => { current = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, ...deps]);
  return { data, error, reload };
}

const statusLabels = { sem_coleta: 'Sem coleta', online: 'Online', offline: 'Offline', atencao: 'Atenção', critico: 'Crítico' };
function Status({ value }) { return <span className={`status status-${value}`}>{statusLabels[value] || value}</span>; }
function Notice({ children, kind = 'info' }) { return children ? <div className={`notice ${kind}`} role="status">{children}</div> : null; }
function Empty({ label }) { return <div className="empty"><div className="empty-icon">◇</div><p>{label}</p></div>; }
function Section({ title, subtitle, action, children }) { return <section className="section"><header className="section-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</header>{children}</section>; }
function Metric({ name, value, helper, tone }) { return <article className={`metric ${tone || ''}`}><small>{name}</small><strong>{value ?? '—'}</strong><span>{helper}</span></article>; }
function FormActions({ cancel, editing, disabled }) { return <div className="actions"><button className="button primary" disabled={disabled}>{editing ? 'Salvar alterações' : 'Cadastrar'}</button><button type="button" className="button secondary" onClick={cancel}>Cancelar</button></div>; }

function Login({ onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [waiting, setWaiting] = useState(false);
  async function submit(e) {
    e.preventDefault(); setError(''); setWaiting(true);
    try { onSuccess(await http('/auth/login', null, { method: 'POST', body: JSON.stringify({ email, password }) })); }
    catch (err) { setError(err.message); }
    finally { setWaiting(false); }
  }
  return <main className="login-scene"><div className="login-panel"><div className="mark">E<span>·</span>I</div><p className="eyebrow">EDU-INFRA ANALYTICS</p><h1>Infraestrutura educacional sob controle.</h1><p className="login-intro">Entre com sua conta institucional. Os indicadores serão calculados apenas com informações cadastradas e coletadas.</p><form onSubmit={submit}><label>E-mail institucional<input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="username" required /></label><label>Senha<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label><Notice kind="error">{error}</Notice><button className="button primary wide" disabled={waiting}>{waiting ? 'Validando acesso…' : 'Entrar na plataforma'}</button></form><small>Primeiro acesso: configure o administrador pelo terminal, sem contas de exemplo.</small></div><aside className="login-visual"><div className="outline"><span className="big-glyph">∷</span><p>Diagnóstico baseado em dados.<br/>Planejamento baseado em evidências.</p></div></aside></main>;
}

function Dashboard({ token }) {
  const api = path => http(path, token);
  const { data, error } = useLoad(() => Promise.all([api('/dashboard'), api('/laboratorios'), api('/alertas')]));
  if (error) return <Notice kind="error">{error}</Notice>;
  if (!data) return <p>Carregando dados reais…</p>;
  const [summary, labs, alerts] = data;
  const pcs = summary.computers;
  return <>
    <Section title="Visão geral" subtitle="Indicadores gerados somente a partir de registros do seu banco de dados." />
    <div className="metric-grid"><Metric name="Laboratórios cadastrados" value={summary.laboratories} helper="Ambientes registrados"/><Metric name="Computadores cadastrados" value={pcs.total} helper="Equipamentos vinculados"/><Metric name="Equipamentos sem coleta" value={pcs.sem_coleta} helper="Aguardando telemetria" tone="amber"/><Metric name="Disponibilidade" value={summary.availability_percent === null ? '—' : `${summary.availability_percent}%`} helper="Não disponível sem medições" tone="blue" /></div>
    <div className="columns"><div className="panel"><h3>Laboratórios</h3>{labs.length ? <table><thead><tr><th>Nome</th><th>Localização</th><th>Computadores</th></tr></thead><tbody>{labs.map(l => <tr key={l.id}><td>{l.name}</td><td>{l.location}</td><td>{l.computer_count}</td></tr>)}</tbody></table> : <Empty label="Nenhum laboratório cadastrado. Comece pela seção Laboratórios." />}</div>
    <div className="panel"><h3>Alertas operacionais</h3>{alerts.length ? alerts.map(a => <p key={a.computer_id}><Status value={a.status}/> {a.hostname}</p>) : <Empty label="Nenhum alerta derivado de medições disponíveis." />}</div></div>
    <div className="explain"><strong>IIE ainda não calculado.</strong> A monografia determina que a fórmula do índice seja definida e validada antes de gerar pontuações. Por isso, nenhuma nota arbitrária é exibida aqui.</div>
  </>;
}

function Laboratories({ token, role }) {
  const canWrite = ['admin', 'tecnico'].includes(role);
  const { data, error, reload } = useLoad(() => http('/laboratorios', token));
  const initial = { name: '', location: '', is_active: true };
  const [form, setForm] = useState(initial);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const start = lab => { setForm(lab ? { name: lab.name, location: lab.location, is_active: lab.is_active } : initial); setEditing(lab?.id ?? null); setOpen(true); setMessage(''); };
  async function submit(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { await http(`/laboratorios${editing ? `/${editing}` : ''}`, token, { method: editing ? 'PUT' : 'POST', body: JSON.stringify(form) }); setOpen(false); setMessage(editing ? 'Laboratório atualizado.' : 'Laboratório cadastrado.'); reload(); }
    catch (err) { setMessage(err.message); } finally { setBusy(false); }
  }
  async function remove(lab) {
    if (!window.confirm(`Excluir definitivamente o laboratório "${lab.name}"? Esta ação será bloqueada se houver computadores vinculados.`)) return;
    try { await http(`/laboratorios/${lab.id}`, token, { method: 'DELETE' }); setMessage('Laboratório excluído.'); reload(); }
    catch (err) { setMessage(err.message); }
  }
  return <Section title="Laboratórios" subtitle="Cadastro, atualização e exclusão controlada de ambientes." action={canWrite && <button className="button primary" onClick={() => start(null)}>+ Novo laboratório</button>}>
    <Notice>{message}</Notice><Notice kind="error">{error}</Notice>
    {open && <form className="panel edit-panel" onSubmit={submit}><h3>{editing ? 'Editar laboratório' : 'Cadastrar laboratório'}</h3><div className="fields"><label>Nome do laboratório<input required minLength="2" maxLength="100" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label><label>Localização<input required minLength="2" maxLength="160" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} /></label><label className="checkbox-label"><input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })}/> Laboratório ativo</label></div><FormActions editing={editing} cancel={() => setOpen(false)} disabled={busy}/></form>}
    <div className="panel table-panel">{data?.length ? <div className="table-scroll"><table><thead><tr><th>Laboratório</th><th>Localização</th><th>Situação</th><th>Computadores</th>{canWrite && <th>Ações</th>}</tr></thead><tbody>{data.map(lab => <tr key={lab.id}><td><strong>{lab.name}</strong></td><td>{lab.location}</td><td>{lab.is_active ? 'Ativo' : 'Inativo'}</td><td>{lab.computer_count}</td>{canWrite && <td className="table-actions"><button onClick={() => start(lab)} className="text-button">Editar</button>{role === 'admin' && <button onClick={() => remove(lab)} className="text-button danger">Excluir</button>}</td>}</tr>)}</tbody></table></div> : <Empty label="O banco está vazio. Cadastre o primeiro laboratório para começar." />}</div>
    <p className="hint">Exclusão de laboratório: somente administrador; proibida enquanto existirem computadores associados (RN01).</p>
  </Section>;
}

function Computers({ token, role }) {
  const canWrite = ['admin', 'tecnico'].includes(role);
  const { data, error, reload } = useLoad(() => Promise.all([http('/computadores', token), http('/laboratorios', token)]));
  const [filter, setFilter] = useState('');
  const [form, setForm] = useState({ hostname: '', ip_address: '', laboratory_id: '' });
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [pcs, labs] = data || [[], []];
  const labNames = Object.fromEntries(labs.map(l => [l.id, l.name]));
  function start(pc) { setForm(pc ? { hostname: pc.hostname, ip_address: pc.ip_address || '', laboratory_id: String(pc.laboratory_id) } : { hostname: '', ip_address: '', laboratory_id: '' }); setEditing(pc?.id ?? null); setOpen(true); setMessage(''); }
  async function submit(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { await http(`/computadores${editing ? `/${editing}` : ''}`, token, { method: editing ? 'PUT' : 'POST', body: JSON.stringify({ hostname: form.hostname, ip_address: form.ip_address || null, laboratory_id: Number(form.laboratory_id) }) }); setOpen(false); setMessage(editing ? 'Computador atualizado.' : 'Computador cadastrado.'); reload(); }
    catch (err) { setMessage(err.message); } finally { setBusy(false); }
  }
  async function remove(pc) {
    if (!window.confirm(`Excluir definitivamente o computador "${pc.hostname}"?`)) return;
    try { await http(`/computadores/${pc.id}`, token, { method: 'DELETE' }); setMessage('Computador excluído.'); reload(); }
    catch (err) { setMessage(err.message); }
  }
  const filtered = pcs.filter(p => (p.hostname + ' ' + (labNames[p.laboratory_id] || '')).toLowerCase().includes(filter.toLowerCase()));
  return <Section title="Computadores" subtitle="Equipamentos vinculados a laboratórios reais." action={canWrite && <button className="button primary" onClick={() => start(null)} disabled={!labs.length}>+ Novo computador</button>}>
    <Notice>{message}</Notice><Notice kind="error">{error}</Notice>
    {!labs.length && <Notice>Cadastre um laboratório antes de cadastrar computadores.</Notice>}
    {open && <form className="panel edit-panel" onSubmit={submit}><h3>{editing ? 'Editar computador' : 'Cadastrar computador'}</h3><div className="fields"><label>Hostname<input required maxLength="100" minLength="2" value={form.hostname} onChange={e => setForm({ ...form, hostname: e.target.value })}/></label><label>Endereço IP (opcional)<input value={form.ip_address} onChange={e => setForm({ ...form, ip_address: e.target.value })} placeholder="IPv4 ou IPv6"/></label><label>Laboratório<select required value={form.laboratory_id} onChange={e => setForm({ ...form, laboratory_id: e.target.value })}><option value="">Selecione um laboratório</option>{labs.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}</select></label></div><FormActions cancel={() => setOpen(false)} editing={editing} disabled={busy}/></form>}
    <div className="panel table-panel"><div className="toolbar"><input className="search" aria-label="Buscar computadores" placeholder="Buscar computador ou laboratório…" value={filter} onChange={e => setFilter(e.target.value)} /><small>{filtered.length} resultado(s)</small></div>{pcs.length ? (filtered.length ? <div className="table-scroll"><table><thead><tr><th>Hostname</th><th>IP</th><th>Laboratório</th><th>Estado</th><th>Última coleta</th>{canWrite && <th>Ações</th>}</tr></thead><tbody>{filtered.map(pc => <tr key={pc.id}><td><strong>{pc.hostname}</strong></td><td>{pc.ip_address || '—'}</td><td>{labNames[pc.laboratory_id] || '—'}</td><td><Status value={pc.status}/></td><td>{pc.last_seen_at ? new Date(pc.last_seen_at).toLocaleString('pt-BR') : 'Nunca'}</td>{canWrite && <td className="table-actions"><button className="text-button" onClick={() => start(pc)}>Editar</button><button className="text-button danger" onClick={() => remove(pc)}>Excluir</button></td>}</tr>)}</tbody></table></div> : <Empty label="Nenhum computador corresponde à busca." />) : <Empty label="Nenhum computador cadastrado. Os registros não são gerados automaticamente." />}</div>
    <p className="hint">"Sem coleta" significa que ainda não existe telemetria do agente. Um cadastro não torna um equipamento automaticamente online.</p>
  </Section>;
}

function Indicators({ token }) {
  const { data, error } = useLoad(() => http('/indicadores', token));
  return <Section title="Indicadores" subtitle="Informações sem cálculo artificial de notas."><Notice kind="error">{error}</Notice>{data ? <><div className="metric-grid"><Metric name="Laboratórios" value={data.laboratories}/><Metric name="Computadores" value={data.computers.total}/><Metric name="Sem coleta" value={data.computers.sem_coleta}/><Metric name="IIE" value="—" helper="Fórmula aguardando validação"/></div><div className="panel"><h3>Por laboratório</h3>{data.laboratory_details.length ? <table><thead><tr><th>Laboratório</th><th>Computadores</th><th>IIE</th></tr></thead><tbody>{data.laboratory_details.map(l => <tr key={l.id}><td>{l.name}</td><td>{l.computer_count}</td><td>Não calculado</td></tr>)}</tbody></table> : <Empty label="Nenhum laboratório registrado." />}</div></> : <p>Carregando indicadores…</p>}</Section>;
}

function Alerts({ token }) {
  const { data, error } = useLoad(() => http('/alertas', token));
  return <Section title="Alertas" subtitle="Situações derivadas de métricas observadas e verificadas."><Notice kind="error">{error}</Notice><div className="panel">{data?.length ? data.map(a => <p className="alert-row" key={a.computer_id}><Status value={a.status}/><strong>{a.hostname}</strong><span>Laboratório #{a.laboratory_id}</span></p>) : <Empty label="Sem alertas registrados a partir de medições disponíveis." />}</div></Section>;
}

function Reports({ token }) {
  const { data, error } = useLoad(() => http('/relatorios/resumo', token));
  return <Section title="Relatório-resumo" subtitle="Retrato do estado cadastrado, sem métricas fabricadas."><Notice kind="error">{error}</Notice>{data ? <div className="panel report"><h3>Resumo da infraestrutura</h3><p>Gerado em {new Date().toLocaleString('pt-BR')}</p><dl><dt>Laboratórios</dt><dd>{data.laboratories}</dd><dt>Computadores</dt><dd>{data.computers.total}</dd><dt>Sem coleta</dt><dd>{data.computers.sem_coleta}</dd><dt>Online</dt><dd>{data.computers.online}</dd><dt>Offline</dt><dd>{data.computers.offline}</dd><dt>Atenção / Crítico</dt><dd>{data.computers.atencao} / {data.computers.critico}</dd><dt>IIE</dt><dd>Não calculado</dd></dl><p className="hint">Exportação de relatórios completos com séries históricas está prevista para a fase de monitoramento.</p></div> : <p>Carregando resumo…</p>}</Section>;
}

function Audit({ token }) {
  const { data, error } = useLoad(() => http('/auditoria', token));
  return <Section title="Auditoria" subtitle="Últimos 100 eventos administrativos e de autenticação."><Notice kind="error">{error}</Notice><div className="panel table-panel">{data?.length ? <div className="table-scroll"><table><thead><tr><th>Quando</th><th>Ação</th><th>Entidade</th><th>ID do usuário</th></tr></thead><tbody>{data.map(log => <tr key={log.id}><td>{new Date(log.created_at).toLocaleString('pt-BR')}</td><td>{log.action}</td><td>{log.entity}{log.entity_id ? ` #${log.entity_id}` : ''}</td><td>{log.user_id ?? '—'}</td></tr>)}</tbody></table></div> : <Empty label="Nenhum evento registrado." />}</div></Section>;
}

function Users({ token }) {
  const { data, error, reload } = useLoad(() => http('/users', token));
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'gestor' });
  const [show, setShow] = useState(false);
  const [message, setMessage] = useState('');
  async function create(e) {
    e.preventDefault(); setMessage('');
    try { await http('/users', token, { method: 'POST', body: JSON.stringify(form) }); setShow(false); setForm({ name: '', email: '', password: '', role: 'gestor' }); setMessage('Usuário cadastrado.'); reload(); }
    catch (err) { setMessage(err.message); }
  }
  async function toggle(user) {
    if (!window.confirm(`${user.is_active ? 'Desativar' : 'Reativar'} a conta de ${user.name}?`)) return;
    try { await http(`/users/${user.id}`, token, { method: 'PATCH', body: JSON.stringify({ is_active: !user.is_active }) }); setMessage('Situação da conta atualizada.'); reload(); }
    catch (err) { setMessage(err.message); }
  }
  return <Section title="Usuários e acesso" subtitle="Criação controlada de contas e gestão de perfis." action={<button className="button primary" onClick={() => setShow(x => !x)}>+ Criar usuário</button>}><Notice>{message}</Notice><Notice kind="error">{error}</Notice>{show && <form className="panel edit-panel" onSubmit={create}><h3>Novo usuário</h3><div className="fields"><label>Nome<input required minLength="2" maxLength="100" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}/></label><label>E-mail<input type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}/></label><label>Senha inicial (mínimo 12 caracteres)<input type="password" required minLength="12" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}/></label><label>Perfil<select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}><option value="gestor">Gestor</option><option value="tecnico">Técnico</option><option value="admin">Administrador</option></select></label></div><FormActions cancel={() => setShow(false)}/></form>}
  <div className="panel table-panel">{data?.length ? <table><thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Situação</th><th>Ação</th></tr></thead><tbody>{data.map(user => <tr key={user.id}><td>{user.name}</td><td>{user.email}</td><td>{user.role}</td><td>{user.is_active ? 'Ativo' : 'Inativo'}</td><td><button className="text-button" onClick={() => toggle(user)}>{user.is_active ? 'Desativar' : 'Reativar'}</button></td></tr>)}</tbody></table> : <Empty label="Nenhum usuário encontrado." />}</div></Section>;
}

function Privacy() { return <Section title="Privacidade" subtitle="Limites de coleta e responsabilidade sobre os dados."><div className="panel legal"><h3>Finalidade dos dados</h3><p>O EDU-Infra Analytics organiza cadastros e métricas de infraestrutura de laboratórios educacionais. Os únicos dados pessoais previstos nesta etapa são nome, e-mail e perfil de acesso dos usuários.</p><p>Não devem ser cadastrados dados individuais de estudantes, notas, frequência ou informações sensíveis. A instituição responsável deve definir base legal, retenção, proteção e atendimento aos titulares antes de utilizar a plataforma em produção.</p><p>Os registros administrativos de auditoria servem à rastreabilidade e precisam respeitar política de retenção definida pela instituição.</p></div></Section>; }

const navigation = [ ['dashboard', 'Painel'], ['laboratorios', 'Laboratórios'], ['computadores', 'Computadores'], ['indicadores', 'Indicadores'], ['alertas', 'Alertas'], ['relatorios', 'Relatórios'], ['auditoria', 'Auditoria', 'admin'], ['usuarios', 'Usuários', 'admin'], ['privacidade', 'Privacidade'] ];

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('edu_token') || '');
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('dashboard');
  const [checking, setChecking] = useState(Boolean(token));
  const logout = useCallback(() => { sessionStorage.removeItem('edu_token'); setToken(''); setUser(null); setPage('dashboard'); }, []);
  useEffect(() => {
    if (!token) { setChecking(false); return; }
    let active = true;
    setChecking(true);
    http('/auth/me', token).then(u => active && setUser(u)).catch(() => active && logout()).finally(() => active && setChecking(false));
    return () => { active = false; };
  }, [token, logout]);
  function signedIn(result) { sessionStorage.setItem('edu_token', result.access_token); setToken(result.access_token); setUser(result.user); setPage('dashboard'); }
  const view = useMemo(() => ({ dashboard: <Dashboard token={token}/>, laboratorios: <Laboratories token={token} role={user?.role}/>, computadores: <Computers token={token} role={user?.role}/>, indicadores: <Indicators token={token}/>, alertas: <Alerts token={token}/>, relatorios: <Reports token={token}/>, auditoria: <Audit token={token}/>, usuarios: <Users token={token}/>, privacidade: <Privacy/> }), [token, user?.role]);
  if (checking) return <div className="boot">Verificando sessão…</div>;
  if (!token || !user) return <Login onSuccess={signedIn}/>;
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="mark smaller">E<span>·</span>I</div><div><strong>EDU-INFRA</strong><small>ANALYTICS</small></div></div><p className="nav-label">PLATAFORMA</p><nav aria-label="Navegação principal">{navigation.filter(([, , access]) => !access || access === user.role).map(([key, label]) => <button key={key} type="button" className={page === key ? 'selected' : ''} onClick={() => setPage(key)}><span className="nav-glyph">{key === 'dashboard' ? '◫' : key === 'laboratorios' ? '▦' : key === 'computadores' ? '▣' : key === 'indicadores' ? '⌁' : key === 'alertas' ? '◇' : key === 'relatorios' ? '≡' : key === 'auditoria' ? '⌘' : key === 'usuarios' ? '◉' : '⊙'}</span>{label}</button>)}</nav><div className="sidebar-foot"><span className="mini-dot"/> Base sem dados artificiais</div></aside><div className="work-area"><header className="topbar"><div className="crumb">EDU-Infra Analytics <span>/ {navigation.find(n => n[0] === page)?.[1]}</span></div><div className="user-area"><div><strong>{user.name}</strong><small>{user.role}</small></div><button onClick={logout} className="button secondary compact">Sair</button></div></header><main className="content" key={page}>{view[page]}</main><footer>EDU-Infra Analytics • PFC Engenharia de Software • Dados do seu ambiente</footer></div></div>;
}
