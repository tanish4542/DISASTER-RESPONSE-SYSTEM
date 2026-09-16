import { useEffect, useState } from 'react';
import { getEmergencies } from '../services/api';
import { PRODUCT_LINE, PRODUCT_NAME } from '../brand';

const confidenceLabel = (value) => (
  typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'
);

export default function ResolvedEmergencies() {
  const [emergencies, setEmergencies] = useState([]);
  const [error, setError] = useState('');
  const hasCurrentAiAnalysis = (emergency) => Boolean(emergency.priority_classification_source);

  useEffect(() => {
    getEmergencies('RESOLVED')
      .then((data) => setEmergencies(Array.isArray(data) ? data : []))
      .catch(() => setError('Unable to connect to the rescue server.'));
  }, []);

  return (
    <div className="dashboard-shell">
      <header className="command-header">
        <div>
          <p className="eyebrow">{PRODUCT_LINE}</p>
          <h1>Resolved Emergencies</h1>
          <p className="subtitle">Historical incidents retained for review.</p>
        </div>
        <div className="command-actions">
          <a className="ghost-link" href="#operations">Active dashboard</a>
          <a className="ghost-link" href="#" aria-label={PRODUCT_NAME}>Homepage</a>
        </div>
      </header>
      {error ? <div className="state-box error-box">{error}</div> : null}
      {!error && emergencies.length === 0 ? (
        <div className="state-box">No resolved emergencies found.</div>
      ) : (
        <div className="resolved-list">
          {emergencies.map((emergency) => (
            <a className="resolved-card" href={`#emergency/${emergency.id}`} key={emergency.id}>
              <div className="card-toprow">
                <strong>Emergency #{emergency.id}</strong>
                <span className="priority-badge">{emergency.priority_level}</span>
              </div>
              <p>{emergency.message}</p>
              <div className="meta-row">
                <span>{hasCurrentAiAnalysis(emergency) ? emergency.operational_category || 'Manual classification required' : 'Legacy / Not analyzed'}</span>
                <span>Score: {emergency.priority_score}</span>
              </div>
              <div className="meta-row muted">
                <span>{hasCurrentAiAnalysis(emergency) ? `${emergency.ai_disaster_type || 'Not applicable'} · AI confidence ${confidenceLabel(emergency.ai_disaster_type_confidence)}` : 'Legacy / Not analyzed'}</span>
                <span>Updated {new Date(emergency.updated_at).toLocaleString()}</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
