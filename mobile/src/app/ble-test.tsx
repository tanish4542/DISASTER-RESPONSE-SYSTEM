import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  BLE_CONFIG,
  checkAndRequestBluetoothPermissions,
  checkBluetoothEnabled,
  cleanupBleManager,
  connectToDevice,
  removeDeviceDisconnectedListener,
  startBleScan,
  stopBleScan,
  writeTestSosPayload,
} from '@/services/bleService';
import { getCurrentLocation } from '@/services/location';

const STATUS = {
  idle: 'Idle',
  unavailable: 'Bluetooth unavailable',
  permissionsRequired: 'Permissions required',
  scanning: 'Scanning',
  discovered: 'Device discovered',
  connecting: 'Connecting',
  connected: 'Connected',
  failed: 'Connection failed',
};

export default function BLETestScreen() {
  const [status, setStatus] = useState(STATUS.idle);
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [connectedDeviceId, setConnectedDeviceId] = useState('');
  const [connectedDevice, setConnectedDevice] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    return () => {
      stopBleScan();
      removeDeviceDisconnectedListener();
      cleanupBleManager();
    };
  }, []);

  const selectedDevice = useMemo(
    () => devices.find((device) => device.id === selectedDeviceId) || null,
    [devices, selectedDeviceId],
  );

  const ensureReady = async () => {
    const hasPermissions = await checkAndRequestBluetoothPermissions();
    if (!hasPermissions) {
      setStatus(STATUS.permissionsRequired);
      setErrorMessage('Bluetooth permissions are required to continue.');
      return false;
    }

    const bluetoothEnabled = await checkBluetoothEnabled();
    if (!bluetoothEnabled) {
      setStatus(STATUS.unavailable);
      setErrorMessage('Bluetooth is off on this device.');
      return false;
    }

    return true;
  };

  const handleStartScan = async () => {
    setErrorMessage('');
    const isReady = await ensureReady();
    if (!isReady) {
      return;
    }

    setDevices([]);
    setSelectedDeviceId('');
    setConnectedDeviceId('');
    setConnectedDevice(null);
    setStatus(STATUS.scanning);
    setIsScanning(true);

    try {
      await startBleScan((device) => {
        const normalizedName = device?.localName || device?.name || 'Unnamed device';
        const candidate = {
          id: device.id,
          name: normalizedName,
          rssi: device.rssi ?? 'n/a',
          serviceUUIDs: device.serviceUUIDs || [],
        };

        setDevices((current) => {
          const existing = current.find((entry) => entry.id === device.id);
          if (existing) {
            return current.map((entry) =>
              entry.id === device.id ? { ...entry, ...candidate } : entry,
            );
          }
          return [...current, candidate];
        });
      });
    } catch (error) {
      setStatus(STATUS.failed);
      setErrorMessage(error?.message || 'Unable to start BLE scan.');
    }
  };

  const handleStopScan = () => {
    stopBleScan();
    setIsScanning(false);
    setStatus(STATUS.idle);
  };

  const handleConnect = async () => {
    if (!selectedDeviceId) {
      setErrorMessage('Select a discovered device before connecting.');
      return;
    }

    setStatus(STATUS.connecting);
    setErrorMessage('');

    try {
      const device = await connectToDevice(selectedDeviceId);
      setConnectedDevice(device);
      setConnectedDeviceId(selectedDeviceId);
      setStatus(STATUS.connected);
      Alert.alert('Connected', `Connected to ${selectedDevice?.name || 'device'}`);
    } catch (error) {
      setStatus(STATUS.failed);
      setErrorMessage(error?.message || 'Unable to connect to the selected device.');
    }
  };

  const handleSendTestSos = async () => {
    if (!connectedDevice || !connectedDeviceId) {
      return;
    }

    setIsSending(true);
    setErrorMessage('');

    try {
      let deviceForWrite;
      try {
        deviceForWrite = await connectedDevice.requestMTU(158);
        console.log('BLE negotiated MTU before SOS write:', deviceForWrite?.mtu);
      } catch (error) {
        console.warn('BLE SOS MTU request failed:', error);
        throw new Error(
          `Unable to negotiate BLE MTU before sending test SOS: ${error?.message || 'unknown error'}`,
        );
      }

      let location = null;
      try {
        location = await getCurrentLocation();
      } catch (error) {
        console.warn('BLE SOS GPS lookup failed:', error);
      }

      const gpsUnavailableMessage = location
        ? ''
        : 'GPS unavailable; sending test SOS without coordinates.';
      if (gpsUnavailableMessage) {
        console.warn(gpsUnavailableMessage);
        setErrorMessage(gpsUnavailableMessage);
      }

      await writeTestSosPayload(connectedDevice, {
        emergency_id: 'test-emergency-001',
        message: 'Test SOS from Phone A',
        people_affected: 1,
        urgency: 'high',
        latitude: location?.latitude ?? null,
        longitude: location?.longitude ?? null,
      });
      Alert.alert(
        'SOS sent',
        gpsUnavailableMessage
          ? 'Test SOS payload sent to Phone B without GPS coordinates.'
          : 'Test SOS payload sent to Phone B with current GPS coordinates.',
      );
    } catch (error) {
      setErrorMessage(error?.message || 'Unable to send the test SOS payload.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Android BLE Test</Text>
        <Text style={styles.subtitle}>A → B discovery and connection prototype</Text>

        <View style={styles.card}>
          <Text style={styles.label}>Status</Text>
          <Text style={styles.statusText}>{status}</Text>
          {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

          <Text style={styles.label}>UUID config</Text>
          <Text style={styles.uuidText}>Service: {BLE_CONFIG.serviceUUID}</Text>
          <Text style={styles.uuidText}>Characteristic: {BLE_CONFIG.characteristicUUID}</Text>

          <View style={styles.buttonRow}>
            <Pressable style={styles.primaryButton} onPress={handleStartScan}>
              <Text style={styles.primaryButtonText}>{isScanning ? 'Scan Again' : 'Start Scan'}</Text>
            </Pressable>

            {isScanning ? (
              <Pressable style={styles.secondaryButton} onPress={handleStopScan}>
                <Text style={styles.secondaryButtonText}>Stop Scan</Text>
              </Pressable>
            ) : null}
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Discovered devices</Text>
          {devices.length === 0 ? (
            <Text style={styles.emptyText}>No devices discovered yet.</Text>
          ) : null}

          {devices.map((device) => {
            const isSelected = device.id === selectedDeviceId;
            const isConnected = device.id === connectedDeviceId;

            return (
              <Pressable
                key={device.id}
                onPress={() => setSelectedDeviceId(device.id)}
                style={[styles.deviceRow, isSelected && styles.deviceRowSelected]}
              >
                <Text style={styles.deviceName}>{device.name}</Text>
                <Text style={styles.deviceMeta}>ID: {device.id}</Text>
                <Text style={styles.deviceMeta}>RSSI: {device.rssi}</Text>
                {isConnected ? <Text style={styles.connectedTag}>Connected</Text> : null}
              </Pressable>
            );
          })}
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Selected device</Text>
          {selectedDevice ? (
            <>
              <Text style={styles.deviceName}>{selectedDevice.name}</Text>
              <Text style={styles.deviceMeta}>ID: {selectedDevice.id}</Text>
              <Text style={styles.deviceMeta}>Service UUIDs: {selectedDevice.serviceUUIDs.join(', ') || 'none'}</Text>
            </>
          ) : (
            <Text style={styles.emptyText}>No device selected.</Text>
          )}

          <Pressable
            style={[styles.primaryButton, !selectedDevice && styles.buttonDisabled]}
            onPress={handleConnect}
            disabled={!selectedDevice}
          >
            <Text style={styles.primaryButtonText}>Connect</Text>
          </Pressable>

          <Pressable
            style={[styles.secondaryButton, !connectedDeviceId && styles.buttonDisabled]}
            onPress={handleSendTestSos}
            disabled={!connectedDeviceId || isSending}
          >
            <Text style={styles.secondaryButtonText}>
              {isSending ? 'Sending...' : 'SEND TEST SOS'}
            </Text>
          </Pressable>
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
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 3 },
  },
  label: {
    fontSize: 13,
    fontWeight: '700',
    color: '#3d4d63',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statusText: {
    color: '#102a43',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  uuidText: {
    color: '#3d4d63',
    fontSize: 12,
    marginBottom: 4,
  },
  errorText: {
    color: '#b91c1c',
    marginBottom: 10,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
    flexWrap: 'wrap',
  },
  primaryButton: {
    backgroundColor: '#1d4ed8',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
    flex: 1,
    minWidth: 120,
    alignItems: 'center',
  },
  secondaryButton: {
    backgroundColor: '#374151',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
    flex: 1,
    minWidth: 120,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  primaryButtonText: {
    color: '#fff',
    fontWeight: '700',
  },
  secondaryButtonText: {
    color: '#fff',
    fontWeight: '700',
  },
  emptyText: {
    color: '#64748b',
    marginBottom: 10,
  },
  deviceRow: {
    borderWidth: 1,
    borderColor: '#dbeafe',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    backgroundColor: '#f8fbff',
  },
  deviceRowSelected: {
    borderColor: '#1d4ed8',
    backgroundColor: '#eff6ff',
  },
  deviceName: {
    color: '#102a43',
    fontWeight: '700',
    fontSize: 16,
  },
  deviceMeta: {
    color: '#475569',
    fontSize: 12,
    marginTop: 2,
  },
  connectedTag: {
    marginTop: 8,
    color: '#15803d',
    fontWeight: '700',
  },
});
