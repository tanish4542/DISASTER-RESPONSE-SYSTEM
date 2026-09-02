function createMessage() {
  return {
    message_id: `msg-emergency-${Date.now()}`,
    emergency_id: 'emergency-001',
    source_device_id: 'Device-A',
    current_device_id: 'Device-A',
    destination: 'BACKEND',
    payload: { message: 'SOS from Device A' },
    hop_count: 0,
    ttl: 3,
    created_at: new Date().toISOString(),
    status: 'SOS_CREATED',
  };
}

function relayMessage(message, device) {
  if (message.ttl <= 0) {
    return null;
  }

  return {
    ...message,
    current_device_id: device,
    hop_count: message.hop_count + 1,
    ttl: message.ttl - 1,
    status: 'RELAYED',
  };
}

export function runCommunicationSimulation() {
  const created = createMessage();
  const atB = relayMessage(created, 'Device-B');
  const duplicateDetected = Boolean(atB);
  const atC = atB && relayMessage(atB, 'Device-C');
  const delivered = atC
    ? { ...atC, current_device_id: 'Device-C', status: 'DELIVERED' }
    : null;

  return {
    message: delivered,
    steps: [
      { device: 'Device-A', action: 'SOS CREATED' },
      { device: 'Device-B', action: 'RELAYED' },
      { device: 'Device-C', action: 'RELAYED' },
      { device: 'BACKEND', action: 'DELIVERED' },
    ],
    relays: delivered?.hop_count || 0,
    duplicateDetected,
  };
}
