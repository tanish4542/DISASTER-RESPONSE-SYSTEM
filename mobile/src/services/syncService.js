import { createEmergencyOnServer } from './api';
import {
  getPendingEmergencies,
  updateEmergencySyncStatus,
} from '@/storage/emergencyRepository';

export async function syncEmergency(emergency) {
  await createEmergencyOnServer(emergency);
  updateEmergencySyncStatus(emergency.local_id, 'SYNCED');
  return true;
}

export async function syncPendingEmergencies() {
  const pendingEmergencies = getPendingEmergencies();
  const syncedLocalIds = [];

  for (const emergency of pendingEmergencies) {
    try {
      await createEmergencyOnServer(emergency);
      updateEmergencySyncStatus(emergency.local_id, 'SYNCED');
      syncedLocalIds.push(emergency.local_id);
    } catch (error) {
      // Keep failed records pending for a later retry.
    }
  }

  return syncedLocalIds;
}
