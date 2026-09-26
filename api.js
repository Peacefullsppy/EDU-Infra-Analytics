const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "edu_infra_token";

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}, authenticated = true) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
  }

  if (authenticated && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Erro ao acessar a API.";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Mantém a mensagem padrão.
    }

    if (response.status === 401 && authenticated) {
      clearToken();
    }

    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}

export async function login(email, password) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const data = await request(
    "/auth/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    },
    false,
  );

  setToken(data.access_token);
  return data;
}

export function getMe() { return request("/auth/me"); }
export function getDashboard() { return request("/dashboard"); }
export function getLaboratorios() { return request("/laboratorios"); }
export function createLaboratorio(data) {
  return request("/laboratorios", { method: "POST", body: JSON.stringify(data) });
}
export function getComputadores() { return request("/computadores"); }
export function createComputador(data) {
  return request("/computadores", { method: "POST", body: JSON.stringify(data) });
}
export function getAlertas() { return request("/alertas"); }
export function getAuditoria(limit = 100) { return request(`/auditoria?limite=${limit}`); }
export function consultarCep(cep) { return request(`/integracoes/cep/${encodeURIComponent(cep)}`); }
export function getLgpd() { return request("/legal/lgpd", {}, false); }
