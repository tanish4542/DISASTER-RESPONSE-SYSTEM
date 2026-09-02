import { DarkTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { AppState } from 'react-native';

import { AnimatedSplashOverlay } from '@/components/animated-icon';
import { initializeEmergencyDatabase } from '@/storage/emergencyRepository';
import { startForegroundBle, stopForegroundBle } from '@/services/bleService';

SplashScreen.preventAutoHideAsync();

export default function TabLayout() {
  useEffect(() => {
    initializeEmergencyDatabase().catch(() => {
      // Ignore initialization failures at startup and keep the app usable.
    });
  }, []);

  useEffect(() => {
    startForegroundBle();
    const appStateSubscription = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'active') {
        startForegroundBle();
      } else {
        stopForegroundBle();
      }
    });

    return () => {
      appStateSubscription.remove();
      stopForegroundBle();
    };
  }, []);

  return (
    <ThemeProvider value={DarkTheme}>
      <AnimatedSplashOverlay />
      <Stack screenOptions={{ headerStyle: { backgroundColor: '#131c24' }, headerTintColor: '#f4f7fa', headerTitleStyle: { fontWeight: '800' } }}>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="developer-tools" options={{ title: 'Developer Tools' }} />
        <Stack.Screen name="ble-test" options={{ title: 'BLE Test' }} />
        <Stack.Screen name="ble-native-peripheral" options={{ title: 'Phone B Peripheral' }} />
      </Stack>
    </ThemeProvider>
  );
}
