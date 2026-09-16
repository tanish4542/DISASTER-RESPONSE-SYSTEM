import { useEffect, useMemo, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import '../operations.css';
import { getEmergencies, updateEmergencyCategory, updateEmergencyStatus } from '../services/api';
import EmergencyMap from '../components/EmergencyMap';
import CommunicationDemo from '../components/CommunicationDemo';
import BrandMark from '../components/BrandMark';
import { PRODUCT_LINE, PRODUCT_NAME } from '../brand';

const STATUS_OPTIONS = ['PENDING', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'];
const PRIORITY_FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const CATEGORY_OPTIONS = [
  'NATURAL DISASTER',
  'HEALTH / SOCIETAL',
  'INFRASTRUCTURE / TRANSPORT',
  'OTHER',
];

function OperationsDashboard() {
  const [emergencies, setEmergencies] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [savingId, setSavingId] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');

  const loadEmergencies = async () => {
    setLoading(true);
    setError('');
    setStatusMessage('');

    try {
      const data = await getEmergencies();
      setEmergencies(Array.isArray(data) ? data : []);
      if (!selectedId && data?.length) {
        setSelectedId(data[0].id);
      }
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

  const selectedEmergency =
    filteredEmergencies.find((emergency) => emergency.id === selectedId) ||
    emergencies.find((emergency) => emergency.id === selectedId) ||
    null;

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

  const handleStatusChange = async (id, nextStatus) => {
    setSavingId(id);
    setStatusMessage('');

    try {
      await updateEmergencyStatus(id, nextStatus);
      await loadEmergencies();
      setStatusMessage(`Status updated to ${nextStatus}.`);
    } catch (updateError) {
      setStatusMessage('Unable to update emergency status.');
    } finally {
      setSavingId(null);
    }
  };

  const handleCategoryChange = async (id, nextCategory) => {
    setSavingId(id);
    setStatusMessage('');

    try {
      await updateEmergencyCategory(id, nextCategory);
      await loadEmergencies();
      setStatusMessage(`Category updated to ${nextCategory}.`);
    } catch (updateError) {
      setStatusMessage('Unable to update emergency category.');
    } finally {
      setSavingId(null);
    }
  };

  const priorityClass = (priority) => `priority-badge ${String(priority || 'LOW').toLowerCase()}`;
  const confidenceLabel = (value) => (
    typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'
  );
  const relevanceLabel = (value) => (
    value === true ? 'Relevant' : value === false ? 'Not Relevant' : 'Unavailable'
  );
  const typeLabel = (value) => value ? String(value).replaceAll('_', ' ').toUpperCase() : 'Unavailable';
  const categoryLabel = (emergency) => (
    emergency.operational_category || (emergency.classification_review_required ? 'Manual review required' : 'Unavailable')
  );
  const statusFailed = statusMessage === 'Unable to update emergency status.';

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

      {statusMessage ? (
        <div className={`status-message ${statusFailed ? 'status-failed' : ''}`}>{statusMessage}</div>
      ) : null}

      <EmergencyMap emergencies={emergencies} onSelectEmergency={setSelectedId} />

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
              <button
                type="button"
                key={emergency.id}
                className={`emergency-card ${String(emergency.priority_level || '').toLowerCase()} ${selectedEmergency?.id === emergency.id ? 'selected' : ''}`}
                onClick={() => setSelectedId(emergency.id)}
              >
                <div className="card-toprow">
                  <span className="id-chip">#{emergency.id}</span>
                  <span className="category-badge">{categoryLabel(emergency)}</span>
                </div>
                <div className="card-ai-row">
                  <strong>{typeLabel(emergency.ai_disaster_type)}</strong>
                  <span>AI confidence: {confidenceLabel(emergency.ai_disaster_type_confidence)}</span>
                </div>
                <p className="card-message">{emergency.message}</p>
                <div className="meta-row">
                  <span>Priority: {emergency.priority_level} · Score: {emergency.priority_score}</span>
                  <span>{emergency.status}</span>
                </div>
                <div className="meta-row muted">
                  <span>{emergency.people_affected} affected</span>
                  <span>{new Date(emergency.created_at).toLocaleString()}</span>
                </div>
              </button>
            ))}
          </div>

          <aside className="details-panel">
            {selectedEmergency ? (
              <>
                <div className="details-header">
                  <h2>Emergency #{selectedEmergency.id}</h2>
                  <span className={priorityClass(selectedEmergency.priority_level)}>
                    {selectedEmergency.priority_level}
                  </span>
                </div>

                <div className="detail-block">
                  <h3>EMERGENCY</h3>
                  <p>{selectedEmergency.message}</p>
                  <small>Created {new Date(selectedEmergency.created_at).toLocaleString()} · Updated {new Date(selectedEmergency.updated_at).toLocaleString()}</small>
                </div>

                <section className="detail-section">
                  <h3>LOCATION</h3>
                  <div className="detail-grid">
                    <div><span>Latitude</span><strong>{selectedEmergency.latitude ?? 'Location unavailable'}</strong></div>
                    <div><span>Longitude</span><strong>{selectedEmergency.longitude ?? 'Location unavailable'}</strong></div>
                  </div>
                  {selectedEmergency.latitude != null && selectedEmergency.longitude != null ? (
                    <p className="detail-note">Location is shown on the incident map above.</p>
                  ) : null}
                </section>

                <section className="detail-section">
                  <h3>IMPACT</h3>
                  <div className="detail-grid">
                    <div><span>People Affected</span><strong>{selectedEmergency.people_affected}</strong></div>
                    <div><span>Injured</span><strong>{selectedEmergency.injured ? 'Yes' : 'No'}</strong></div>
                    <div><span>Trapped</span><strong>{selectedEmergency.trapped ? 'Yes' : 'No'}</strong></div>
                    <div><span>Fire</span><strong>{selectedEmergency.fire ? 'Yes' : 'No'}</strong></div>
                    <div><span>Medical Emergency</span><strong>{selectedEmergency.medical_emergency ? 'Yes' : 'No'}</strong></div>
                  </div>
                </section>

                <section className="detail-section ai-analysis" aria-labelledby="ai-analysis-heading">
                  <div className="ai-analysis-header">
                    <h3 id="ai-analysis-heading">AI ANALYSIS</h3>
                    <span>{selectedEmergency.classification_source || 'Unavailable'}</span>
                  </div>
                  <div className="ai-analysis-grid">
                    <div><span>Category</span><strong>{categoryLabel(selectedEmergency)}</strong></div>
                    <div><span>AI Disaster Type</span><strong>{typeLabel(selectedEmergency.ai_disaster_type)}</strong></div>
                    <div><span>AI Confidence</span><strong>{confidenceLabel(selectedEmergency.ai_disaster_type_confidence)}</strong></div>
                    <div><span>Classification source</span><strong>{selectedEmergency.classification_source || 'Unavailable'}</strong></div>
                    <div><span>Manual review</span><strong>{selectedEmergency.classification_review_required ? 'Required' : 'No'}</strong></div>
                    <div><span>AI Urgency</span><strong>{selectedEmergency.ai_urgency ?? 'Unavailable'}</strong></div>
                    <div><span>Urgency confidence</span><strong>{confidenceLabel(selectedEmergency.ai_urgency_confidence)}</strong></div>
                    <div><span>Relevance</span><strong>{relevanceLabel(selectedEmergency.ai_relevant)}</strong></div>
                    <div><span>Relevance confidence</span><strong>{confidenceLabel(selectedEmergency.ai_relevance_confidence)}</strong></div>
                  </div>
                  <div className="ai-reason">
                    <strong>Why this classification?</strong>
                    <p>{selectedEmergency.ai_classification_reason || 'Unavailable'}</p>
                  </div>
                  {selectedEmergency.classification_review_required ? (
                    <div className="manual-review">
                      <strong>AI CLASSIFICATION REQUIRES REVIEW</strong>
                      <p>Select the operational category for this emergency.</p>
                    </div>
                  ) : null}
                  <div className="category-actions">
                    {CATEGORY_OPTIONS.map((category) => (
                      <button
                        key={category}
                        type="button"
                        className={selectedEmergency.operational_category === category ? 'category-button selected' : 'category-button'}
                        onClick={() => handleCategoryChange(selectedEmergency.id, category)}
                        disabled={savingId === selectedEmergency.id}
                      >
                        {category}
                      </button>
                    ))}
                  </div>
                  <p className="ai-analysis-note">
                    AI classification and urgency are analysis. Priority score and level remain the existing rescue priority.
                  </p>
                </section>

                <section className="detail-section">
                  <h3>PRIORITY</h3>
                  <div className="detail-grid">
                    <div><span>Priority Score</span><strong>{selectedEmergency.priority_score}</strong></div>
                    <div><span>Priority Level</span><strong>{selectedEmergency.priority_level}</strong></div>
                  </div>
                </section>

                <div className="status-control">
                  <label htmlFor="status-update">Update status</label>
                  <select
                    id="status-update"
                    value={selectedEmergency.status}
                    onChange={(event) => handleStatusChange(selectedEmergency.id, event.target.value)}
                    disabled={savingId === selectedEmergency.id}
                  >
                    {STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </div>
                <p className="detail-note">Current status: {selectedEmergency.status}</p>
              </>
            ) : (
              <div className="state-box">Select an emergency to view details.</div>
            )}
          </aside>
        </div>
      )}

      <CommunicationDemo />
    </div>
  );
}

export default OperationsDashboard;
