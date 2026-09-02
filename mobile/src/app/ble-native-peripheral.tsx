import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  DeviceEventEmitter,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  BLE_PERIPHERAL_CONFIG,
  checkBluetoothAvailabilityNative,
  hasPeripheralPermissions,
  startPeripheralAdvertising,
  stopPeripheralAdvertising,
} from '@/services/blePeripheralNative';
import { createEmergencyOnServer } from '@/services/api';
import {
  hasForwardedEmergencyId,
  markEmergencyIdForwarded,
} from '@/storage/emergencyRepository';

const forwardingEmergencyIds = new Set();

function validateSosPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return 'SOS payload must be a JSON object.';
  }

  const requiredFields = [
    'emergency_id',
    'message',
    'people_affected',
    'urgency',
    'latitude',
    'longitude',
  ];

  const missingField = requiredFields.find(
    (field) => !Object.prototype.hasOwnProperty.call(payload, field),
  );
  if (missingField) {
    return `Missing required SOS field: ${missingField}`;
  }

  if (typeof payload.emergency_id !== 'string' || !payload.emergency_id.trim()) {
    return 'SOS emergency_id must be a non-empty string.';
  }

  if (typeof payload.message !== 'string' || !payload.message.trim()) {
    return 'SOS message must be a non-empty string.';
  }

  if (!Number.isInteger(payload.people_affected) || payload.people_affected < 1) {
    return 'SOS people_affected must be a positive integer.';
  }

  const urgency = typeof payload.urgency === 'string'
    ? payload.urgency.toLowerCase()
    : payload.urgency;
  const validUrgency = ['low', 'medium', 'high', 'critical'].includes(urgency)
    || (Number.isInteger(urgency) && urgency >= 1 && urgency <= 5);
  if (!validUrgency) {
    return 'SOS urgency must be low, medium, high, critical, or an integer from 1 to 5.';
  }

  if (payload.latitude !== null && typeof payload.latitude !== 'number') {
    return 'SOS latitude must be a number or null.';
  }
  if (payload.longitude !== null && typeof payload.longitude !== 'number') {
    return 'SOS longitude must be a number or null.';
  }

  return '';
}

function normalizeUrgencyForApi(urgency) {
  if (typeof urgency === 'number') {
    return urgency;
  }

  return {
    low: 1,
    medium: 3,
    high: 4,
    critical: 5,
  }[urgency.toLowerCase()];
}

