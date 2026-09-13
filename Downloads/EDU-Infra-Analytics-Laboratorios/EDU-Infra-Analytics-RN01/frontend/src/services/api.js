const API_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    let message = "Erro ao acessar a API.";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Mantém a mensagem padrão.
    }
    throw new Error(message);
  }

  return response.json();
}

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
