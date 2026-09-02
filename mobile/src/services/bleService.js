import { BleManager } from 'react-native-ble-plx';
import { PermissionsAndroid, Platform } from 'react-native';
import { getPendingEmergencies } from '@/storage/emergencyRepository';

export const BLE_CONFIG = {
  serviceUUID: '0000FFE0-0000-1000-8000-00805F9B34FB',
  characteristicUUID: '0000FFE1-0000-1000-8000-00805F9B34FB',
  scanOptions: {
    allowDuplicates: false,
  },
};

let manager = new BleManager();
let connectedDevice = null;
let foregroundBleActive = false;
let foregroundScanInProgress = false;
let foregroundConnectionInProgress = false;
let foregroundReconnectTimer = null;
const emergencyTransmissions = new Map();
const BASE64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function encodeBase64(value) {
  let encoded = '';

  for (let index = 0; index < value.length; index += 3) {
    const first = value.charCodeAt(index);
    const second = value.charCodeAt(index + 1);
    const third = value.charCodeAt(index + 2);
    const hasSecond = index + 1 < value.length;
    const hasThird = index + 2 < value.length;

    encoded += BASE64_CHARS[first >> 2];
    encoded += BASE64_CHARS[((first & 3) << 4) | (hasSecond ? second >> 4 : 0)];
    encoded += hasSecond ? BASE64_CHARS[((second & 15) << 2) | (hasThird ? third >> 6 : 0)] : '=';
    encoded += hasThird ? BASE64_CHARS[third & 63] : '=';
  }

  return encoded;
}

const ANDROID_BLE_PERMISSIONS = [
  PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
  PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
  PermissionsAndroid.PERMISSIONS.BLUETOOTH_ADVERTISE,
  PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
];

function getBleManager() {
  if (!manager) {
    manager = new BleManager();
  }
  return manager;
}

export async function checkBluetoothEnabled() {
  if (Platform.OS !== 'android') {
    return true;
  }

  try {
    const state = await getBleManager().state();
    return state === 'PoweredOn';
  } catch (error) {
    console.warn('BLE enable check failed:', error);
    return false;
  }
}

export async function checkAndRequestBluetoothPermissions() {
  if (Platform.OS !== 'android') {
    return true;
  }

  const grantedResults = await PermissionsAndroid.requestMultiple(ANDROID_BLE_PERMISSIONS);
  const hasAllPermissions = Object.values(grantedResults).every(
    (status) => status === PermissionsAndroid.RESULTS.GRANTED,
  );

  if (!hasAllPermissions) {
    const denied = Object.entries(grantedResults)
      .filter(([, status]) => status !== PermissionsAndroid.RESULTS.GRANTED)
      .map(([permission]) => permission);
    console.warn('Missing BLE Android permissions:', denied);
    return false;
  }

  return true;
}

export async function startBleScan(onDeviceDiscovered) {
  if (Platform.OS !== 'android') {
    return false;
  }

  const hasPermissions = await checkAndRequestBluetoothPermissions();
  if (!hasPermissions) {
    return false;
  }

  const bluetoothEnabled = await checkBluetoothEnabled();
  if (!bluetoothEnabled) {
    return false;
  }

  await getBleManager().startDeviceScan([BLE_CONFIG.serviceUUID], BLE_CONFIG.scanOptions, (error, device) => {
    if (error) {
      console.warn('BLE scan error:', error);
      return;
    }

    if (device && typeof onDeviceDiscovered === 'function') {
      onDeviceDiscovered(device);
    }
  });

  return true;
}

export function stopBleScan() {
  if (Platform.OS !== 'android') {
    return;
  }

  getBleManager().stopDeviceScan();
}

export async function connectToDevice(deviceId, options = {}) {
  if (!deviceId) {
    throw new Error('Device ID is required to connect.');
  }

  const hasPermissions = await checkAndRequestBluetoothPermissions();
  if (!hasPermissions) {
    throw new Error('Bluetooth permissions were not granted.');
  }

  const bluetoothEnabled = await checkBluetoothEnabled();
  if (!bluetoothEnabled) {
    throw new Error('Bluetooth is disabled.');
  }

  const device = await getBleManager().connectToDevice(deviceId, {
    autoConnect: false,
  });

  const discoveredDevice = await device.discoverAllServicesAndCharacteristics();
  connectedDevice = discoveredDevice;
  discoveredDevice.onDisconnected(() => {
    if (connectedDevice === discoveredDevice) {
      connectedDevice = null;
    }
    options.onDisconnected?.();
  });
  return connectedDevice;
}

export function getConnectedDevice() {
  return connectedDevice;
}

