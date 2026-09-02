import { NativeModules, Platform } from 'react-native';

const { BlePeripheral } = NativeModules;

export const BLE_PERIPHERAL_CONFIG = {
  serviceUUID: '0000FFE0-0000-1000-8000-00805F9B34FB',
  characteristicUUID: '0000FFE1-0000-1000-8000-00805F9B34FB',
};

export async function checkBluetoothAvailabilityNative() {
  if (Platform.OS !== 'android') {
    return true;
  }

  try {
    return Boolean(await BlePeripheral?.checkBluetoothAvailability?.());
  } catch (error) {
    console.warn('Bluetooth availability check failed:', error);
    return false;
  }
}

export async function hasPeripheralPermissions() {
  if (Platform.OS !== 'android') {
    return true;
  }

  try {
    return Boolean(await BlePeripheral?.hasRequiredPermissions?.());
  } catch (error) {
    console.warn('Permission check failed:', error);
    return false;
  }
}

export async function startPeripheralAdvertising() {
  if (Platform.OS !== 'android') {
    return false;
  }

  try {
    return Boolean(
      await BlePeripheral?.startAdvertising?.(
        BLE_PERIPHERAL_CONFIG.serviceUUID,
        BLE_PERIPHERAL_CONFIG.characteristicUUID,
      ),
    );
  } catch (error) {
    console.warn('Advertising failed:', error);
    return false;
  }
}

export async function stopPeripheralAdvertising() {
  if (Platform.OS !== 'android') {
    return true;
  }

  try {
    return Boolean(await BlePeripheral?.stopAdvertising?.());
  } catch (error) {
    console.warn('Stop advertising failed:', error);
    return false;
  }
}
