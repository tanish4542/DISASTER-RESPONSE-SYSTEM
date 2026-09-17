import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import '../operations.css';
import { getEmergencies } from '../services/api';
import EmergencyMap from '../components/EmergencyMap';
import CommunicationDemo from '../components/CommunicationDemo';
import BrandMark from '../components/BrandMark';
import { PRODUCT_LINE, PRODUCT_NAME } from '../brand';

const STATUS_OPTIONS = ['PENDING', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'];
const PRIORITY_FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

function OperationsDashboard() {
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const refreshInFlight = useRef(false);

  const loadEmergencies = useCallback(async () => {
    if (refreshInFlight.current) return;
    refreshInFlight.current = true;
    setLoading(true);
    setError('');

    try {
      const data = await getEmergencies();
      setEmergencies(Array.isArray(data) ? data.filter((item) => item.status !== 'RESOLVED') : []);
    } catch {
      setError('Unable to connect to the rescue server.');
    } finally {
      setLoading(false);
      refreshInFlight.current = false;
    }
  }, []);

  useEffect(() => {
    loadEmergencies();
    const intervalId = window.setInterval(loadEmergencies, 10000);
    return () => window.clearInterval(intervalId);
  }, [loadEmergencies]);

  const filteredEmergencies = useMemo(() => {
    return emergencies.filter((emergency) => {
      const priorityMatch = priorityFilter === 'ALL' || emergency.priority_level === priorityFilter;
      const statusMatch = statusFilter === 'ALL' || emergency.status === statusFilter;
      return priorityMatch && statusMatch;
    });
  }, [emergencies, priorityFilter, statusFilter]);

  const summary = useMemo(() => {
    const totals = {
      total: emergencies.length,
      critical: emergencies.filter((item) => item.priority_level === 'CRITICAL').length,
      high: emergencies.filter((item) => item.priority_level === 'HIGH').length,
      medium: emergencies.filter((item) => item.priority_level === 'MEDIUM').length,
      low: emergencies.filter((item) => item.priority_level === 'LOW').length,
      pending: emergencies.filter((item) => item.status === 'PENDING').length,
    };

    return totals;
  }, [emergencies]);

  const confidenceLabel = (value) => (
    typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'
  );
  const hasCurrentAiAnalysis = (emergency) => Boolean(emergency.priority_classification_source);
  const aiPriorityConfidence = (emergency) => (
    hasCurrentAiAnalysis(emergency) ? emergency.ai_priority_confidence : null
  );
  const prioritySourceLabel = (emergency) => (
    ({
      AI: 'AI',
      MANUAL: 'Manual override',
      MANUAL_REVIEW: 'Manual review',
      NOT_RELEVANT: 'Not relevant',
      LOW_RELEVANCE_CONFIDENCE: 'Low relevance confidence',
    }[emergency.priority_classification_source] || 'Legacy / Not analyzed')
  );
  const aiPriorityReason = (emergency) => (
    emergency.ai_priority
      ? emergency.ai_priority_reason
      : emergency.ai_relevant === false
        ? 'SOS was determined not relevant; priority was not classified.'
        : 'AI priority not available.'
  );

  return (
    <div className="dashboard-shell">
      <header className="command-header">
        <div className="command-identity">
          <a className="home-link" href="#" aria-label={PRODUCT_NAME}>
            <BrandMark compact />
          </a>
          <div>
            <p className="eyebrow">{PRODUCT_LINE}</p>
            <h1>Command view</h1>
            <p className="subtitle">Monitor, prioritize and manage emergency requests.</p>
          </div>
        </div>
        <div className="command-actions">
          <a className="ghost-link" href="#resolved">Resolved Emergencies</a>
          <a className="ghost-link" href="#">Homepage</a>
          <span className="auto-refresh-indicator">Auto-refresh: 10s</span>
          <button type="button" className="refresh-button" onClick={loadEmergencies} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span>Total incidents</span>
          <strong>{summary.total}</strong>
        </div>
        <button type="button" className={`summary-card critical ${priorityFilter === 'CRITICAL' ? 'selected' : ''}`} onClick={() => setPriorityFilter('CRITICAL')}>
          <span>Critical</span>
          <strong>{summary.critical}</strong>
        </button>
        <button type="button" className={`summary-card high ${priorityFilter === 'HIGH' ? 'selected' : ''}`} onClick={() => setPriorityFilter('HIGH')}>
          <span>High</span>
          <strong>{summary.high}</strong>
        </button>
        <button type="button" className={`summary-card medium ${priorityFilter === 'MEDIUM' ? 'selected' : ''}`} onClick={() => setPriorityFilter('MEDIUM')}>
          <span>Medium</span>
          <strong>{summary.medium}</strong>
        </button>
        <button type="button" className={`summary-card low ${priorityFilter === 'LOW' ? 'selected' : ''}`} onClick={() => setPriorityFilter('LOW')}>
          <span>Low</span>
          <strong>{summary.low}</strong>
        </button>
        <div className="summary-card pending">
          <span>Pending</span>
          <strong>{summary.pending}</strong>
        </div>
      </section>

      <section className="filters-panel">
        <div className="filter-group">
          <label htmlFor="priority-filter">Priority</label>
          <select id="priority-filter" value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)}>
            {PRIORITY_FILTERS.map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="clear-filters"
          onClick={() => { setPriorityFilter('ALL'); setStatusFilter('ALL'); }}
          disabled={priorityFilter === 'ALL' && statusFilter === 'ALL'}
        >
          Clear filters
        </button>

        <div className="filter-group">
          <label htmlFor="status-filter">Status</label>
          <select id="status-filter" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="ALL">All</option>
            {STATUS_OPTIONS.map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </div>
      </section>

      <EmergencyMap emergencies={emergencies} onSelectEmergency={(id) => { window.location.hash = `#emergency/${id}`; }} />

      {loading ? (
        <div className="state-box">Loading emergencies...</div>
      ) : error ? (
        <div className="state-box error-box">
          <p>{error}</p>
          <button type="button" className="retry-button" onClick={loadEmergencies}>Retry</button>
        </div>
      ) : filteredEmergencies.length === 0 ? (
        <div className="state-box">No incidents match the selected filters.</div>
      ) : (
        <div className="content-grid">
          <div className="list-panel">
            <div className="panel-label">
              <h2>Incident queue</h2>
              <span>{filteredEmergencies.length} shown</span>
            </div>
            {filteredEmergencies.map((emergency) => (
              <a
                key={emergency.id}
                className={`emergency-card ${String(emergency.priority_level || '').toLowerCase()}`}
                href={`#emergency/${emergency.id}`}
              >
                <div className="card-toprow">
                  <span className="priority-badge">{emergency.priority_level || 'LOW'}</span>
                  <span className={`status-pill status-${String(emergency.status || '').toLowerCase()}`}>{emergency.status}</span>
                </div>
                <div className="incident-card-title">
                  <span className="id-chip">Emergency #{emergency.id}</span>
                  {emergency.status === 'PENDING' ? <span className="new-badge">NEW</span> : null}
                </div>
                <p className="card-message">{emergency.message}</p>
                <div className="card-ai-row">
                  <strong>AI Priority: {emergency.ai_priority || 'Not classified'}</strong>
                  <span>Priority confidence: {confidenceLabel(aiPriorityConfidence(emergency))}</span>
                </div>
                <div className="meta-row muted">
                  <span>Final Priority: {emergency.priority_level || '—'}</span>
                  <span>Source: {prioritySourceLabel(emergency)}</span>
                </div>
                {emergency.priority_classification_review_required ? (
                  <div className="review-banner">Priority review required</div>
                ) : null}
                {emergency.operational_safety_processing ? <div className="review-banner">Safety evidence detected — processing continued</div> : null}
                <div className="meta-row muted">
                  <span>{emergency.people_affected} affected</span>
                  <span>Location: {emergency.latitude ?? '—'}, {emergency.longitude ?? '—'}</span>
                </div>
                <div className="meta-row muted">
                  <span>Injured: {emergency.injured ? 'Yes' : 'No'} · Trapped: {emergency.trapped ? 'Yes' : 'No'}</span>
                  <span>Fire: {emergency.fire ? 'Yes' : 'No'} · Medical: {emergency.medical_emergency ? 'Yes' : 'No'}</span>
                </div>
                <div className="meta-row muted">
                  <span>Updated {new Date(emergency.updated_at).toLocaleString()}</span>
                </div>
                <p className="card-ai-reason">{aiPriorityReason(emergency)}</p>
              </a>
            ))}
          </div>
        </div>
      )}

      <CommunicationDemo />
    </div>
  );
}

export default OperationsDashboard;
