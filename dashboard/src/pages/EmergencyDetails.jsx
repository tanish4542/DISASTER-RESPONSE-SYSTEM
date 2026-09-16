import { useEffect, useState } from 'react';
import '../operations.css';
import { getEmergency, updateEmergencyCategory, updateEmergencyPriority, updateEmergencyStatus } from '../services/api';
import EmergencyMap from '../components/EmergencyMap';

const STATUS_OPTIONS = ['PENDING', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'];
const CATEGORY_OPTIONS = ['NATURAL DISASTER', 'HEALTH / SOCIETAL', 'INFRASTRUCTURE / TRANSPORT', 'OTHER'];
const PRIORITY_OPTIONS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const confidenceLabel = (value) => (
  typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'
);
const displayValue = (value, fallback = 'Legacy / Not analyzed') => value ?? fallback;
const hasCurrentAiAnalysis = (emergency) => Boolean(emergency.priority_classification_source);
const isNotActionable = (emergency) => (
  hasCurrentAiAnalysis(emergency)
  && (emergency.classification_source === 'NOT_RELEVANT'
    || emergency.classification_source === 'LOW_RELEVANCE_CONFIDENCE')
);
const finalPriorityExplanation = (emergency) => {
  if (emergency.priority_classification_review_required) {
    return 'Final rescue priority is pending manual selection; the displayed four-category value is only a temporary compatibility value.';
  }
  return emergency.final_priority_reason || 'Final priority is determined from structured SOS impact fields and urgency.';
};

export default function EmergencyDetails({ id }) {
  const [emergency, setEmergency] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => getEmergency(id)
    .then(setEmergency)
    .catch(() => setError('Unable to load this emergency.'));

  useEffect(() => { load(); }, [id]);

  const update = async (payload) => {
    setSaving(true);
    try {
      const updated = payload.operational_category
        ? await updateEmergencyCategory(id, payload.operational_category)
        : payload.manual_priority
          ? await updateEmergencyPriority(id, payload.manual_priority)
        : await updateEmergencyStatus(id, payload.status);
      setEmergency(updated);
    } catch {
      setError('Unable to update this emergency.');
    } finally {
      setSaving(false);
    }
  };

  if (error && !emergency) return <div className="dashboard-shell"><div className="state-box error-box">{error}</div></div>;
  if (!emergency) return <div className="dashboard-shell"><div className="state-box">Loading emergency...</div></div>;

  return (
    <div className="dashboard-shell">
      <header className="command-header">
        <div>
          <p className="eyebrow">Emergency details</p>
          <h1>Emergency #{emergency.id}</h1>
          <p className="subtitle">AI analysis and deterministic rescue priority are shown separately.</p>
        </div>
        <a className="ghost-link" href={emergency.status === 'RESOLVED' ? '#resolved' : '#operations'}>Back to {emergency.status === 'RESOLVED' ? 'resolved emergencies' : 'active dashboard'}</a>
      </header>

      {error ? <div className="status-message status-failed">{error}</div> : null}
      <section className="detail-section">
        <h3>INCIDENT INFORMATION</h3>
        <div className="detail-block"><p>{emergency.message}</p><small>Created {new Date(emergency.created_at).toLocaleString()} · Updated {new Date(emergency.updated_at).toLocaleString()}</small></div>
      </section>
      <section className="detail-section">
        <h3>LOCATION</h3>
        <div className="detail-grid">
          <div><span>Latitude</span><strong>{emergency.latitude ?? 'Location unavailable'}</strong></div>
          <div><span>Longitude</span><strong>{emergency.longitude ?? 'Location unavailable'}</strong></div>
        </div>
        <EmergencyMap emergencies={[emergency]} onSelectEmergency={() => {}} />
      </section>
      <section className="detail-section">
        <h3>IMPACT</h3>
        <div className="detail-grid">
          <div><span>People affected</span><strong>{emergency.people_affected}</strong></div>
          <div><span>Injured</span><strong>{emergency.injured ? 'Yes' : 'No'}</strong></div>
          <div><span>Trapped</span><strong>{emergency.trapped ? 'Yes' : 'No'}</strong></div>
          <div><span>Fire</span><strong>{emergency.fire ? 'Yes' : 'No'}</strong></div>
          <div><span>Medical emergency</span><strong>{emergency.medical_emergency ? 'Yes' : 'No'}</strong></div>
        </div>
      </section>
      <section className="detail-section ai-analysis">
        <div className="ai-analysis-header"><h3>AI ANALYSIS</h3><span>{hasCurrentAiAnalysis(emergency) ? displayValue(emergency.classification_source) : 'Legacy / Not analyzed'}</span></div>
        <div className="ai-analysis-grid">
         <div><span>AI Relevance</span><strong>{!hasCurrentAiAnalysis(emergency) ? 'Legacy / Not analyzed' : emergency.ai_relevant == null ? 'Not analyzed' : emergency.ai_relevant ? 'RELEVANT' : 'NOT RELEVANT'}</strong></div>
         <div><span>Relevance confidence</span><strong>{confidenceLabel(hasCurrentAiAnalysis(emergency) ? emergency.ai_relevance_confidence : null)}</strong></div>
         <div><span>Safety evidence</span><strong>{hasCurrentAiAnalysis(emergency) ? (emergency.emergency_evidence_detected ? 'Detected' : 'Not detected') : 'Legacy / Not analyzed'}</strong></div>
         <div><span>Operational processing</span><strong>{hasCurrentAiAnalysis(emergency) ? (emergency.operational_safety_processing ? 'Emergency evidence detected — analysis continued' : 'Normal relevance processing') : 'Legacy / Not analyzed'}</strong></div>
          <div><span>Disaster Type</span><strong>{isNotActionable(emergency) ? 'N/A' : hasCurrentAiAnalysis(emergency) ? displayValue(emergency.ai_disaster_type) : 'Legacy / Not analyzed'}</strong></div>
          <div><span>Disaster type confidence</span><strong>{confidenceLabel(hasCurrentAiAnalysis(emergency) ? emergency.ai_disaster_type_confidence : null)}</strong></div>
          <div><span>Disaster category</span><strong>{isNotActionable(emergency) ? 'N/A' : hasCurrentAiAnalysis(emergency) ? displayValue(emergency.operational_category, emergency.classification_review_required ? 'Manual classification required' : undefined) : 'Legacy / Not analyzed'}</strong></div>
          <div><span>Disaster review required</span><strong>{hasCurrentAiAnalysis(emergency) && emergency.classification_review_required ? 'Yes' : 'No'}</strong></div>
          <div><span>AI Priority</span><strong>{isNotActionable(emergency) ? 'N/A' : hasCurrentAiAnalysis(emergency) ? displayValue(emergency.ai_priority) : 'Legacy / Not analyzed'}</strong></div>
          <div><span>AI Priority confidence</span><strong>{confidenceLabel(hasCurrentAiAnalysis(emergency) ? emergency.ai_priority_confidence : null)}</strong></div>
          <div><span>Priority source</span><strong>{displayValue(emergency.priority_classification_source)}</strong></div>
          <div><span>Priority review required</span><strong>{emergency.priority_classification_review_required ? 'Yes' : 'No'}</strong></div>
        </div>
        <div className="ai-reason"><strong>Disaster classification reason</strong><p>{hasCurrentAiAnalysis(emergency) ? displayValue(emergency.ai_classification_reason) : 'Legacy / Not analyzed'}</p></div>
        <div className="ai-reason"><strong>AI priority reason</strong><p>{hasCurrentAiAnalysis(emergency) ? displayValue(emergency.ai_priority_reason) : 'Legacy / Not analyzed'}</p></div>
        {hasCurrentAiAnalysis(emergency) && !isNotActionable(emergency) ? (
          <div className="category-actions">
            {CATEGORY_OPTIONS.map((category) => <button type="button" className={emergency.operational_category === category ? 'category-button selected' : 'category-button'} key={category} onClick={() => update({ operational_category: category })} disabled={saving}>{category}</button>)}
          </div>
        ) : <p className="detail-note">Not relevant or below the operational relevance threshold — no further classification.</p>}
        {emergency.priority_classification_review_required ? (
          <div className="category-actions manual-review">
            <strong>Manual priority review required</strong>
            {PRIORITY_OPTIONS.map((priority) => (
              <button type="button" className={emergency.priority_classification_source === 'MANUAL' && emergency.priority_level === priority ? 'category-button selected' : 'category-button'} key={priority} onClick={() => update({ manual_priority: priority })} disabled={saving}>{priority}</button>
            ))}
          </div>
        ) : null}
      </section>
      <section className="detail-section">
        <h3>FINAL RESCUE PRIORITY</h3>
        <div className={`priority-summary ${String(emergency.priority_level || '').toLowerCase()}`}>
          <div><span>Final Priority</span><strong>{emergency.priority_classification_review_required ? 'Pending Manual Review' : emergency.priority_level}</strong></div>
          <div><span>Priority Score</span><strong>{emergency.priority_score}</strong></div>
        </div>
        <div className="detail-grid">
          <div><span>Urgency input</span><strong>{emergency.urgency}</strong></div>
        </div>
        <p className="detail-note">{finalPriorityExplanation(emergency)}</p>
        <p className="detail-note">Safety protection applied: {emergency.safety_protection_applied ? 'Yes' : 'No'}</p>
        <p className="detail-note">Final rescue priority is calculated deterministically from the SOS impact fields and urgency input.</p>
      </section>
      <section className="status-control">
        <label htmlFor="detail-status">Current status</label>
        <select id="detail-status" value={emergency.status} onChange={(event) => update({ status: event.target.value })} disabled={saving}>
          {STATUS_OPTIONS.map((status) => <option value={status} key={status}>{status}</option>)}
        </select>
      </section>
    </div>
  );
}
