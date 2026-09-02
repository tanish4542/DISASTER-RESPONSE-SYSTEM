from communication.store_and_forward import StoreAndForwardEngine


def test_demo_delivers_device_a_to_backend_and_preserves_message_id():
    result = StoreAndForwardEngine().run_demo()

    assert [step["device"] for step in result["steps"]] == [
        "Device-A",
        "Device-B",
        "Device-C",
        "BACKEND",
    ]
    assert result["message"]["current_device_id"] == "Device-C"
    assert result["message"]["message_id"] == "msg-emergency-001"
    assert result["message"]["hop_count"] == 2
    assert result["message"]["ttl"] == 1
    assert result["message"]["status"] == "DELIVERED"
    assert result["relays"] == 2
    assert result["duplicate_detected"] is True


def test_duplicate_is_not_stored_or_relayed_twice():
    engine = StoreAndForwardEngine()
    message = engine.create_message("emergency-duplicate", {})

    assert engine.receive_message("Device-B", message) is True
    assert engine.receive_message("Device-B", message) is False
    assert engine.duplicate_detections == 1
    assert len(engine.queues["Device-B"]) == 1


def test_ttl_exhaustion_prevents_forwarding():
    engine = StoreAndForwardEngine()
    message = engine.create_message("emergency-ttl", {}, ttl=0)

    assert engine.forward_message("Device-A", "Device-B", message) is None
    assert "Device-B" not in engine.queues


def test_unavailable_delivery_remains_queued():
    engine = StoreAndForwardEngine()
    message = engine.create_message("emergency-queued", {})

    queued = engine.deliver_message("Device-C", message, destination_available=False)

    assert queued.status == "QUEUED"
    assert queued.message_id == message.message_id
    assert engine.queues["Device-C"] == [queued]
