import { useEffect, useState } from 'react';
import { Link } from 'expo-router';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

import { APP_COLORS, APP_RADII, APP_SPACING } from '@/constants/appTheme';
import { BLE_CONFIG, checkBluetoothEnabled } from '@/services/bleService';

export default function NetworkScreen() {
  const [bluetoothReady, setBluetoothReady] = useState(null);
  useEffect(() => { checkBluetoothEnabled().then(setBluetoothReady).catch(() => setBluetoothReady(false)); }, []);
  const statusText = bluetoothReady === null ? 'Checking device radio' : bluetoothReady ? 'Bluetooth is ready for nearby links' : 'Bluetooth is currently unavailable';
  return (
    <SafeAreaView style={styles.safeArea}><ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>COMMUNICATIONS</Text><Text style={styles.title}>Network readiness</Text>
      <Text style={styles.subtitle}>See whether this device can participate in the nearby communication layer.</Text>
      <View style={styles.statusCard}><View style={[styles.statusDot, bluetoothReady ? styles.statusGood : styles.statusWaiting]} /><View style={styles.statusCopy}><Text style={styles.cardLabel}>LOCAL RADIO</Text><Text style={styles.statusTitle}>{statusText}</Text><Text style={styles.statusDetail}>BLE service discovery is used for nearby relay connections.</Text></View></View>
      <View style={styles.card}><Text style={styles.cardLabel}>CONFIGURED SERVICE</Text><Text style={styles.uuid}>{BLE_CONFIG.serviceUUID}</Text><Text style={styles.note}>Nearby capability is checked from the existing Bluetooth service. No relay is active from this screen.</Text></View>
      <View style={styles.card}><Text style={styles.cardLabel}>COMMUNICATION PATH</Text><View style={styles.pathRow}><PathNode label="Victim" /><Text style={styles.arrow}>→</Text><PathNode label="Relay" /><Text style={styles.arrow}>→</Text><PathNode label="Rescue" /></View></View>
      <Link href="/sos" asChild><Pressable style={styles.secondaryButton}><Text style={styles.secondaryButtonText}>OPEN SOS REPORT</Text></Pressable></Link>
    </ScrollView></SafeAreaView>
  );
}
function PathNode({ label }) { return <View style={styles.pathNode}><View style={styles.nodeMark} /><Text style={styles.nodeLabel}>{label}</Text></View>; }
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: APP_COLORS.background }, container: { padding: APP_SPACING.lg, paddingBottom: 44 }, eyebrow: { color: APP_COLORS.accent, fontSize: 12, fontWeight: '800', letterSpacing: 2, marginBottom: APP_SPACING.sm }, title: { color: APP_COLORS.text, fontSize: 30, fontWeight: '800', marginBottom: APP_SPACING.sm }, subtitle: { color: APP_COLORS.muted, fontSize: 16, lineHeight: 24, marginBottom: APP_SPACING.lg }, statusCard: { alignItems: 'flex-start', backgroundColor: APP_COLORS.surfaceRaised, borderColor: APP_COLORS.border, borderRadius: APP_RADII.lg, borderWidth: 1, flexDirection: 'row', marginBottom: APP_SPACING.md, padding: APP_SPACING.lg }, statusDot: { borderRadius: 8, height: 16, marginRight: APP_SPACING.md, marginTop: 2, width: 16 }, statusGood: { backgroundColor: APP_COLORS.success }, statusWaiting: { backgroundColor: APP_COLORS.warning }, statusCopy: { flex: 1 }, card: { backgroundColor: APP_COLORS.surface, borderColor: APP_COLORS.border, borderRadius: APP_RADII.md, borderWidth: 1, marginBottom: APP_SPACING.md, padding: APP_SPACING.md }, cardLabel: { color: APP_COLORS.muted, fontSize: 11, fontWeight: '800', letterSpacing: 1.4, marginBottom: APP_SPACING.sm }, statusTitle: { color: APP_COLORS.text, fontSize: 17, fontWeight: '700', lineHeight: 23 }, statusDetail: { color: APP_COLORS.muted, fontSize: 13, lineHeight: 19, marginTop: 6 }, uuid: { color: APP_COLORS.accent, fontFamily: 'monospace', fontSize: 12, marginBottom: APP_SPACING.sm }, note: { color: APP_COLORS.muted, fontSize: 13, lineHeight: 20 }, pathRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' }, pathNode: { alignItems: 'center', flex: 1 }, nodeMark: { backgroundColor: APP_COLORS.accent, borderRadius: 7, height: 14, marginBottom: 7, width: 14 }, nodeLabel: { color: APP_COLORS.text, fontSize: 12, fontWeight: '700' }, arrow: { color: APP_COLORS.muted, fontSize: 18 }, secondaryButton: { alignItems: 'center', backgroundColor: APP_COLORS.accent, borderRadius: APP_RADII.sm, minHeight: 52, justifyContent: 'center', paddingHorizontal: APP_SPACING.md }, secondaryButtonText: { color: APP_COLORS.background, fontSize: 13, fontWeight: '900', letterSpacing: 0.8 },
});
