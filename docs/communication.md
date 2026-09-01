# Communication Protocol - Disaster Response System

## Overview

The Communication Protocol defines how emergency messages are exchanged between mobile devices in offline scenarios using Bluetooth and Wi-Fi Direct. This document specifies the message format, routing rules, and synchronization mechanisms.

## Communication Channels

### Bluetooth Low Energy (BLE)
- **Range**: 10-100 meters
- **Bandwidth**: 1-2 Mbps
- **Power**: Low battery consumption
- **Use Case**: Mobile-to-mobile short-range communication
- **Frequency**: 2.4 GHz

### Wi-Fi Direct
- **Range**: 50-200 meters
- **Bandwidth**: 10-54 Mbps
- **Power**: Higher consumption
- **Use Case**: Mobile-to-mobile medium-range, higher throughput
- **Frequency**: 2.4 GHz / 5 GHz

## Message Format

### Binary Protocol Definition (Phase 4)

```
[HEADER][MESSAGE_ID][HOP_COUNT][TIMESTAMP][SOURCE][DESTINATION][TYPE][PAYLOAD_LEN][PAYLOAD][CHECKSUM]
  1 B      8 B         1 B         4 B       8 B      8 B          1 B      2 B        Var      4 B
```

### Field Descriptions

| Field | Size | Description |
|-------|------|-------------|
| Header | 1 byte | Protocol version & flags (0x01 for v1) |
| Message ID | 8 bytes | Unique message identifier (UUID) |
| Hop Count | 1 byte | Remaining hops (TTL, max 3) |
| Timestamp | 4 bytes | Unix timestamp (seconds) |
| Source ID | 8 bytes | Source device identifier |
| Destination ID | 8 bytes | Destination device/backend ID |
| Message Type | 1 byte | See message types below |
| Payload Length | 2 bytes | Length of payload (0-65535 bytes) |
| Payload | Variable | Actual message content (JSON) |
| Checksum | 4 bytes | CRC32 checksum for integrity |

### Message Types

```
0x01 - SOS_ALERT              # Emergency report
0x02 - LOCATION_UPDATE        # GPS update
0x03 - ACK_CONFIRMATION       # Acknowledgment
0x04 - SYNC_REQUEST           # Sync initialization
0x05 - SYNC_RESPONSE          # Sync data response
0x06 - HEARTBEAT              # Keep-alive signal
0x07 - ROUTING_QUERY          # Route inquiry
0x08 - ROUTING_RESPONSE       # Route response
0x09 - MESSAGE_FORWARD        # Forwarded message
0x0A - DUPLICATE_FILTER       # Seen message ID
```

## Message Payloads

### SOS_ALERT (0x01)
```json
{
  "victim_id": "mobile_device_1",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "description": "Building collapsed, people trapped",
  "emergency_type": "structural_collapse",
  "photos": ["base64_photo_1", "base64_photo_2"],
  "severity": 9,
  "timestamp": 1693468200
}
```

### LOCATION_UPDATE (0x02)
```json
{
  "device_id": "mobile_device_1",
  "latitude": 28.7050,
  "longitude": 77.1030,
  "accuracy": 10,
  "timestamp": 1693468250
}
```

### ACK_CONFIRMATION (0x03)
```json
{
  "message_id": "uuid_12345",
  "source_id": "mobile_device_1",
  "status": "received",
  "timestamp": 1693468260
}
```

### SYNC_REQUEST (0x04)
```json
{
  "device_id": "mobile_device_1",
  "last_sync": 1693468000,
  "message_count": 45,
  "protocol_version": 1
}
```

### SYNC_RESPONSE (0x05)
```json
{
  "device_id": "mobile_device_2",
  "new_messages": [
    "msg_id_1",
    "msg_id_2",
    "msg_id_3"
  ],
  "message_count": 3,
  "timestamp": 1693468270
}
```

## Routing Rules

### Direct Communication
```
Device A ↔ Device B (connected)
```
- Send message directly to destination
- Wait for ACK
- Mark as delivered

### Store-and-Forward (Multi-hop)
```
Device A → Device B → Device C → Backend
```

1. Device A cannot reach Backend
2. Device A has Device B as neighbor
3. Device A forwards message to Device B
4. Device B stores message locally
5. When Device B connects to Backend (or Device C):
   - Check hop count (decrement)
   - Forward if hop count > 0
   - Update source_id to show path

### Routing Decision Logic

```
If destination == nearby device:
    Send directly
Else if destination == backend AND connected:
    Send directly
Else if hop_count > 0:
    Forward to random available peer
Else:
    Drop message (TTL expired)
    Log event
```

### Hop Count Policy

- **Initial TTL**: 3 hops
- **Decrement**: On each forward
- **Minimum**: 1 hop (discard at 0)
- **Purpose**: Prevent infinite loops

### Duplicate Prevention

Using Bloom filter for memory efficiency:

```
On receive:
  If message_id in bloom_filter:
    Discard (seen before)
  Else:
    Add to bloom_filter
    Process message
```

