# Mobile App - Disaster Response System

## Overview

The mobile application is a **React Native** (Expo) application designed for disaster victims to report emergencies and request rescue assistance. It works **offline-first** and can communicate with other nearby devices and the rescue backend when connectivity is available.

## Architecture

### Core Features (Future Phases)

- **SOS Reporting** - Quick emergency submission with location and description
- **Offline Storage** - Local SQLite database for persistent message storage
- **GPS Integration** - Automatic location capture for victim position
- **Device-to-Device Communication** - Bluetooth/Wi-Fi Direct messaging
- **Photo/Video Capture** - Document damage and emergency situations
- **Message Synchronization** - Sync with rescue backend when possible

### Current Screens (Phase 1+)

- Home screen (Phase 3)
- SOS form (Phase 3)
- Offline storage view (Phase 3)
- Device discovery (Phase 4)
- Message history (Phase 3)

## Technology Stack

- **Framework**: React Native (Expo)
- **Language**: JavaScript
- **Storage**: SQLite (via expo-sqlite)
- **Maps**: React Native Maps (Phase 3)
- **Networking**: Bluetooth/Wi-Fi Direct APIs (Phase 4)
- **Build System**: Expo

## Current Status

**Phase 1: Initialization**
- ✅ Project structure created
- ✅ Expo app initialized
- ✅ Directory structure for screens, components, services
- ⏳ SOS form (Phase 3)
- ⏳ Location services (Phase 3)
- ⏳ Offline storage (Phase 3)
- ⏳ Bluetooth communication (Phase 4)

## Installation

### Prerequisites

- Node.js (v18+) and npm
- Expo CLI: `npm install -g expo-cli`
- Android SDK (for Android testing)
- iOS development tools (for iOS testing)

### Setup

```bash
# Navigate to mobile directory
cd mobile

# Dependencies already installed during creation
npm install

# Or reinstall if needed
rm -rf node_modules package-lock.json
npm install
```

## Running the App

### Android (Local Development)

```bash
cd mobile
npm run android
```

Requires Android emulator or connected Android device.

### iOS (Local Development)

```bash
cd mobile
npm run ios
```

Requires Xcode and iOS simulator or connected iPhone.

### Web Preview

```bash
cd mobile
npm run web
```

Opens web preview at `http://localhost:19006/`

### Expo Go (Fast Development)

```bash
cd mobile
npm start
```

Then:
- Press `a` for Android
- Press `i` for iOS
- Scan QR code with Expo Go app

## Project Structure

```
mobile/
├── src/
│   ├── screens/         # Screen components (Phase 3+)
│   │   ├── HomeScreen.js
│   │   ├── SOSScreen.js
│   │   └── ...
│   ├── components/      # Reusable components
│   ├── services/        # Business logic services
│   │   ├── apiService.js
│   │   ├── bluetoothService.js (Phase 4)
│   │   └── ...
│   ├── storage/         # Local storage utilities
│   │   └── storageService.js (Phase 3)
│   ├── communication/   # Device-to-device messaging (Phase 4)
│   ├── location/        # GPS and location services (Phase 3)
│   ├── utils/           # Utility functions
│   └── App.js           # Root component
├── app.json             # Expo configuration
├── package.json
├── README.md           # This file
└── .gitignore
```

## Planned Development

### Phase 3: SOS Collection
- SOS form with text input
- Location capture
- Photo attachment
- Offline form storage
- Submit to backend when online

### Phase 4: Device-to-Device Communication
- Bluetooth/Wi-Fi Direct setup
- Device discovery
- Message relay
- Duplicate prevention
- Store-and-forward

### Phase 5+: Enhanced Features
- Real-time status updates
- Emergency message classification
- Priority notifications
- Damage documentation

## Configuration

### Expo Configuration (app.json)

```json
{
  "expo": {
    "name": "Disaster Response SOS",
    "slug": "disaster-response-sos",
    "version": "1.0.0",
    "orientation": "portrait",
    "userInterfaceStyle": "automatic",
    "scheme": "disastersos",
    "platforms": ["ios", "android", "web"]
  }
}
```

## Development Guidelines

- Use functional components with hooks
- Store reusable logic in services/
- Keep components focused and small
- Follow React Native best practices
- Use offline-first approach

## Testing

Manual testing on devices:

```bash
# Start dev server
npm start

# Test on Android
npm run android

# Test on iOS
npm run ios
```

## Troubleshooting

### Port 19000/19001 already in use

```bash
# Kill process using port
lsof -i :19000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

### Packages not installing

```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Bluetooth permissions (Android)

Add to `app.json`:
```json
{
  "plugins": [
    ["expo-bluetooth", { "microphonePermission": true }]
  ]
}
```

## Performance Considerations

- Minimize re-renders using `React.memo` and `useMemo`
- Use lazy loading for heavy components
- Cache API responses locally
- Limit database queries
- Optimize images before upload

## Building for Production

```bash
# Android APK/AAB
eas build -p android

# iOS IPA
eas build -p ios

# Requires EAS account: https://eas.expo.dev
```

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [Communication Protocol](../docs/communication.md)
- [Database Schema](../docs/database.md)

## Resources

- [React Native Docs](https://reactnative.dev/)
- [Expo Docs](https://docs.expo.dev/)
- [React Hooks Guide](https://react.dev/reference/react/hooks)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 3 (SOS implementation)  
**Last Updated**: August 2026

## Join the community

Join our community of developers creating universal apps.

- [Expo on GitHub](https://github.com/expo/expo): View our open source platform and contribute.
- [Discord community](https://chat.expo.dev): Chat with Expo users and ask questions.
