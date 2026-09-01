import { v4 as uuidv4 } from 'uuid';

import { getDatabase } from './database';

export async function initializeEmergencyDatabase() {
  try {
    getDatabase();
    return true;
  } catch (error) {
    console.warn('Emergency database initialization failed:', error);
    return false;
  }
}

export function createEmergency(emergency) {
  const db = getDatabase();
  const localId = emergency.local_id || uuidv4();
  const createdAt = emergency.created_at || new Date().toISOString();
  const record = {
    local_id: localId,
    message: emergency.message,
    latitude: emergency.latitude ?? null,
    longitude: emergency.longitude ?? null,
    people_affected: emergency.people_affected,
    injured: emergency.injured ? 1 : 0,
    trapped: emergency.trapped ? 1 : 0,
    fire: emergency.fire ? 1 : 0,
    medical_emergency: emergency.medical_emergency ? 1 : 0,
    urgency: emergency.urgency,
    priority_score: emergency.priority_score ?? null,
    priority_level: emergency.priority_level ?? null,
    status: emergency.status || 'PENDING',
    sync_status: emergency.sync_status || 'PENDING',
    created_at: createdAt,
  };

  if (!db) {
    return {
      ...record,
      id: null,
      savedLocally: false,
    };
  }

  const result = db.runSync(
    `INSERT INTO emergencies (
      local_id,
      message,
      latitude,
      longitude,
      people_affected,
      injured,
      trapped,
      fire,
      medical_emergency,
      urgency,
      priority_score,
      priority_level,
      status,
      sync_status,
      created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);`,
    [
      record.local_id,
      record.message,
      record.latitude,
      record.longitude,
      record.people_affected,
      record.injured,
      record.trapped,
      record.fire,
      record.medical_emergency,
      record.urgency,
      record.priority_score,
      record.priority_level,
      record.status,
      record.sync_status,
      record.created_at,
    ],
  );

  return getEmergencyByLocalId(localId) || { ...record, id: result.lastInsertRowId, savedLocally: true };
}

export function getAllEmergencies() {
  const db = getDatabase();
  if (!db) {
    return [];
  }

  const rows = db.getAllSync(
    `SELECT * FROM emergencies ORDER BY created_at DESC;`,
  );

  return rows.map((row) => ({
    ...row,
    injured: Boolean(row.injured),
    trapped: Boolean(row.trapped),
    fire: Boolean(row.fire),
    medical_emergency: Boolean(row.medical_emergency),
  }));
}

export function getPendingEmergencies() {
  const db = getDatabase();
  if (!db) {
    return [];
  }

  const rows = db.getAllSync(
    `SELECT * FROM emergencies WHERE sync_status = ? ORDER BY created_at ASC;`,
    ['PENDING'],
  );

  return rows.map((row) => ({
    ...row,
    injured: Boolean(row.injured),
    trapped: Boolean(row.trapped),
    fire: Boolean(row.fire),
    medical_emergency: Boolean(row.medical_emergency),
  }));
}

export function getEmergencyByLocalId(localId) {
  const db = getDatabase();
  if (!db) {
    return null;
  }

  const row = db.getFirstSync(
    `SELECT * FROM emergencies WHERE local_id = ?;`,
    [localId],
  );

  if (!row) {
    return null;
  }

  return {
    ...row,
    injured: Boolean(row.injured),
    trapped: Boolean(row.trapped),
    fire: Boolean(row.fire),
    medical_emergency: Boolean(row.medical_emergency),
  };
}

export function updateEmergencySyncStatus(localId, syncStatus) {
  const db = getDatabase();
  if (!db) {
    return null;
  }

  db.runSync(`UPDATE emergencies SET sync_status = ? WHERE local_id = ?;`, [
    syncStatus,
    localId,
  ]);
  return getEmergencyByLocalId(localId);
}

export function deleteEmergency(localId) {
  const db = getDatabase();
  if (!db) {
    return false;
  }

  db.runSync(`DELETE FROM emergencies WHERE local_id = ?;`, [localId]);
  return true;
}
