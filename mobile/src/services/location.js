import { Platform } from 'react-native';
import * as Location from 'expo-location';

export async function getCurrentLocation() {
  if (Platform.OS === 'web') {
    return null;
  }

  const permission = await Location.requestForegroundPermissionsAsync();
  if (permission.status !== 'granted') {
    return null;
  }

  const position = await Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.Balanced,
  });

  return {
    latitude: position.coords.latitude,
    longitude: position.coords.longitude,
  };
}