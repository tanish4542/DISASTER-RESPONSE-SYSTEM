import { useState } from 'react';
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import { createEmergency } from '@/storage/emergencyRepository';
import { syncEmergency, syncPendingEmergencies } from '@/services/syncService';
import { getCurrentLocation } from '@/services/location';
import { APP_COLORS, APP_RADII, APP_SPACING } from '@/constants/appTheme';
import { getConnectedDevice, writeTestSosPayload } from '@/services/bleService';

const initialFormState = {
  message: '',
  people_affected: '1',
  injured: false,
  trapped: false,
  fire: false,
  medical_emergency: false,
  urgency: '3',
};

export default function SOSScreen() {
  const [form, setForm] = useState(initialFormState);
  const [error, setError] = useState('');
  const [savedEmergency, setSavedEmergency] = useState(null);
  const [locationStatus, setLocationStatus] = useState('Location will be requested before saving.');
  const [relayStatus, setRelayStatus] = useState('');

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const validateForm = () => {
    if (!form.message || form.message.trim().length < 5) {
      return 'Emergency description must be at least 5 characters.';
    }

    const peopleAffected = Number(form.people_affected);
    if (!Number.isInteger(peopleAffected) || peopleAffected < 1) {
      return 'People affected must be a whole number of at least 1.';
    }

    const urgency = Number(form.urgency);
    if (!Number.isInteger(urgency) || urgency < 1 || urgency > 5) {
      return 'Urgency must be between 1 and 5.';
    }

    return '';
  };

  const handleSubmit = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      setSavedEmergency(null);
      return;
    }

    setLocationStatus('📍 Getting location...');
    let location = null;
    try {
      location = await getCurrentLocation();
    } catch (locationError) {
      location = null;
    }

    if (location) {
      setLocationStatus('📍 Location captured');
    } else {
      setLocationStatus('⚠️ Location unavailable');
    }

    const emergencyPayload = {
      local_id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `local-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      message: form.message.trim(),
      latitude: location?.latitude ?? null,
      longitude: location?.longitude ?? null,
      people_affected: Number(form.people_affected),
      injured: Boolean(form.injured),
      trapped: Boolean(form.trapped),
      fire: Boolean(form.fire),
      medical_emergency: Boolean(form.medical_emergency),
      urgency: Number(form.urgency),
      status: 'PENDING',
      sync_status: 'PENDING',
      priority_score: null,
      priority_level: null,
    };

    try {
      const saved = createEmergency(emergencyPayload);
      const localId = saved?.local_id || emergencyPayload.local_id;
      setSavedEmergency({ ...saved, local_id: localId, sync_status: 'PENDING' });
      setError('');
      setForm(initialFormState);

      const connectedDevice = getConnectedDevice();
      let relaySent = false;
      if (!connectedDevice) {
        setRelayStatus('Saved locally; no nearby relay is connected.');
      } else {
        try {
          const deviceForWrite = await connectedDevice.requestMTU(158);
          await writeTestSosPayload(deviceForWrite, {
            emergency_id: localId,
            message: emergencyPayload.message,
            people_affected: emergencyPayload.people_affected,
            injured: emergencyPayload.injured,
            trapped: emergencyPayload.trapped,
            fire: emergencyPayload.fire,
            medical_emergency: emergencyPayload.medical_emergency,
            urgency: emergencyPayload.urgency,
            latitude: emergencyPayload.latitude,
            longitude: emergencyPayload.longitude,
          });
          relaySent = true;
          setRelayStatus('SOS sent to nearby relay.');
        } catch (relayError) {
          console.warn('SOS relay transmission failed:', relayError);
          setRelayStatus('Saved locally; relay transmission failed.');
        }
      }

      let synced = false;
      if (!relaySent) {
        try {
          synced = await syncEmergency(emergencyPayload);
        } catch (syncError) {
          setError(`Synchronization failed: ${syncError.message}`);
          synced = false;
        }
      }

      if (relaySent) {
        Alert.alert('SOS SENT TO RELAY', 'Your emergency was saved locally and sent to a nearby relay.');
      } else if (synced) {
        setSavedEmergency((current) => ({ ...current, sync_status: 'SYNCED' }));
        Alert.alert('SOS SENT', 'Your emergency was saved and sent to the rescue server.');
      } else {
        Alert.alert(
          'SOS SAVED OFFLINE',
          'Your emergency is safely stored on this device and will be sent when connectivity is available.',
        );
      }
    } catch (submitError) {
      console.error('SOS submission failed:', submitError, submitError?.message);
      setError('Could not save the SOS locally. Please try again.');
      setSavedEmergency(null);
    }
  };

  const handleSyncPending = async () => {
    const syncedLocalIds = await syncPendingEmergencies();
    if (syncedLocalIds.length > 0) {
      Alert.alert('SOS SENT', `${syncedLocalIds.length} pending SOS sent to the rescue server.`);
    } else {
      Alert.alert('NO SOS SENT', 'No pending SOS could be synchronized right now.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Emergency SOS</Text>
        <Text style={styles.locationStatus}>{locationStatus}</Text>
        {relayStatus ? <Text style={styles.relayStatus}>{relayStatus}</Text> : null}

        <View style={styles.formCard}>
          <Text style={styles.label}>Emergency description</Text>
          <TextInput
            style={styles.input}
            value={form.message}
            onChangeText={(value) => updateField('message', value)}
            placeholder="Describe the emergency"
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />

          <Text style={styles.label}>People affected</Text>
          <TextInput
            style={styles.input}
            value={form.people_affected}
            onChangeText={(value) => updateField('people_affected', value.replace(/[^0-9]/g, ''))}
            keyboardType="number-pad"
            placeholder="1"
          />

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Injured</Text>
            <Switch value={form.injured} onValueChange={(value) => updateField('injured', value)} />
          </View>

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Trapped</Text>
            <Switch value={form.trapped} onValueChange={(value) => updateField('trapped', value)} />
          </View>

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Fire</Text>
            <Switch value={form.fire} onValueChange={(value) => updateField('fire', value)} />
          </View>

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Medical emergency</Text>
            <Switch value={form.medical_emergency} onValueChange={(value) => updateField('medical_emergency', value)} />
          </View>

          <Text style={styles.label}>Urgency (1-5)</Text>
          <TextInput
            style={styles.input}
            value={form.urgency}
            onChangeText={(value) => updateField('urgency', value.replace(/[^1-5]/g, '').slice(0, 1))}
            keyboardType="number-pad"
            placeholder="3"
          />

          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          <Pressable style={styles.button} onPress={handleSubmit}>
            <Text style={styles.buttonText}>SAVE SOS</Text>
          </Pressable>

          <Pressable style={styles.secondaryButton} onPress={handleSyncPending}>
            <Text style={styles.secondaryButtonText}>SYNC PENDING SOS</Text>
          </Pressable>

          {savedEmergency ? (
            <View style={styles.successBox}>
              <Text style={styles.successTitle}>
                {relayStatus === 'Relayed to nearby rescue device'
                  ? '🚨 RELAYED TO NEARBY RESCUE DEVICE'
                  : savedEmergency.sync_status === 'SYNCED'
                    ? '🚨 SOS SENT'
                    : '🚨 SOS SAVED OFFLINE'}
              </Text>
              <Text style={styles.successText}>Local ID: {savedEmergency.local_id}</Text>
              <Text style={styles.successText}>Status: {savedEmergency.status}</Text>
              {relayStatus !== 'Relayed to nearby rescue device' ? (
                <Text style={styles.successText}>Sync status: {savedEmergency.sync_status}</Text>
              ) : null}
              {savedEmergency.latitude !== null && savedEmergency.longitude !== null ? (
                <Text style={styles.successText}>
                  Coordinates: {savedEmergency.latitude}, {savedEmergency.longitude}
                </Text>
              ) : null}
            </View>
          ) : null}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: APP_COLORS.background,
  },
  container: {
    padding: APP_SPACING.lg,
    paddingBottom: 44,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: APP_COLORS.text,
    marginBottom: APP_SPACING.sm,
  },
  locationStatus: {
    color: APP_COLORS.muted,
    marginBottom: APP_SPACING.md,
  },
  relayStatus: {
    color: APP_COLORS.accent,
    fontWeight: '700',
    marginBottom: APP_SPACING.md,
  },
  formCard: {
    backgroundColor: APP_COLORS.surface,
    borderColor: APP_COLORS.border,
    borderRadius: APP_RADII.lg,
    borderWidth: 1,
    padding: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: APP_COLORS.text,
    marginBottom: 8,
    marginTop: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: APP_COLORS.border,
    borderRadius: APP_RADII.sm,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: APP_COLORS.surfaceRaised,
    color: APP_COLORS.text,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginVertical: 8,
  },
  rowLabel: {
    fontSize: 15,
    color: APP_COLORS.text,
  },
  errorText: {
    color: '#ff8b8f',
    fontSize: 14,
    marginTop: 4,
    marginBottom: 12,
  },
  button: {
    backgroundColor: APP_COLORS.danger,
    borderRadius: APP_RADII.sm,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    borderColor: APP_COLORS.danger,
    borderWidth: 1,
    borderRadius: APP_RADII.sm,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  secondaryButtonText: {
    color: '#ff8589',
    fontSize: 14,
    fontWeight: '700',
  },
  successBox: {
    marginTop: 18,
    backgroundColor: '#123524',
    borderColor: '#286844',
    borderWidth: 1,
    borderRadius: APP_RADII.sm,
    padding: 12,
  },
  successTitle: {
    color: APP_COLORS.success,
    fontWeight: '700',
    marginBottom: 4,
  },
  successText: {
    color: '#b9f1cb',
  },
});
