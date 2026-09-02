import { Platform } from 'react-native';
import * as SQLite from 'expo-sqlite';

let databaseInstance = null;

export function initializeDatabase() {
  if (Platform.OS === 'web') {
    return null;
  }

  if (databaseInstance) {
    return databaseInstance;
  }

  try {
    const database = SQLite.openDatabaseSync('disaster_response_local.db');
    database.execSync(`
      CREATE TABLE IF NOT EXISTS emergencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        local_id TEXT UNIQUE NOT NULL,
        message TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        people_affected INTEGER NOT NULL,
        injured INTEGER NOT NULL DEFAULT 0,
        trapped INTEGER NOT NULL DEFAULT 0,
        fire INTEGER NOT NULL DEFAULT 0,
        medical_emergency INTEGER NOT NULL DEFAULT 0,
        urgency INTEGER NOT NULL,
        priority_score INTEGER,
        priority_level TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING',
        sync_status TEXT NOT NULL DEFAULT 'PENDING',
        created_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS forwarded_emergencies (
        emergency_id TEXT PRIMARY KEY NOT NULL,
        forwarded_at TEXT NOT NULL
      );
    `);

    databaseInstance = database;
    return databaseInstance;
  } catch (error) {
    databaseInstance = null;
    console.warn('Failed to initialize local emergency database:', error);
    throw error;
  }
}

export function getDatabase() {
  if (Platform.OS === 'web') {
    return null;
  }

  if (!databaseInstance) {
    return initializeDatabase();
  }
  return databaseInstance;
}
