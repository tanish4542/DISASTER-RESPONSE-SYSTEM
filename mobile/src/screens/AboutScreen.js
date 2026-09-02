import { useRouter } from 'expo-router';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

import { APP_COLORS, APP_RADII, APP_SPACING } from '@/constants/appTheme';

export default function AboutScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.eyebrow}>THE PROJECT</Text>
        <Text style={styles.title}>Disaster Response</Text>
        <Text style={styles.subtitle}>Emergency communication when connectivity fails.</Text>
        <InfoSection title="The problem">In a disaster, damaged infrastructure can make ordinary communication unreliable. People still need a way to report an emergency and move that report toward a response team.</InfoSection>
        <InfoSection title="The goal">This application is designed to capture essential emergency information locally, preserve it when a connection is unavailable, and support nearby device-to-device communication.</InfoSection>
        <View style={styles.flowCard}>
          <Text style={styles.cardLabel}>EMERGENCY COMMUNICATION CONCEPT</Text>
          <FlowLine label="Victim" detail="Creates an SOS report" />
          <FlowLine label="Nearby Relay" detail="Carries the report onward" />
          <FlowLine label="Rescue Dashboard" detail="Receives information for coordination" last />
        </View>
        <InfoSection title="Capabilities present">Offline SOS storage, GPS capture, backend synchronization when available, and an Android BLE proof of concept for nearby device communication are included in the current project.</InfoSection>
        <View style={styles.toolsSection}>
          <Text style={styles.cardLabel}>DEVELOPER TOOLS</Text>
          <Text style={styles.toolsNote}>Prototype communication tools for demonstration and device testing.</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Open Developer Tools" accessibilityHint="Open BLE testing and Phone B peripheral tools" onPress={() => router.push('/developer-tools')} style={({ pressed }) => [styles.toolButton, pressed && styles.toolButtonPressed]}>
            <View style={styles.toolIcon}><Text style={styles.toolIconText}>⌘</Text></View>
            <View style={styles.toolCopy}><Text style={styles.toolButtonText}>DEVELOPER TOOLS</Text><Text style={styles.toolDescription}>Open communication diagnostics and device tools.</Text></View>
            <Text style={styles.toolButtonArrow}>›</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoSection({ title, children }) {
  return <View style={styles.infoSection}><Text style={styles.sectionTitle}>{title}</Text><Text style={styles.body}>{children}</Text></View>;
}

function FlowLine({ label, detail, last }) {
  return <View style={styles.flowLine}><View style={styles.flowMarkerColumn}><View style={styles.flowMarker} />{!last ? <View style={styles.flowConnector} /> : null}</View><View style={styles.flowCopy}><Text style={styles.flowLabel}>{label}</Text><Text style={styles.flowDetail}>{detail}</Text></View></View>;
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: APP_COLORS.background },
  container: { padding: APP_SPACING.lg, paddingBottom: 44 },
  eyebrow: { color: APP_COLORS.accent, fontSize: 12, fontWeight: '800', letterSpacing: 2, marginBottom: APP_SPACING.sm },
  title: { color: APP_COLORS.text, fontSize: 32, fontWeight: '900', marginBottom: APP_SPACING.sm },
  subtitle: { color: APP_COLORS.muted, fontSize: 17, lineHeight: 24, marginBottom: APP_SPACING.xl },
  infoSection: { marginBottom: APP_SPACING.lg },
  sectionTitle: { color: APP_COLORS.text, fontSize: 18, fontWeight: '800', marginBottom: APP_SPACING.sm },
  body: { color: APP_COLORS.muted, fontSize: 14, lineHeight: 22 },
  flowCard: { backgroundColor: APP_COLORS.surface, borderColor: APP_COLORS.border, borderRadius: APP_RADII.md, borderWidth: 1, marginBottom: APP_SPACING.lg, padding: APP_SPACING.md },
  cardLabel: { color: APP_COLORS.muted, fontSize: 11, fontWeight: '800', letterSpacing: 1.3, marginBottom: APP_SPACING.md },
  flowLine: { flexDirection: 'row', minHeight: 52 },
  flowMarkerColumn: { alignItems: 'center', marginRight: APP_SPACING.md, width: 14 },
  flowMarker: { backgroundColor: APP_COLORS.accent, borderRadius: 7, height: 14, width: 14 },
  flowConnector: { backgroundColor: APP_COLORS.border, flex: 1, marginVertical: 3, width: 2 },
  flowCopy: { flex: 1 },
  flowLabel: { color: APP_COLORS.text, fontSize: 14, fontWeight: '700' },
  flowDetail: { color: APP_COLORS.muted, fontSize: 13, marginTop: 3 },
  toolsSection: { borderTopColor: APP_COLORS.border, borderTopWidth: 1, paddingTop: APP_SPACING.lg },
  toolsNote: { color: APP_COLORS.muted, fontSize: 13, lineHeight: 20, marginBottom: APP_SPACING.md },
  toolButton: { alignItems: 'center', backgroundColor: APP_COLORS.surfaceRaised, borderColor: APP_COLORS.border, borderRadius: APP_RADII.sm, borderWidth: 1, flexDirection: 'row', marginBottom: APP_SPACING.sm, minHeight: 64, paddingHorizontal: APP_SPACING.md },
  toolButtonPressed: { backgroundColor: APP_COLORS.accentSoft, borderColor: APP_COLORS.accent, opacity: 0.9 },
  toolIcon: { alignItems: 'center', backgroundColor: APP_COLORS.accentSoft, borderRadius: 20, height: 40, justifyContent: 'center', marginRight: APP_SPACING.sm, width: 40 },
  toolIconText: { color: APP_COLORS.accent, fontSize: 24, fontWeight: '800' },
  toolCopy: { flex: 1, paddingRight: APP_SPACING.sm },
  toolButtonText: { color: APP_COLORS.text, fontSize: 13, fontWeight: '800', letterSpacing: 0.7 },
  toolDescription: { color: APP_COLORS.muted, fontSize: 12, lineHeight: 17, marginTop: 4 },
  toolButtonArrow: { color: APP_COLORS.accent, fontSize: 30, lineHeight: 30 },
});