export default function BleNativePeripheralScreen() {
  const [status, setStatus] = useState('Idle');
  const [error, setError] = useState('');
  const [advertising, setAdvertising] = useState(false);
  const [receivedPayload, setReceivedPayload] = useState('');
  const [forwardingStatus, setForwardingStatus] = useState('');
  const payloadBufferRef = useRef('');

  const readablePayload = receivedPayload
    ? (() => {
        try {
          return JSON.stringify(JSON.parse(receivedPayload), null, 2);
        } catch {
          return receivedPayload;
        }
      })()
    : 'No payload received yet.';

  useEffect(() => {
    const forwardPayload = async (payload) => {
      const validationError = validateSosPayload(payload);
      if (validationError) {
        setForwardingStatus('Invalid SOS payload');
        setError(validationError);
        console.warn('BLE SOS payload validation failed:', validationError);
        return;
      }

      const emergencyId = payload.emergency_id;
      let alreadyForwarded = false;
      try {
        alreadyForwarded = hasForwardedEmergencyId(emergencyId);
      } catch (lookupError) {
        console.warn('BLE SOS persistent duplicate lookup failed; continuing:', lookupError);
      }

      if (forwardingEmergencyIds.has(emergencyId) || alreadyForwarded) {
        console.log('BLE SOS payload already forwarded:', emergencyId);
        setForwardingStatus('Already forwarded');
        return;
      }

      forwardingEmergencyIds.add(emergencyId);
      setForwardingStatus('Forwarding to backend');
      setError('');
      console.log('Forwarding complete BLE SOS payload:', emergencyId);

      try {
        await createEmergencyOnServer({
          message: payload.message,
          latitude: payload.latitude,
          longitude: payload.longitude,
          people_affected: payload.people_affected,
          injured: payload.injured,
          trapped: payload.trapped,
          fire: payload.fire,
          medical_emergency: payload.medical_emergency,
          urgency: normalizeUrgencyForApi(payload.urgency),
        });
        markEmergencyIdForwarded(emergencyId);
        forwardingEmergencyIds.delete(emergencyId);
        setForwardingStatus('Forwarded to backend');
        console.log('BLE SOS payload forwarded successfully:', emergencyId);
      } catch (forwardingError) {
        forwardingEmergencyIds.delete(emergencyId);
        setForwardingStatus('Backend forwarding failed');
        setError(forwardingError?.message || 'Unable to forward SOS to the backend.');
        console.warn('BLE SOS backend forwarding failed:', forwardingError);
      }
    };

    const writeSubscription = DeviceEventEmitter.addListener('BlePeripheralWrite', (event) => {
      const chunk = event?.payload || '';
      if (!chunk) {
        return;
      }

      payloadBufferRef.current += chunk;
      console.log(
        'BLE SOS chunk received:',
        chunk.length,
        'bytes; accumulated length:',
        payloadBufferRef.current.length,
      );

      try {
        const parsedPayload = JSON.parse(payloadBufferRef.current);
        const completePayload = JSON.stringify(parsedPayload);
        setReceivedPayload(completePayload);
        console.log('BLE SOS complete payload detected:', completePayload);
        payloadBufferRef.current = '';
        void forwardPayload(parsedPayload);
      } catch {
        // Wait for the next BLE write chunk to complete the JSON payload.
      }
    });

    return () => {
      writeSubscription.remove();
      stopPeripheralAdvertising().catch(() => undefined);
    };
  }, []);

  const handleStartAdvertising = async () => {
    try {
      setError('');
      const hasBluetooth = await checkBluetoothAvailabilityNative();
      if (!hasBluetooth) {
        setStatus('Bluetooth unavailable');
        setError('Bluetooth is disabled on Phone B.');
        return;
      }

      const hasPermissionsResult = await hasPeripheralPermissions();
      if (!hasPermissionsResult) {
        setStatus('Permissions required');
        setError('Android BLE permissions are required.');
        return;
      }

      setStatus('Starting advertising');
      const started = await startPeripheralAdvertising();
      if (started) {
        setAdvertising(true);
        setStatus('Advertising');
      } else {
        setStatus('Advertising failed');
        setError('Advertise start failed.');
      }
    } catch (err) {
      setStatus('Advertising failed');
      setError(err?.message || 'Unable to start advertising.');
    }
  };

  const handleStopAdvertising = async () => {
    try {
      const stopped = await stopPeripheralAdvertising();
      if (stopped) {
        setAdvertising(false);
        setStatus('Stopped');
      }
    } catch (err) {
      setError(err?.message || 'Unable to stop advertising.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Phone B BLE Peripheral</Text>
        <Text style={styles.subtitle}>Native Android advertiser + GATT server</Text>

        <View style={styles.card}>
          <Text style={styles.label}>Status</Text>
          <Text style={styles.status}>{status}</Text>
          {forwardingStatus ? <Text style={styles.forwardingStatus}>{forwardingStatus}</Text> : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Text style={styles.label}>Custom UUIDs</Text>
          <Text style={styles.uuidText}>Service: {BLE_PERIPHERAL_CONFIG.serviceUUID}</Text>
          <Text style={styles.uuidText}>Characteristic: {BLE_PERIPHERAL_CONFIG.characteristicUUID}</Text>

          <View style={styles.buttonRow}>
            <Pressable style={styles.primaryButton} onPress={handleStartAdvertising}>
              <Text style={styles.primaryButtonText}>{advertising ? 'Restart Advertising' : 'Start Advertising'}</Text>
            </Pressable>

            <Pressable style={styles.secondaryButton} onPress={handleStopAdvertising}>
              <Text style={styles.secondaryButtonText}>Stop Advertising</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Received SOS payload</Text>
          <View style={styles.payloadBox}>
            <Text selectable style={styles.payloadText}>{readablePayload}</Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Next step</Text>
          <Text style={styles.note}>Use Phone A to scan for this service UUID and connect to the device.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f4f7fb',
  },
  container: {
    padding: 20,
    paddingBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#102a43',
    textAlign: 'center',
    marginBottom: 4,
  },
  subtitle: {
    color: '#3d4d63',
    textAlign: 'center',
    marginBottom: 18,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 16,
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    color: '#3d4d63',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  status: {
    fontSize: 20,
    color: '#102a43',
    fontWeight: '700',
    marginBottom: 8,
  },
  error: {
    color: '#b91c1c',
    marginBottom: 8,
  },
  forwardingStatus: {
    color: '#0f766e',
    fontWeight: '700',
    marginBottom: 8,
  },
  uuidText: {
    color: '#475569',
    fontSize: 12,
    marginBottom: 4,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
    flexWrap: 'wrap',
  },
  primaryButton: {
    backgroundColor: '#0f766e',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    flex: 1,
    minWidth: 140,
    alignItems: 'center',
  },
  secondaryButton: {
    backgroundColor: '#374151',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    flex: 1,
    minWidth: 140,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontWeight: '700',
  },
  secondaryButtonText: {
    color: '#fff',
    fontWeight: '700',
  },
  note: {
    color: '#475569',
    lineHeight: 22,
  },
  payloadText: {
    color: '#102a43',
    fontFamily: 'monospace',
    fontSize: 14,
    lineHeight: 20,
  },
  payloadBox: {
    backgroundColor: '#e2e8f0',
    borderColor: '#94a3b8',
    borderRadius: 8,
    borderWidth: 1,
    padding: 12,
  },
});
