"""Deterministic in-memory store-and-forward communication simulation."""
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class StoreAndForwardMessage:
    message_id: str
    emergency_id: str
    source_device_id: str
    current_device_id: str
    destination: str
    payload: dict[str, Any]
    hop_count: int
    ttl: int
    created_at: str
    status: str


class StoreAndForwardEngine:
    def __init__(self) -> None:
        self.queues: dict[str, list[StoreAndForwardMessage]] = {}
        self.seen: dict[str, set[str]] = {}
        self.relay_count = 0
        self.duplicate_detections = 0

    def create_message(
        self,
        emergency_id: str,
        payload: dict[str, Any],
        ttl: int = 3,
        source_device_id: str = "Device-A",
        destination: str = "BACKEND",
    ) -> StoreAndForwardMessage:
        if ttl < 0:
            raise ValueError("ttl must be non-negative")
        return StoreAndForwardMessage(
            message_id=f"msg-{emergency_id}",
            emergency_id=emergency_id,
            source_device_id=source_device_id,
            current_device_id=source_device_id,
            destination=destination,
            payload=payload,
            hop_count=0,
            ttl=ttl,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="SOS_CREATED",
        )

    def store_message(self, device_id: str, message: StoreAndForwardMessage) -> bool:
        device_seen = self.seen.setdefault(device_id, set())
        if message.message_id in device_seen:
            self.duplicate_detections += 1
            return False
        device_seen.add(message.message_id)
        self.queues.setdefault(device_id, []).append(message)
        return True

    def receive_message(self, device_id: str, message: StoreAndForwardMessage) -> bool:
        received = replace(message, current_device_id=device_id, status="RELAYED")
        return self.store_message(device_id, received)

    def forward_message(
        self,
        from_device_id: str,
        to_device_id: str,
        message: StoreAndForwardMessage,
    ) -> StoreAndForwardMessage | None:
        if message.ttl <= 0:
            return None
        forwarded = replace(
            message,
            current_device_id=to_device_id,
            hop_count=message.hop_count + 1,
            ttl=message.ttl - 1,
            status="RELAYED",
        )
        if self.receive_message(to_device_id, forwarded):
            self.relay_count += 1
            return forwarded
        return None

    def deliver_message(
        self,
        device_id: str,
        message: StoreAndForwardMessage,
        destination_available: bool = True,
    ) -> StoreAndForwardMessage:
        if not destination_available:
            queued = replace(message, current_device_id=device_id, status="QUEUED")
            self.queues.setdefault(device_id, []).append(queued)
            return queued
        return replace(
            message,
            current_device_id=device_id,
            status="DELIVERED",
        )

    def run_demo(self) -> dict[str, Any]:
        message = self.create_message(
            emergency_id="emergency-001",
            payload={"message": "SOS from Device A"},
        )
        self.store_message("Device-A", message)
        device_b_message = self.forward_message("Device-A", "Device-B", message)
        if device_b_message is None:
            raise RuntimeError("Device-B relay failed")
        duplicate_received = not self.receive_message("Device-B", device_b_message)
        device_c_message = self.forward_message("Device-B", "Device-C", device_b_message)
        if device_c_message is None:
            raise RuntimeError("Device-C relay failed")
        delivered = self.deliver_message("Device-C", device_c_message)
        return {
            "message": asdict(delivered),
            "steps": [
                {"device": "Device-A", "action": "SOS CREATED"},
                {"device": "Device-B", "action": "RELAYED"},
                {"device": "Device-C", "action": "RELAYED"},
                {"device": "BACKEND", "action": "DELIVERED"},
            ],
            "relays": self.relay_count,
            "duplicate_detected": duplicate_received,
        }
