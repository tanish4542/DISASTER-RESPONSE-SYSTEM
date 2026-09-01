const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function createEmergencyOnServer(emergency) {
  const response = await fetch(`${API_BASE_URL}/api/emergencies`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: emergency.message,
      latitude: emergency.latitude ?? 0,
      longitude: emergency.longitude ?? 0,
      people_affected: emergency.people_affected,
      injured: Boolean(emergency.injured),
      trapped: Boolean(emergency.trapped),
      fire: Boolean(emergency.fire),
      medical_emergency: Boolean(emergency.medical_emergency),
      urgency: emergency.urgency,
    }),
  });

  if (!response.ok) {
    throw new Error(`Emergency request failed with status ${response.status}`);
  }

  return response.json();
}
