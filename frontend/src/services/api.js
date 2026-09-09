const API_URL = "http://127.0.0.1:8000";

export async function getApiStatus() {
  const response = await fetch(`${API_URL}/`);

  if (!response.ok) {
    throw new Error("Erro ao acessar API");
  }

  return response.json();
}