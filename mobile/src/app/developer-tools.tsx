import { useRouter } from 'expo-router';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

import { APP_COLORS, APP_RADII, APP_SPACING } from '@/constants/appTheme';

export default function DeveloperToolsScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.eyebrow}>DIAGNOSTICS</Text>
        <Text style={styles.title}>Developer Tools</Text>
        <Text style={styles.subtitle}>Communication tools for device testing and demonstration.</Text>

        <ToolCard
          icon="⌁"
          title="BLE Test"
          description="Scan for a nearby relay, connect, and send a test SOS."
          onPress={() => router.push('/ble-test')}
        />
        <ToolCard
          icon="◉"
          title="Phone B Peripheral"
          description="Advertise this device as the receiving BLE peripheral."
          onPress={() => router.push('/ble-native-peripheral')}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

function ToolCard({ icon, title, description, onPress }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Open ${title}`}
      onPress={onPress}
      style={({ pressed }) => [styles.toolCard, pressed && styles.toolCardPressed]}
    >
      <View style={styles.icon}><Text style={styles.iconText}>{icon}</Text></View>
      <View style={styles.copy}>
        <Text style={styles.toolTitle}>{title}</Text>
        <Text style={styles.toolDescription}>{description}</Text>
      </View>
      <Text style={styles.arrow}>›</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: APP_COLORS.background },
  container: { padding: APP_SPACING.lg, paddingBottom: 44 },
  eyebrow: { color: APP_COLORS.accent, fontSize: 12, fontWeight: '800', letterSpacing: 2, marginBottom: APP_SPACING.sm },
  title: { color: APP_COLORS.text, fontSize: 32, fontWeight: '900', marginBottom: APP_SPACING.sm },
  subtitle: { color: APP_COLORS.muted, fontSize: 16, lineHeight: 24, marginBottom: APP_SPACING.xl },
  toolCard: { alignItems: 'center', backgroundColor: APP_COLORS.surfaceRaised, borderColor: APP_COLORS.border, borderRadius: APP_RADII.md, borderWidth: 1, flexDirection: 'row', marginBottom: APP_SPACING.md, minHeight: 76, padding: APP_SPACING.md },
  toolCardPressed: { backgroundColor: APP_COLORS.accentSoft, borderColor: APP_COLORS.accent, opacity: 0.9 },
  icon: { alignItems: 'center', backgroundColor: APP_COLORS.accentSoft, borderRadius: 22, height: 44, justifyContent: 'center', marginRight: APP_SPACING.md, width: 44 },
  iconText: { color: APP_COLORS.accent, fontSize: 25, fontWeight: '800' },
  copy: { flex: 1, paddingRight: APP_SPACING.sm },
  toolTitle: { color: APP_COLORS.text, fontSize: 16, fontWeight: '800' },
  toolDescription: { color: APP_COLORS.muted, fontSize: 13, lineHeight: 19, marginTop: 4 },
  arrow: { color: APP_COLORS.accent, fontSize: 32, lineHeight: 32 },
});
