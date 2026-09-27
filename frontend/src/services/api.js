const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("edu_infra_token");
}

export function saveSession(data) {
  localStorage.setItem("edu_infra_token", data.access_token);
  localStorage.setItem("edu_infra_user", JSON.stringify(data.user));
}

export function clearSession() {
  localStorage.removeItem("edu_infra_token");
  localStorage.removeItem("edu_infra_user");
}

export function getSavedUser() {
  try {
    return JSON.parse(localStorage.getItem("edu_infra_user") || "null");
  } catch {
    return null;
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
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

    if (response.status === 401 && path !== "/auth/login") {
      clearSession();
    }

    throw new Error(message);
  }

  return response.json();
}

export function login(email, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getMe() { return request("/auth/me"); }
export function getHealth() { return request("/health"); }
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
export function getIndicadores() { return request("/indicadores"); }
export function getRelatorioResumo() { return request("/relatorios/resumo"); }
export function consultarCep(cep) { return request(`/externo/cep/${encodeURIComponent(cep)}`); }
export function getAuditoria(limit = 30) { return request(`/auditoria?limit=${limit}`); }
export function getPrivacidade() { return request("/privacidade"); }