function buildEmergencySosPayload(emergency) {
  return {
    emergency_id: emergency.local_id,
    message: emergency.message,
    people_affected: emergency.people_affected,
    injured: Boolean(emergency.injured),
    trapped: Boolean(emergency.trapped),
    fire: Boolean(emergency.fire),
    medical_emergency: Boolean(emergency.medical_emergency),
    urgency: emergency.urgency,
    latitude: emergency.latitude ?? null,
    longitude: emergency.longitude ?? null,
  };
}

export async function sendEmergencyToRelay(emergency, device = getConnectedDevice()) {
  const emergencyId = emergency?.local_id;
  if (!emergencyId) {
    return false;
  }
  if (emergencyTransmissions.has(emergencyId)) {
    return emergencyTransmissions.get(emergencyId);
  }

  const transmission = (async () => {
    try {
      const deviceForWrite = typeof device.requestMTU === 'function'
        ? await device.requestMTU(158)
        : device;
      await writeTestSosPayload(deviceForWrite, buildEmergencySosPayload(emergency));
      return true;
    } finally {
      emergencyTransmissions.delete(emergencyId);
    }
  })();
  emergencyTransmissions.set(emergencyId, transmission);
  return transmission;
}

async function syncPendingEmergenciesToRelay() {
  const pendingEmergencies = getPendingEmergencies();

  for (const emergency of pendingEmergencies) {
    if (!foregroundBleActive || !connectedDevice) {
      return;
    }

    try {
      await sendEmergencyToRelay(emergency);
    } catch (error) {
      console.warn('Pending SOS relay transmission failed:', error);
    }
  }
}

function scheduleForegroundBleScan() {
  if (!foregroundBleActive || foregroundReconnectTimer) {
    return;
  }

  foregroundReconnectTimer = setTimeout(() => {
    foregroundReconnectTimer = null;
    void scanForForegroundRelay();
  }, 1000);
}

async function scanForForegroundRelay() {
  if (!foregroundBleActive || connectedDevice || foregroundScanInProgress || foregroundConnectionInProgress) {
    return;
  }

  foregroundScanInProgress = true;
  try {
    const scanStarted = await startBleScan((device) => {
      if (!foregroundBleActive || connectedDevice || foregroundConnectionInProgress) {
        return;
      }

      foregroundConnectionInProgress = true;
      stopBleScan();
      void connectToDevice(device.id, {
        onDisconnected: () => {
          scheduleForegroundBleScan();
        },
      })
        .then(() => syncPendingEmergenciesToRelay())
        .catch((error) => {
          console.warn('Automatic BLE relay connection failed:', error);
          scheduleForegroundBleScan();
        })
        .finally(() => {
          foregroundConnectionInProgress = false;
          if (!connectedDevice) {
            scheduleForegroundBleScan();
          }
        });
    });
    if (!scanStarted) {
      scheduleForegroundBleScan();
    }
  } catch (error) {
    console.warn('Automatic BLE relay scan failed:', error);
    scheduleForegroundBleScan();
  } finally {
    foregroundScanInProgress = false;
  }
}

export function startForegroundBle() {
  if (Platform.OS !== 'android' || foregroundBleActive) {
    return;
  }

  foregroundBleActive = true;
  void scanForForegroundRelay();
}

export function stopForegroundBle() {
  foregroundBleActive = false;
  stopBleScan();
  if (foregroundReconnectTimer) {
    clearTimeout(foregroundReconnectTimer);
    foregroundReconnectTimer = null;
  }
}

export async function resetBleManager() {
  const managerToReset = manager;
  const deviceToDisconnect = connectedDevice;
  connectedDevice = null;

  try {
    managerToReset?.stopDeviceScan();
    if (deviceToDisconnect) {
      await deviceToDisconnect.cancelConnection();
    }
  } catch (error) {
    console.warn('BLE connection reset failed:', error);
  } finally {
    manager = null;
    managerToReset?.destroy();
  }
}

export async function writeTestSosPayload(device, payload) {
  if (!device) {
    throw new Error('A connected BLE device is required.');
  }

  const payloadJson = JSON.stringify(payload);
  const payloadBase64 = encodeBase64(payloadJson);

  if (typeof device.writeCharacteristicWithResponseForService !== 'function') {
    throw new Error('Connected BLE device does not support characteristic writes.');
  }

  try {
    return await device.writeCharacteristicWithResponseForService(
      BLE_CONFIG.serviceUUID,
      BLE_CONFIG.characteristicUUID,
      payloadBase64,
    );
  } catch (error) {
    console.warn('BLE SOS payload write failed:', error);
    throw error;
  }
}

export function removeDeviceDisconnectedListener(listener) {
  if (listener && typeof listener.remove === 'function') {
    listener.remove();
  }
}

export function cleanupBleManager() {
  try {
    stopBleScan();
  } catch (error) {
    console.warn('BLE cleanup failed:', error);
  }
}
