import { Link } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import * as Location from 'expo-location';

import { APP_COLORS, APP_RADII, APP_SPACING } from '@/constants/appTheme';
import { checkBluetoothEnabled } from '@/services/bleService';

export default function HomeScreen() {
  const [bluetoothReady, setBluetoothReady] = useState(null);
  const [locationReady, setLocationReady] = useState(null);

  useEffect(() => {
    checkBluetoothEnabled().then(setBluetoothReady).catch(() => setBluetoothReady(false));
    Location.hasServicesEnabledAsync().then(setLocationReady).catch(() => setLocationReady(false));
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header} accessible accessibilityRole="header">
          <View>
            <View style={styles.brandLine}>
              <View style={styles.brandMark}><Text style={styles.brandMarkText}>+</Text></View>
              <Text style={styles.eyebrow}>DISASTER RESPONSE</Text>
            </View>
            <Text style={styles.title}>Stay connected when it matters.</Text>
          </View>
          <View style={styles.statusDot} accessible accessibilityLabel="System monitoring active" />
        </View>

        <Text style={styles.description}>
          Send a local emergency report and keep it moving through nearby communication links.
        </Text>

        <View style={styles.readinessCard}>
          <View style={styles.readinessHeader}>
            <Text style={styles.cardEyebrow}>READINESS</Text>
              <Text style={styles.readyLabel}>LIVE CHECK</Text>
          </View>
            <Text style={styles.readinessTitle}>Know what is ready before you need it.</Text>
          <View style={styles.statusGrid}>
              <StatusItem
                label="LOCATION"
                value={locationReady === null ? 'Checking...' : locationReady ? 'Ready' : 'Unavailable'}
                tone={locationReady === null ? 'muted' : locationReady ? 'success' : 'danger'}
              />
            <StatusItem
                label="COMMUNICATION"
                value={bluetoothReady === null ? 'Checking...' : bluetoothReady ? 'Ready' : 'Unavailable'}
                tone={bluetoothReady === null ? 'muted' : bluetoothReady ? 'success' : 'danger'}
            />
              <StatusItem label="SOS SERVICE" value="Ready" tone="accent" />
          </View>
        </View>

        <Link href="/sos" asChild>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Send SOS"
              accessibilityHint="Open the emergency report form"
              style={({ pressed }) => [styles.sosButton, pressed && styles.sosButtonPressed]}
            >
              <View style={styles.sosIcon}><Text style={styles.sosIconText}>!</Text></View>
            <Text style={styles.sosButtonKicker}>EMERGENCY ACTION</Text>
            <Text style={styles.sosButtonText}>SEND SOS</Text>
            <Text style={styles.sosButtonHint}>Capture details, location, and delivery status</Text>
          </Pressable>
        </Link>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>How emergency communication works</Text>
          <Text style={styles.sectionMeta}>3 STEPS</Text>
        </View>
        <View style={styles.flowCard}>
          <FlowStep number="01" title="Victim" detail="Report an emergency" />
          <FlowStep number="02" title="Nearby Relay" detail="Pass the message onward" />
          <FlowStep number="03" title="Rescue Dashboard" detail="Coordinate a response" />
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent activity</Text>
          <Text style={styles.sectionMeta}>LOCAL</Text>
        </View>
        <View style={styles.activityCard}>
          <View style={styles.activityIcon}><Text style={styles.activityIconText}>–</Text></View>
          <View style={styles.activityCopy}>
            <Text style={styles.activityTitle}>No recent emergencies</Text>
            <Text style={styles.activityDetail}>Saved SOS reports will appear here on this device.</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function StatusItem({ label, value, tone }) {
  return (
    <View style={styles.statusItem}>
      <View style={[styles.statusIndicator, styles[`statusIndicator${tone}`]]} />
      <View>
        <Text style={styles.statusLabel}>{label}</Text>
        <Text style={styles.statusValue}>{value}</Text>
      </View>
    </View>
  );
}

function FlowStep({ number, title, detail }) {
  return (
    <View style={styles.flowStep}>
      <View style={styles.flowNumber}><Text style={styles.flowNumberText}>{number}</Text></View>
      <View style={styles.flowCopy}>
        <Text style={styles.flowTitle}>{title}</Text>
        <Text style={styles.flowDetail}>{detail}</Text>
      </View>
    </View>
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
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: APP_SPACING.md,
  },
  brandLine: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: APP_SPACING.sm,
    marginBottom: APP_SPACING.sm,
  },
  brandMark: {
    alignItems: 'center',
    backgroundColor: APP_COLORS.danger,
    borderRadius: 6,
    height: 22,
    justifyContent: 'center',
    width: 22,
  },
  brandMarkText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '800',
  },
  eyebrow: {
    color: APP_COLORS.accent,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 2,
  },
  title: {
    color: APP_COLORS.text,
    fontSize: 30,
    fontWeight: '800',
    lineHeight: 35,
    maxWidth: 300,
  },
  description: {
    color: APP_COLORS.muted,
    fontSize: 16,
    lineHeight: 24,
    marginBottom: APP_SPACING.lg,
  },
  statusDot: {
    backgroundColor: APP_COLORS.success,
    borderRadius: 8,
    height: 12,
    marginTop: 8,
    width: 12,
  },
  readinessCard: {
    backgroundColor: APP_COLORS.surface,
    borderColor: APP_COLORS.border,
    borderRadius: APP_RADII.lg,
    borderWidth: 1,
    marginBottom: APP_SPACING.md,
    padding: APP_SPACING.md,
  },
  readinessHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: APP_SPACING.sm,
  },
  cardEyebrow: {
    color: APP_COLORS.muted,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  readyLabel: {
    color: APP_COLORS.success,
    fontSize: 11,
    fontWeight: '800',
  },
  readinessTitle: {
    color: APP_COLORS.text,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: APP_SPACING.md,
  },
  statusGrid: {
    borderTopColor: APP_COLORS.border,
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: APP_SPACING.sm,
    paddingTop: APP_SPACING.md,
  },
  statusItem: {
    alignItems: 'center',
    flex: 1,
    flexDirection: 'row',
    gap: APP_SPACING.sm,
  },
  statusIndicator: {
    borderRadius: 5,
    height: 10,
    width: 10,
  },
  statusIndicatoraccent: { backgroundColor: APP_COLORS.accent },
  statusIndicatorsuccess: { backgroundColor: APP_COLORS.success },
  statusIndicatormuted: { backgroundColor: APP_COLORS.warning },
  statusIndicatordanger: { backgroundColor: APP_COLORS.danger },
  statusLabel: {
    color: APP_COLORS.muted,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  statusValue: {
    color: APP_COLORS.text,
    fontSize: 12,
    marginTop: 2,
  },
  sosButton: {
    backgroundColor: APP_COLORS.danger,
    borderRadius: APP_RADII.lg,
    marginBottom: APP_SPACING.xl,
    padding: APP_SPACING.lg,
  },
  sosButtonPressed: {
    opacity: 0.82,
    transform: [{ scale: 0.985 }],
  },
  sosIcon: {
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
    borderRadius: 15,
    height: 30,
    justifyContent: 'center',
    marginBottom: APP_SPACING.sm,
    width: 30,
  },
  sosIconText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '900',
  },
  sosButtonKicker: {
    color: '#ffd9da',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  sosButtonText: {
    color: '#fff',
    fontSize: 30,
    fontWeight: '900',
    marginVertical: 4,
  },
  sosButtonHint: {
    color: '#ffe9e9',
    fontSize: 13,
  },
  sectionHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: APP_SPACING.sm,
  },
  sectionTitle: {
    color: APP_COLORS.text,
    fontSize: 18,
    fontWeight: '800',
  },
  sectionMeta: {
    color: APP_COLORS.accent,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  flowCard: {
    backgroundColor: APP_COLORS.surface,
    borderColor: APP_COLORS.border,
    borderRadius: APP_RADII.md,
    borderWidth: 1,
    padding: APP_SPACING.md,
  },
  flowStep: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    minHeight: 58,
  },
  flowNumber: {
    alignItems: 'center',
    backgroundColor: APP_COLORS.accentSoft,
    borderRadius: 16,
    height: 32,
    justifyContent: 'center',
    marginRight: APP_SPACING.sm,
    width: 32,
  },
  flowNumberText: {
    color: APP_COLORS.accent,
    fontSize: 10,
    fontWeight: '800',
  },
  flowCopy: {
    flex: 1,
  },
  flowTitle: {
    color: APP_COLORS.text,
    fontSize: 13,
    fontWeight: '700',
  },
  flowDetail: {
    color: APP_COLORS.muted,
    fontSize: 11,
    lineHeight: 15,
    marginTop: 4,
  },
  activityCard: {
    alignItems: 'center',
    backgroundColor: APP_COLORS.surface,
    borderColor: APP_COLORS.border,
    borderRadius: APP_RADII.md,
    borderWidth: 1,
    flexDirection: 'row',
    padding: APP_SPACING.md,
  },
  activityIcon: {
    alignItems: 'center',
    backgroundColor: APP_COLORS.surfaceRaised,
    borderRadius: 18,
    height: 36,
    justifyContent: 'center',
    marginRight: APP_SPACING.sm,
    width: 36,
  },
  activityIconText: {
    color: APP_COLORS.muted,
    fontSize: 20,
  },
  activityCopy: {
    flex: 1,
  },
  activityTitle: {
    color: APP_COLORS.text,
    fontSize: 14,
    fontWeight: '700',
  },
  activityDetail: {
    color: APP_COLORS.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 3,
  },
});
