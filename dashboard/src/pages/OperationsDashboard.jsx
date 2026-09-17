import { useEffect, useMemo, useState } from 'react';
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

  const loadEmergencies = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await getEmergencies();
      setEmergencies(Array.isArray(data) ? data.filter((item) => item.status !== 'RESOLVED') : []);
    } catch (loadError) {
      setError('Unable to connect to the rescue server.');
      setEmergencies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmergencies();
  }, []);

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
      pending: emergencies.filter((item) => item.status === 'PENDING').length,
    };

    return totals;
  }, [emergencies]);

  const confidenceLabel = (value) => (
    typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'
  );
  const hasCurrentAiAnalysis = (emergency) => Boolean(emergency.priority_classification_source);
  const aiPriorityLabel = (emergency) => (
    hasCurrentAiAnalysis(emergency) && emergency.ai_priority
      ? emergency.ai_priority
      : 'Legacy / Not analyzed'
  );
  const aiPriorityConfidence = (emergency) => (
    hasCurrentAiAnalysis(emergency) ? emergency.ai_priority_confidence : null
  );
  const prioritySourceLabel = (emergency) => (
    emergency.priority_classification_source || 'Legacy / Not analyzed'
  );
  const finalPriorityLabel = (emergency) => (
    emergency.priority_classification_review_required
      ? 'Pending Manual Priority Review'
      : `Final Priority: ${emergency.priority_level}`
  );
  const safetyElevation = (emergency) => (
    emergency.safety_protection_applied ? emergency.final_priority_reason : null
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
          <button type="button" className="refresh-button" onClick={loadEmergencies}>
            Refresh
          </button>
        </div>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span>Total incidents</span>
          <strong>{summary.total}</strong>
        </div>
        <div className="summary-card critical">
          <span>Critical</span>
          <strong>{summary.critical}</strong>
        </div>
        <div className="summary-card high">
          <span>High</span>
          <strong>{summary.high}</strong>
        </div>
        <div className="summary-card medium">
          <span>Medium</span>
          <strong>{summary.medium}</strong>
        </div>
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
        <div className="state-box">No emergency requests found.</div>
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
                  <span className="id-chip">#{emergency.id}</span>
                  <span className="category-badge">{emergency.operational_safety_processing ? 'Safety processing' : 'Emergency'}</span>
                </div>
                <div className="card-ai-row">
                  <strong>AI Priority: {aiPriorityLabel(emergency)}</strong>
                  <span>Confidence: {confidenceLabel(aiPriorityConfidence(emergency))}</span>
                </div>
                {emergency.priority_classification_review_required ? (
                  <div className="review-banner">Manual priority review required</div>
                ) : null}
                <div className="meta-row muted">
                  <span>Source: {prioritySourceLabel(emergency)}</span>
                </div>
                <p className="card-message">{emergency.message}</p>
                <div className="meta-row">
                  <span>{finalPriorityLabel(emergency)}</span>
                  <span>{emergency.status}</span>
                </div>
                {safetyElevation(emergency) ? <div className="review-banner">{safetyElevation(emergency)}</div> : null}
                <div className="meta-row muted">
                  <span>{emergency.people_affected} affected</span>
                  <span>Location: {emergency.latitude ?? '—'}, {emergency.longitude ?? '—'}</span>
                </div>
                <div className="meta-row muted">
                  <span>Injured: {emergency.injured ? 'Yes' : 'No'} · Trapped: {emergency.trapped ? 'Yes' : 'No'}</span>
                  <span>Fire: {emergency.fire ? 'Yes' : 'No'} · Medical: {emergency.medical_emergency ? 'Yes' : 'No'}</span>
                </div>
                <div className="meta-row muted">
                  <span>{new Date(emergency.created_at).toLocaleString()}</span>
                </div>
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
