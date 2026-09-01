import { useEffect } from 'react';
import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';

const PRIORITY_COLORS = {
  CRITICAL: '#b91c1c',
  HIGH: '#ea580c',
  MEDIUM: '#d97706',
  LOW: '#15803d',
};

function isValidCoordinate(value, minimum, maximum) {
  return typeof value === 'number' && Number.isFinite(value) && value >= minimum && value <= maximum;
}

function MapViewport({ emergencies }) {
  const map = useMap();

  useEffect(() => {
    if (emergencies.length === 1) {
      map.setView([emergencies[0].latitude, emergencies[0].longitude], 12);
    } else if (emergencies.length > 1) {
      map.fitBounds(emergencies.map((emergency) => [emergency.latitude, emergency.longitude]), {
        padding: [32, 32],
        maxZoom: 13,
      });
    }
  }, [emergencies, map]);

  return null;
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : 'N/A';
}

export default function EmergencyMap({ emergencies, onSelectEmergency }) {
  const mappedEmergencies = emergencies.filter(
    (emergency) =>
      isValidCoordinate(emergency.latitude, -90, 90) &&
      isValidCoordinate(emergency.longitude, -180, 180),
  );

  return (
    <section className="map-panel" aria-label="Emergency locations map">
      <div className="map-heading">
        <div>
          <p className="eyebrow">Live Locations</p>
          <h2>Emergency map</h2>
        </div>
        <span className="map-count">{mappedEmergencies.length} mapped</span>
      </div>
      <div className="map-wrapper">
        <MapContainer center={[20, 0]} zoom={2} scrollWheelZoom className="emergency-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapViewport emergencies={mappedEmergencies} />
          {mappedEmergencies.map((emergency) => {
            const priority = emergency.priority_level || 'LOW';
            const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.LOW;

            return (
              <CircleMarker
                key={emergency.id}
                center={[emergency.latitude, emergency.longitude]}
                radius={priority === 'CRITICAL' ? 11 : 8}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.85, weight: 2 }}
                eventHandlers={{ click: () => onSelectEmergency(emergency.id) }}
              >
                <Popup>
                  <div className="map-popup">
                    <strong>Emergency #{emergency.id}</strong>
                    <span className={`priority-badge ${priority.toLowerCase()}`}>{priority}</span>
                    <p>{emergency.message}</p>
                    <dl>
                      <div><dt>Score</dt><dd>{emergency.priority_score}</dd></div>
                      <div><dt>People</dt><dd>{emergency.people_affected}</dd></div>
                      <div><dt>Injured</dt><dd>{emergency.injured ? 'Yes' : 'No'}</dd></div>
                      <div><dt>Trapped</dt><dd>{emergency.trapped ? 'Yes' : 'No'}</dd></div>
                      <div><dt>Medical</dt><dd>{emergency.medical_emergency ? 'Yes' : 'No'}</dd></div>
                      <div><dt>Status</dt><dd>{emergency.status}</dd></div>
                      <div><dt>Latitude</dt><dd>{emergency.latitude}</dd></div>
                      <div><dt>Longitude</dt><dd>{emergency.longitude}</dd></div>
                    </dl>
                    <small>Created {formatDate(emergency.created_at)}</small>
                    <button type="button" onClick={() => onSelectEmergency(emergency.id)}>
                      View full details
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
        {mappedEmergencies.length === 0 ? (
          <div className="map-empty">No emergency locations available.</div>
        ) : null}
      </div>
    </section>
  );
}
