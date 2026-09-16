const API_BASE_URL = 'http://172.20.10.8:8000';

async function parseJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch (error) {
    return text;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  const data = await parseJson(response);

  if (!response.ok) {
    const message =
      typeof data === 'string' && data ? data : data?.detail || 'Request failed';
    throw new Error(message);
  }

  return data;
}

export async function getEmergencies(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return request(`/api/emergencies${query}`);
}

export async function getEmergency(id) {
  return request(`/api/emergencies/${id}`);
}

export async function updateEmergencyStatus(id, status) {
  return request(`/api/emergencies/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function updateEmergencyCategory(id, operational_category) {
  return request(`/api/emergencies/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ operational_category }),
  });
}

export async function updateEmergencyPriority(id, manual_priority) {
  return request(`/api/emergencies/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ manual_priority }),
  });
}
