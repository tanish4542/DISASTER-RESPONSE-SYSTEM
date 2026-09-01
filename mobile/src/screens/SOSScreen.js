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
import { syncPendingEmergencies } from '@/services/syncService';
import { getCurrentLocation } from '@/services/location';

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

      let synced = false;
      try {
        const syncedLocalIds = await syncPendingEmergencies();
        synced = syncedLocalIds.includes(localId);
      } catch (syncError) {
        synced = false;
      }

      if (synced) {
        setSavedEmergency((current) => ({ ...current, sync_status: 'SYNCED' }));
        Alert.alert('SOS SENT', 'Your emergency was saved and sent to the rescue server.');
      } else {
        Alert.alert(
          'SOS SAVED OFFLINE',
          'Your emergency is safely stored on this device and will be sent when connectivity is available.',
        );
      }
    } catch (submitError) {
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
                {savedEmergency.sync_status === 'SYNCED' ? '🚨 SOS SENT' : '🚨 SOS SAVED OFFLINE'}
              </Text>
              <Text style={styles.successText}>Local ID: {savedEmergency.local_id}</Text>
              <Text style={styles.successText}>Status: {savedEmergency.status}</Text>
              <Text style={styles.successText}>Sync status: {savedEmergency.sync_status}</Text>
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
    backgroundColor: '#f4f7fb',
  },
  container: {
    padding: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#102a43',
    marginBottom: 16,
    textAlign: 'center',
  },
  locationStatus: {
    color: '#3d4d63',
    textAlign: 'center',
    marginBottom: 14,
  },
  formCard: {
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#102a43',
    marginBottom: 8,
    marginTop: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d9e2ec',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#f8fafc',
    color: '#102a43',
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
    color: '#102a43',
  },
  errorText: {
    color: '#b42318',
    fontSize: 14,
    marginTop: 4,
    marginBottom: 12,
  },
  button: {
    backgroundColor: '#d62828',
    borderRadius: 12,
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
    borderColor: '#d62828',
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  secondaryButtonText: {
    color: '#d62828',
    fontSize: 14,
    fontWeight: '700',
  },
  successBox: {
    marginTop: 18,
    backgroundColor: '#ecfdf3',
    borderColor: '#a7f3d0',
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
  },
  successTitle: {
    color: '#065f46',
    fontWeight: '700',
    marginBottom: 4,
  },
  successText: {
    color: '#065f46',
  },
});
