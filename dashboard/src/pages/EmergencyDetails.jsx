import { useEffect, useState } from 'react';
import '../operations.css';
import { getEmergency, updateEmergencyPriority, updateEmergencyStatus } from '../services/api';
import EmergencyMap from '../components/EmergencyMap';

const STATUS_OPTIONS = ['PENDING', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'];
const PRIORITY_OPTIONS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const confidenceLabel = (value) => (
  typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'
);
const displayValue = (value, fallback = 'Legacy / Not analyzed') => value ?? fallback;
const hasCurrentAiAnalysis = (emergency) => Boolean(emergency.priority_classification_source);
const isNotActionable = (emergency) => (
  hasCurrentAiAnalysis(emergency)
  && emergency.ai_priority == null
  && !emergency.operational_safety_processing
);
const finalPriorityExplanation = (emergency) => {
  if (emergency.priority_classification_review_required) {
    return 'Final rescue priority is pending manual selection; the displayed four-category value is only a temporary compatibility value.';
  }
  return emergency.final_priority_reason || 'Final priority is unavailable.';
};

export default function EmergencyDetails({ id }) {
  const [emergency, setEmergency] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);
  const [interventionOpen, setInterventionOpen] = useState(false);
  const [selectedPriority, setSelectedPriority] = useState('');

  const load = () => getEmergency(id)
    .then(setEmergency)
    .catch(() => setError('Unable to load this emergency.'));

  useEffect(() => { load(); }, [id]);

  const update = async (payload) => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const updated = payload.manual_priority
          ? await updateEmergencyPriority(id, payload.manual_priority)
        : await updateEmergencyStatus(id, payload.status);
      setEmergency(updated);
      setSuccess('Status updated successfully.');
    } catch {
      setError('Unable to update this emergency.');
    } finally {
      setSaving(false);
    }
  };

  const applyManualDecision = async () => {
    if (!selectedPriority) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const updated = await updateEmergencyPriority(id, selectedPriority);
      setEmergency(updated);
      try {
        const refreshed = await getEmergency(id);
        setEmergency(refreshed);
      } catch {
        // Keep the successful PATCH response if the follow-up refresh fails.
      }
      setInterventionOpen(false);
      setSuccess('Manual decision applied successfully.');
    } catch {
      setError('Unable to apply the manual decision.');
    } finally {
      setSaving(false);
    }
  };

  const openIntervention = () => {
    setSelectedPriority(emergency.priority_level || emergency.ai_priority || 'LOW');
    setInterventionOpen(true);
    setError('');
    setSuccess('');
  };

  if (error && !emergency) return <div className="dashboard-shell"><div className="state-box error-box">{error}</div></div>;
  if (!emergency) return <div className="dashboard-shell"><div className="state-box">Loading emergency...</div></div>;

  const classificationSource = emergency.priority_classification_source === 'MANUAL'
    ? 'MANUAL OVERRIDE'
    : displayValue(emergency.priority_classification_source);
  const manualExplanation = emergency.priority_classification_source === 'MANUAL'
    ? emergency.ai_priority === emergency.priority_level
      ? `Manual operator confirmed the AI priority as ${emergency.priority_level}.`
      : `Manual operator override changed final priority from ${emergency.ai_priority || 'unavailable'} to ${emergency.priority_level}.`
    : null;

  return (
    <div className="dashboard-shell">
      <header className="command-header">
        <div>
          <p className="eyebrow">Emergency details</p>
          <h1>Emergency #{emergency.id}</h1>
          <p className="subtitle">Rescue operations overview</p>
        </div>
        <div className="detail-header-actions">
          <span className={`priority-badge ${String(emergency.priority_level || 'LOW').toLowerCase()}`}>{emergency.priority_level || 'LOW'}</span>
          <span className={`status-pill status-${String(emergency.status || '').toLowerCase()}`}>{emergency.status}</span>
          <a className="ghost-link" href={emergency.status === 'RESOLVED' ? '#resolved' : '#operations'}>Back to {emergency.status === 'RESOLVED' ? 'resolved emergencies' : 'active dashboard'}</a>
        </div>
      </header>

      {error ? <div className="status-message status-failed">{error}</div> : null}
      {success ? <div className="status-message">{success}</div> : null}
      <section className="detail-section">
        <div className="section-heading"><div><p className="eyebrow">Incoming report</p><h2>Emergency Information</h2></div></div>
        <div className="detail-block"><p className="incident-message">{emergency.message}</p><small>Created {new Date(emergency.created_at).toLocaleString()} · Updated {new Date(emergency.updated_at).toLocaleString()}</small></div>
        <div className="detail-grid impact-grid">
          <div><span>People affected</span><strong>{emergency.people_affected}</strong></div>
          <div><span>Injured</span><strong>{emergency.injured ? 'Yes' : 'No'}</strong></div>
          <div><span>Trapped</span><strong>{emergency.trapped ? 'Yes' : 'No'}</strong></div>
          <div><span>Fire</span><strong>{emergency.fire ? 'Yes' : 'No'}</strong></div>
          <div><span>Medical emergency</span><strong>{emergency.medical_emergency ? 'Yes' : 'No'}</strong></div>
          <div><span>Urgency input</span><strong>{emergency.urgency}</strong></div>
        </div>
      </section>
      <section className="detail-section ai-analysis">
        <div className="ai-analysis-header"><div><p className="eyebrow">Decision support</p><h2>AI Analysis</h2></div><div className="ai-analysis-actions"><span>{hasCurrentAiAnalysis(emergency) ? classificationSource : 'Legacy / Not analyzed'}</span><button type="button" className="secondary-action" onClick={openIntervention}>Manual Intervention</button></div></div>
        <div className="ai-analysis-grid">
         <div><span>AI Relevance</span><strong>{!hasCurrentAiAnalysis(emergency) ? 'Legacy / Not analyzed' : emergency.ai_relevant == null ? 'Not analyzed' : emergency.ai_relevant ? 'RELEVANT' : 'NOT RELEVANT'}</strong></div>
         <div><span>Relevance confidence (experimental)</span><strong>{confidenceLabel(hasCurrentAiAnalysis(emergency) ? emergency.ai_relevance_confidence : null)}</strong></div>
         <div><span>Safety evidence</span><strong>{hasCurrentAiAnalysis(emergency) ? (emergency.emergency_evidence_detected ? 'Detected' : 'Not detected') : 'Legacy / Not analyzed'}</strong></div>
         <div><span>Operational processing</span><strong>{hasCurrentAiAnalysis(emergency) ? (emergency.operational_safety_processing ? 'Continued due to safety evidence' : isNotActionable(emergency) ? 'Stopped after relevance' : 'Continued') : 'Legacy / Not analyzed'}</strong></div>
          <div><span>AI Priority</span><strong>{isNotActionable(emergency) ? 'NOT PERFORMED' : hasCurrentAiAnalysis(emergency) ? displayValue(emergency.ai_priority) : 'Legacy / Not analyzed'}</strong></div>
          <div><span>Priority confidence (experimental)</span><strong>{confidenceLabel(hasCurrentAiAnalysis(emergency) ? emergency.ai_priority_confidence : null)}</strong></div>
          <div><span>Priority source</span><strong>{classificationSource}</strong></div>
          <div><span>Priority review required</span><strong>{emergency.priority_classification_review_required ? 'Yes' : 'No'}</strong></div>
        </div>
        <div className="ai-reason"><strong>Why this classification</strong><p>{isNotActionable(emergency) ? 'Priority classification was not performed because the SOS was determined to be not relevant.' : hasCurrentAiAnalysis(emergency) ? displayValue(emergency.ai_priority_reason) : 'Legacy / Not analyzed'}</p></div>
        {emergency.operational_safety_processing ? <p className="detail-note safety-note">Safety evidence detected. Operational processing continued despite the relevance result.</p> : null}
        {manualExplanation ? <p className="detail-note manual-decision-note">{manualExplanation}</p> : null}
        {interventionOpen ? (
          <div className="manual-intervention-panel">
            <div>
              <p className="eyebrow">Operator action</p>
              <h3>Manual Intervention</h3>
              <p>AI classifications can be incorrect. A rescue operator can review the incident and override the final priority when necessary.</p>
            </div>
            <div className="manual-intervention-summary">
              <div><span>Current AI Priority</span><strong>{emergency.ai_priority || 'Not classified'}</strong></div>
              <div><span>AI Priority Confidence</span><strong>{confidenceLabel(emergency.ai_priority_confidence)}</strong></div>
              <div><span>Current Final Priority</span><strong>{emergency.priority_level}</strong></div>
            </div>
            <div className="category-actions" aria-label="Select final priority">
              {PRIORITY_OPTIONS.map((priority) => (
                <button type="button" className={`category-button ${String(priority).toLowerCase()}${selectedPriority === priority ? ' selected' : ''}`} key={priority} onClick={() => setSelectedPriority(priority)} disabled={saving}>{priority}</button>
              ))}
            </div>
            <div className="manual-intervention-actions">
              <button type="button" className="primary-action" onClick={applyManualDecision} disabled={saving || !selectedPriority}>{saving ? 'Applying...' : 'Apply Manual Decision'}</button>
              <button type="button" className="clear-filters" onClick={() => setInterventionOpen(false)} disabled={saving}>Cancel</button>
            </div>
          </div>
        ) : null}
      </section>
      <section className="detail-section">
        <div className="section-heading"><div><p className="eyebrow">Operational decision</p><h2>Final Rescue Priority</h2></div></div>
        <div className={`priority-summary ${String(emergency.priority_level || '').toLowerCase()}`}>
          <div><span>Final Priority</span><strong>{emergency.priority_classification_review_required ? 'Pending Manual Review' : emergency.priority_level}</strong></div>
          <span className={`priority-badge ${String(emergency.priority_level || 'LOW').toLowerCase()}`}>{emergency.priority_level || 'LOW'}</span>
        </div>
        <div className="detail-grid decision-meta">
          <div><span>Source</span><strong>{classificationSource || 'Unavailable'}</strong></div>
          <div><span>Review required</span><strong>{emergency.priority_classification_review_required ? 'Yes' : 'No'}</strong></div>
        </div>
        <p className="detail-note">{manualExplanation || finalPriorityExplanation(emergency)}</p>
        {emergency.safety_protection_applied ? <p className="detail-note safety-note">Safety protection applied to this incident.</p> : null}
      </section>
      <section className="status-control">
        <div><p className="eyebrow">Rescue operations</p><label htmlFor="detail-status">Operational status</label></div>
        <select id="detail-status" className={`status-select status-${String(emergency.status || '').toLowerCase()}`} value={emergency.status} onChange={(event) => update({ status: event.target.value })} disabled={saving}>
          {STATUS_OPTIONS.map((status) => <option value={status} key={status}>{status}</option>)}
        </select>
        {saving ? <span className="status-saving">Saving...</span> : null}
      </section>
      <section className="detail-section location-section">
        <div className="section-heading"><div><p className="eyebrow">Coordinates and map</p><h2>Incident Location</h2></div></div>
        <EmergencyMap emergencies={[emergency]} onSelectEmergency={() => {}} />
        <div className="detail-grid location-coordinates">
          <div><span>Latitude</span><strong>{emergency.latitude ?? 'Location unavailable'}</strong></div>
          <div><span>Longitude</span><strong>{emergency.longitude ?? 'Location unavailable'}</strong></div>
        </div>
      </section>
    </div>
  );
}