### Message Expiration

```
TTL = created_at + max_age_seconds
If current_time > TTL:
    Delete message
    Don't forward
```

Default max_age: 86400 seconds (24 hours)

## Synchronization Protocol

### Connection Phase

```
1. Device A discovers Device B via Bluetooth
2. Connection established
3. Device A initiates SYNC_REQUEST
   - Sends last_sync timestamp
   - Sends local message count
4. Device B responds with SYNC_RESPONSE
   - Lists new message IDs since last_sync
5. Device A requests missing messages
   - Batch requests (10 at a time)
6. Device B sends messages
7. Device A sends ACK for each batch
8. Sync state updated
   - last_sync = current_timestamp
```

### Conflict Resolution

When same message received from multiple devices:

```
1. Compare timestamps
2. Keep version with LATEST timestamp
3. Log conflict
4. Discard older version
5. Forward latest version to other peers
```

### Sync State Storage

```sqlite
CREATE TABLE sync_state (
    peer_id TEXT PRIMARY KEY,
    last_sync INTEGER,
    message_count INTEGER,
    sync_status TEXT  -- 'idle', 'syncing', 'error'
);
```

## Device Discovery

### Bluetooth Scanning

```
Duration: 30 seconds per scan
Signal Threshold: -70 dBm minimum
Scan Interval: Every 5 minutes (idle device)
Scan Interval: Every 30 seconds (active SOS mode)
```

### Available Devices

```json
{
  "device_id": "uuid_abc123",
  "name": "Rescue Mobile 2",
  "signal_strength": -55,
  "last_seen": 1693468270,
  "connection_type": "bluetooth",
  "connection_status": "connected"
}
```

## Retry Policy

### Exponential Backoff

```
Attempt 1: Immediate (0 seconds)
Attempt 2: 2 seconds
Attempt 3: 4 seconds
Attempt 4: 8 seconds
Attempt 5: 16 seconds
Max retries: 5
```

### Failed Message Handling

```
If message fails to send:
  1. Store in local queue
  2. Try again with exponential backoff
  3. After 5 failed attempts:
     - Log failure
     - Mark as "delivery_uncertain"
     - Notify user
```

## Security Measures

### Message Authentication (Phase 4+)

```
HMAC-SHA256(message + device_secret) → auth_tag
Append auth_tag to message
Verify on receive
```

### Device Pairing (Phase 4+)

```
1. First connection: Generate pairing code
2. Both devices display code
3. User confirms on both devices
4. Exchange device certificates
5. Store in local keystore
6. Future connections verified via certificate
```

### Replay Attack Prevention (Phase 4+)

```
Each message includes:
  - sequence_number (incremental)
  - timestamp
  
On receive:
  If timestamp too old (> 5 minutes):
      Reject (replay attack suspected)
  If sequence_number <= last_received:
      Reject (duplicate/replay)
```

## Performance Metrics

- **Message Delivery Time**: < 1 second (direct)
- **Multi-hop Delivery**: < 30 seconds
- **Sync Time**: < 10 seconds for 100 messages
- **Discovery Time**: < 5 seconds
- **Message Success Rate**: > 95%
- **Duplicate Prevention**: > 99% effective

## Testing Scenarios (Phase 4)

### Test 1: Direct Communication
```
Device A → Device B (Bluetooth)
Verify: Message received within 1 second
        ACK returned
        No duplicates
```

### Test 2: Multi-hop Relay
```
Device A → Device B → Device C → Backend
Verify: Message relayed correctly
        Hop count decremented
        No loops
```

### Test 3: Synchronization
```
Device A + Device B disconnected for 10 min
Device A receives 5 new messages
A and B connect
Verify: B receives all 5 messages
        No duplicates
        Sync completes in < 10 seconds
```

### Test 4: Network Partition
```
Create partition: {A,B} ↔ {C,D}
Send message from A to C
Verify: Message stored on B (can't route)
        When partition healed:
        Message delivered to C
```

## Integration with Mobile App

```javascript
// communicationService.js
class CommunicationService {
  async startAdvertising() {
    // Start BLE/Wi-Fi Direct advertising
  }

  async startScanning() {
    // Discover nearby devices
  }

  async connectToPeer(peerId) {
    // Establish connection
  }

  async sendMessage(message, destinationId) {
    // Send with store-and-forward
  }

  async syncWithPeer(peerId) {
    // Synchronize message history
  }

  async handleIncomingMessage(message) {
    // Process received message
    // Route if needed
    // Store locally
  }
}
```

## Future Enhancements (Phase 5+)

- Congestion control algorithms
- Quality of Service (QoS) levels
- Adaptive transmission rates
- Network coding for better efficiency
- Full mesh networking
- Hierarchical routing for large networks

---

**Version**: 1.0  
**Phase**: 1 (Protocol Definition)  
**Last Updated**: August 2026  
**Status**: ✅ Ready for Phase 4 Implementation
