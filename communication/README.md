# Communication - Disaster Response System

## Overview

The **Communication module** implements device-to-device emergency messaging for offline scenarios. It enables:

- **Bluetooth/Wi-Fi Direct** peer-to-peer communication
- **Store-and-forward** message propagation across disconnected networks
- **Message synchronization** between devices
- **Device discovery** and connection management
- **Duplicate prevention** and hop count tracking
- **Mesh networking** concepts for emergency response

## Architecture

### Core Components (Phase 4+)

- **Protocol Definition** - Message format, headers, routing rules
- **Storage** - Local message database and queue
- **Discovery** - Device detection and availability
- **Synchronization** - Message exchange and conflict resolution
- **Routing** - Multi-hop message forwarding
- **Security** - Message authentication and integrity

### Current Status

**Phase 1: Initialization**
- ✅ Module structure created
- ✅ Directory layout for protocol and implementation
- ⏳ Protocol design (Phase 4)
- ⏳ Bluetooth integration (Phase 4)
- ⏳ Wi-Fi Direct setup (Phase 4)
- ⏳ Message routing (Phase 4)

## Technology Stack

- **Mobile**: React Native (Expo)
- **Protocols**: Bluetooth LE, Wi-Fi Direct
- **Storage**: SQLite (on each device)
- **Libraries**: 
  - `expo-bluetooth` (Phase 4)
  - `react-native-wifi-p2p` (Phase 4)

## Project Structure

```
communication/
├── protocol/           # Message format & routing
│   ├── __init__.py
│   ├── message_format.py
│   ├── message_types.py
│   ├── routing_rules.py
│   ├── headers.py
│   └── compression.py
├── storage/            # Local message storage
│   ├── __init__.py
│   ├── message_store.py
│   ├── queue_manager.py
│   ├── db_schema.py
│   └── cleanup_policy.py
├── discovery/          # Device discovery
│   ├── __init__.py
│   ├── device_finder.py
│   ├── availability_tracker.py
│   ├── peer_manager.py
│   └── connection_handler.py
├── synchronization/    # Message exchange
│   ├── __init__.py
│   ├── sync_engine.py
│   ├── conflict_resolver.py
│   ├── ack_manager.py
│   └── retry_policy.py
├── README.md          # This file
└── .gitignore
```

## Planned Development

### Phase 4: Offline Communication
1. Define protocol and message format
2. Implement Bluetooth LE on mobile
3. Implement Wi-Fi Direct on mobile
4. Local message storage
5. Device discovery mechanism
6. Store-and-forward routing
7. Message synchronization
8. Integration with backend

## Message Format

### Protocol Definition (Phase 4)

```
[Header (4 bytes)] [Message ID (8 bytes)] [Hop Count (1 byte)] 
[Timestamp (4 bytes)] [Source ID (8 bytes)] [Destination ID (8 bytes)]
[Message Type (1 byte)] [Payload Length (2 bytes)] [Payload (variable)]
[Checksum (4 bytes)]
```

### Message Types
- `0x01` - SOS Alert
- `0x02` - Location Update
- `0x03` - ACK/Confirmation
- `0x04` - Sync Request
- `0x05` - Sync Response
- `0x06` - Heartbeat
- `0x07` - Routing Query

## Features

### Store-and-Forward
- Messages queued locally if destination unavailable
- Automatic retry with exponential backoff
- Forward to nearby peers if they have route to destination
- TTL (Time-To-Live) based message expiration

### Duplicate Prevention
- Unique message IDs
- Bloom filter for seen messages
- Message deduplication on storage

### Hop Count
- Initial TTL: 3 hops
- Decremented on each forward
- Discarded if TTL reaches 0

### Message Synchronization
- Bidirectional sync when devices connect
- Delta sync: only new/changed messages
- Conflict resolution by timestamp
- ACK-based reliability

## Device Discovery

### Bluetooth LE Scanning
```python
# Phase 4 implementation
from communication.discovery.device_finder import BluetoothScanner

scanner = BluetoothScanner()
nearby_devices = scanner.scan(duration=10, signal_strength_threshold=-70)
# Returns: [{'id': '...', 'name': '...', 'rssi': -50}, ...]
```

### Wi-Fi Direct Discovery
```python
from communication.discovery.device_finder import WiFiP2PScanner

scanner = WiFiP2PScanner()
nearby_devices = scanner.scan()
# Returns: [{'id': '...', 'name': '...', 'signal': -50}, ...]
```

## Message Storage

### SQLite Schema (Phase 4)

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    timestamp INTEGER,
    source_id TEXT,
    destination_id TEXT,
    message_type INTEGER,
    payload BLOB,
    hop_count INTEGER,
    is_forwarded BOOLEAN,
    ack_received BOOLEAN,
    created_at INTEGER,
    delivered_at INTEGER
);

CREATE TABLE peers (
    id TEXT PRIMARY KEY,
    name TEXT,
    last_seen INTEGER,
    is_connected BOOLEAN,
    connection_type TEXT  -- 'bluetooth' or 'wifi_p2p'
);

CREATE TABLE sync_state (
    peer_id TEXT PRIMARY KEY,
    last_sync INTEGER,
    message_count INTEGER
);
```

## Synchronization Protocol

### Connection Handshake
1. Device A discovers Device B
2. Device A sends SYNC_REQUEST with last_sync timestamp
3. Device B responds with SYNC_RESPONSE containing new message IDs
4. Device A requests missing messages
5. Device B sends messages in batches
6. Device A sends ACK after each batch
7. Devices update sync_state

## Integration with Mobile App

```javascript
// In mobile/src/services/communicationService.js
import { CommunicationManager } from '../../communication';

class CommunicationService {
  constructor() {
    this.manager = new CommunicationManager();
  }

  async startDiscovery() {
    const devices = await this.manager.discoveryService.scan();
    return devices;
  }

  async sendMessage(message) {
    await this.manager.storageService.store(message);
    
    const sent = await this.manager.synchronizationService.send(message);
    return sent;
  }

  async syncWithPeer(peerId) {
    const results = await this.manager.synchronizationService.sync(peerId);
    return results;
  }
}
```

## Performance Targets

- **Discovery time**: < 5 seconds for nearby devices
- **Message delivery**: < 1 second (direct connection)
- **Store-and-forward**: < 30 seconds (multi-hop)
- **Sync time**: < 10 seconds for 100 messages
- **Storage**: < 50MB for 10,000 messages

## Security Considerations

- Message authentication tags (Phase 4+)
- Device pairing/whitelisting (Phase 4+)
- Payload encryption (Phase 4+)
- Replay attack prevention (Phase 4+)

## Troubleshooting

### Device not found in discovery
- Ensure target device is in range (< 100m)
- Check Bluetooth/Wi-Fi is enabled
- Verify device is not in power-saving mode

### Messages not synchronizing
- Check device connectivity
- Verify device IDs match
- Check TTL/hop count hasn't expired
- Review sync_state timestamps

### High memory usage
- Implement message cleanup policy
- Set older message deletion threshold
- Reduce maximum queue size

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [Communication Protocol](../docs/communication.md)

## Resources

- [Bluetooth Low Energy Spec](https://www.bluetooth.com/specifications/specs/)
- [Wi-Fi Direct Spec](https://www.wi-fi.org/discover-wi-fi/wi-fi-direct)
- [Store-and-Forward Networks](https://en.wikipedia.org/wiki/Delay-tolerant_networking)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 4 (Implementation)  
**Last Updated**: August 2026
