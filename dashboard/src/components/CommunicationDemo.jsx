import { useState } from 'react';
import { runCommunicationSimulation } from '../services/communicationSimulation';

export default function CommunicationDemo() {
  const [result, setResult] = useState(null);

  return (
    <section className="communication-panel" aria-label="Offline Communication Simulation">
      <div className="communication-header">
        <div>
          <p className="eyebrow">Offline Network</p>
          <h2>Offline Communication Simulation</h2>
          <p className="communication-description">
            Software-only store-and-forward demonstration. No Bluetooth or Wi-Fi Direct is used.
          </p>
        </div>
        <button type="button" className="refresh-button" onClick={() => setResult(runCommunicationSimulation())}>
          Run Simulation
        </button>
      </div>

      {result ? (
        <>
          <div className="communication-flow">
            {result.steps.map((step, index) => (
              <div className="communication-step" key={step.device}>
                <strong>{step.device}</strong>
                <span>{step.action}</span>
                {index < result.steps.length - 1 ? <b aria-hidden="true">↓</b> : null}
              </div>
            ))}
          </div>
          <div className="communication-details">
            <div><span>Message ID</span><strong>{result.message.message_id}</strong></div>
            <div><span>Current device</span><strong>{result.message.current_device_id}</strong></div>
            <div><span>Hop count</span><strong>{result.message.hop_count}</strong></div>
            <div><span>TTL remaining</span><strong>{result.message.ttl}</strong></div>
            <div><span>Status</span><strong>{result.message.status}</strong></div>
            <div><span>Relays</span><strong>{result.relays}</strong></div>
            <div><span>Duplicate detection</span><strong>{result.duplicateDetected ? 'Detected and suppressed' : 'None'}</strong></div>
          </div>
        </>
      ) : (
        <p className="communication-empty">Run the simulation to view the relay path.</p>
      )}
    </section>
  );
}
