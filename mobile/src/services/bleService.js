import { BleManager } from 'react-native-ble-plx';
import { PermissionsAndroid, Platform } from 'react-native';

export const BLE_CONFIG = {
  serviceUUID: '0000FFE0-0000-1000-8000-00805F9B34FB',
  characteristicUUID: '0000FFE1-0000-1000-8000-00805F9B34FB',
  scanOptions: {
    allowDuplicates: false,
  },
};

let manager = new BleManager();
let connectedDevice = null;
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

export async function connectToDevice(deviceId) {
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
  });
  return connectedDevice;
}

export function getConnectedDevice() {
  return connectedDevice;
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
