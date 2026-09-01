import { Link } from 'expo-router';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';

export default function HomeScreen() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Disaster Response System</Text>
        <Text style={styles.description}>
          Emergency assistance when communication infrastructure is unavailable.
        </Text>

        <Link href="/sos" style={styles.button}>
          <Text style={styles.buttonText}>🚨 SEND SOS</Text>
        </Link>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f4f7fb',
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 30,
    fontWeight: '700',
    color: '#102a43',
    textAlign: 'center',
    marginBottom: 12,
  },
  description: {
    fontSize: 16,
    color: '#3d4d63',
    textAlign: 'center',
    marginBottom: 28,
    lineHeight: 24,
  },
  button: {
    backgroundColor: '#d62828',
    borderRadius: 16,
    paddingVertical: 18,
    paddingHorizontal: 28,
    width: '100%',
    maxWidth: 320,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
});
