export const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export const getToken = () => sessionStorage.getItem('eia_access_token');
export const setToken = token => token ? sessionStorage.setItem('eia_access_token', token) : sessionStorage.removeItem('eia_access_token');

export async function request(path, { method='GET', body, headers = {} } = {}) {
  const token = getToken();
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers: {...(body ? {'Content-Type':'application/json'} : {}), ...(token ? {Authorization:`Bearer ${token}`} : {}), ...headers},
    ...(body ? {body:JSON.stringify(body)} : {}),
    cache:'no-store'
  });
  if (response.status === 428) window.dispatchEvent(new Event('edu-terms-required'));
  if (response.status === 401 && !path.includes('/auth/login')) window.dispatchEvent(new Event('edu-unauthorized'));
  if (!response.ok) {
    const data = await response.json().catch(()=>({}));
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg).join('; ') : `Erro HTTP ${response.status}`);
  }
  if (response.status === 204) return null;
  return response.json();
}
export async function download(path, filename) {
  const response = await fetch(`${BASE}${path}`, { headers: { Authorization: `Bearer ${getToken()}` }, cache:'no-store' });
  if (response.status === 428) window.dispatchEvent(new Event('edu-terms-required'));
  if (!response.ok) throw new Error(`Não foi possível exportar: HTTP ${response.status}`);
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
