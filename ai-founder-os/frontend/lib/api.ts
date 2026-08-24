const API_BASE = "http://localhost:8000/api";

export async function fetcher(url: string) {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `An error occurred while fetching the data: ${res.status}`);
  }
  return res.json();
}

export async function postApi(url: string, data: any) {
  const res = await fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `An error occurred while posting the data: ${res.status}`);
  }
  return res.json();
}

export async function putApi(url: string, data: any) {
  const res = await fetch(`${API_BASE}${url}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `An error occurred while putting the data: ${res.status}`);
  }
  return res.json();
}
