import { useEffect, useMemo, useState } from 'react';
import './App.css';
import 'leaflet/dist/leaflet.css';
import { getEmergencies, updateEmergencyStatus } from './services/api';
import EmergencyMap from './components/EmergencyMap';
import CommunicationDemo from './components/CommunicationDemo';

const STATUS_OPTIONS = ['PENDING', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'];
const PRIORITY_FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

function App() {
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

  const priorityClass = (priority) => `priority-badge ${String(priority || 'LOW').toLowerCase()}`;

  return (
    <div className="dashboard-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Rescue Operations</p>
          <h1>🚨 Disaster Response Dashboard</h1>
          <p className="subtitle">Monitor, prioritize and manage emergency requests.</p>
        </div>
        <button type="button" className="refresh-button" onClick={loadEmergencies}>
          Refresh
        </button>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span>Total Emergencies</span>
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

      {statusMessage ? <div className="status-message">{statusMessage}</div> : null}

      <EmergencyMap emergencies={emergencies} onSelectEmergency={setSelectedId} />
      <CommunicationDemo />

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
            {filteredEmergencies.map((emergency) => (
              <button
                type="button"
                key={emergency.id}
                className={`emergency-card ${selectedEmergency?.id === emergency.id ? 'selected' : ''}`}
                onClick={() => setSelectedId(emergency.id)}
              >
                <div className="card-toprow">
                  <span className="id-chip">#{emergency.id}</span>
                  <span className={priorityClass(emergency.priority_level)}>{emergency.priority_level}</span>
                </div>
                <p className="card-message">{emergency.message}</p>
                <div className="meta-row">
                  <span>Score: {emergency.priority_score}</span>
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
                  <h3>Incident</h3>
                  <p>{selectedEmergency.message}</p>
                </div>

                <div className="detail-grid">
                  <div><span>Priority Score</span><strong>{selectedEmergency.priority_score}</strong></div>
                  <div><span>People Affected</span><strong>{selectedEmergency.people_affected}</strong></div>
                  <div><span>Injured</span><strong>{selectedEmergency.injured ? 'Yes' : 'No'}</strong></div>
                  <div><span>Trapped</span><strong>{selectedEmergency.trapped ? 'Yes' : 'No'}</strong></div>
                  <div><span>Fire</span><strong>{selectedEmergency.fire ? 'Yes' : 'No'}</strong></div>
                  <div><span>Medical</span><strong>{selectedEmergency.medical_emergency ? 'Yes' : 'No'}</strong></div>
                  <div><span>Latitude</span><strong>{selectedEmergency.latitude ?? 'N/A'}</strong></div>
                  <div><span>Longitude</span><strong>{selectedEmergency.longitude ?? 'N/A'}</strong></div>
                  <div><span>Created</span><strong>{new Date(selectedEmergency.created_at).toLocaleString()}</strong></div>
                </div>

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
              </>
            ) : (
              <div className="state-box">Select an emergency to view details.</div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

export default App;
