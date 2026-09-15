import BrandMark from '../components/BrandMark';
import NetworkGraph from '../components/NetworkGraph';
import useScrollReveal from '../hooks/useScrollReveal';
import { OPERATIONS_HASH, PRODUCT_LINE, PRODUCT_NAME } from '../brand';
import '../landing.css';

const STEPS = [
  { id: '01', title: 'SOS created', text: 'A victim records an emergency on the mobile app, including a message and available details.' },
  { id: '02', title: 'Stored locally', text: 'The report is persisted on the device in SQLite so it is not lost if the network is down.' },
  { id: '03', title: 'Relay discovered', text: 'Nearby devices can be discovered over Bluetooth Low Energy for short-range transfer.' },
  { id: '04', title: 'BLE transfer', text: 'The SOS payload is relayed to a neighboring device using store-and-forward hops.' },
  { id: '05', title: 'Server receives', text: 'When a device has connectivity, the report is submitted to the FastAPI backend over HTTP.' },
  { id: '06', title: 'Rescuer sees incident', text: 'The operations dashboard lists the emergency, maps its location when coordinates exist, and lets responders update status.' },
];

const TECHNOLOGIES = [
  {
    name: 'BLE',
    role: 'Bluetooth Low Energy is used on the mobile app to discover nearby devices and transfer SOS payloads when cellular service is unavailable.',
    icon: 'ble',
  },
  {
    name: 'SQLite',
    role: 'Emergencies are stored locally on the device and in the backend SQLite database so reports persist across offline and online periods.',
    icon: 'db',
  },
  {
    name: 'FastAPI',
    role: 'The Python backend exposes the emergency API used by this dashboard to list incidents and update their status.',
    icon: 'api',
  },
  {
    name: 'GPS / Location',
    role: 'The mobile app can attach latitude and longitude when location permission is granted, so mapped incidents appear on OpenStreetMap.',
    icon: 'gps',
  },
  {
    name: 'React + Vite',
    role: 'This rescue operations interface is a React application built with Vite for the web.',
    icon: 'react',
  },
  {
    name: 'Leaflet + OSM',
    role: 'Incident coordinates are drawn as markers on an OpenStreetMap basemap inside the operations view.',
    icon: 'map',
  },
];

function TechIcon({ name }) {
  if (name === 'ble') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 7.5 17 16l-6 5.5V2.5L17 8 7 16.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      </svg>
    );
  }
  if (name === 'db') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <ellipse cx="12" cy="6" rx="7" ry="3" fill="none" stroke="currentColor" strokeWidth="1.7" />
        <path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6" fill="none" stroke="currentColor" strokeWidth="1.7" />
        <path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3" fill="none" stroke="currentColor" strokeWidth="1.7" />
      </svg>
    );
  }
  if (name === 'api') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="4" y="5" width="16" height="14" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.7" />
        <path d="M8 12h8M8 9h5M8 15h4" stroke="currentColor" strokeWidth="1.7" />
      </svg>
    );
  }
  if (name === 'gps') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10Z" fill="none" stroke="currentColor" strokeWidth="1.7" />
        <circle cx="12" cy="11" r="2.2" fill="currentColor" />
      </svg>
    );
  }
  if (name === 'react') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="2" fill="currentColor" />
        <ellipse cx="12" cy="12" rx="9" ry="3.6" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(60 12 12)" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(-60 12 12)" fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3.5" y="5" width="17" height="14" rx="2" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <circle cx="9" cy="12" r="2" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M14 9.5h5M14 12h5M14 14.5h3" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function ArchitectureVisual() {
  const hops = [
    { label: 'Victim device', note: 'SOS + local store' },
    { label: 'BLE', note: 'Nearby relay' },
    { label: 'Relay device', note: 'Store-and-forward' },
    { label: 'HTTP', note: 'When online' },
    { label: 'Backend', note: 'FastAPI' },
    { label: 'Dashboard', note: PRODUCT_NAME },
  ];

  return (
    <ol className="architecture-flow">
      {hops.map((hop, index) => (
        <li key={hop.label}>
          <strong>{hop.label}</strong>
          <span>{hop.note}</span>
          {index < hops.length - 1 ? <b aria-hidden="true">↓</b> : null}
        </li>
      ))}
    </ol>
  );
}

export default function LandingPage() {
  useScrollReveal(true);

  return (
    <div className="landing-shell">
      <header className="landing-nav">
        <BrandMark />
        <nav>
          <a href="#problem">Problem</a>
          <a href="#how-it-works">How it works</a>
          <a className="nav-cta" href={OPERATIONS_HASH}>Open Rescue Operations</a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">{PRODUCT_NAME}</p>
          <h1>When Communication Fails, Rescue Can't.</h1>
          <p className="hero-lede">
            {PRODUCT_NAME} is a resilient emergency communication system designed to relay SOS
            information through nearby devices when conventional connectivity is unavailable.
            Reports are stored locally, forwarded over Bluetooth Low Energy, and shown to
            responders once they reach the FastAPI backend.
          </p>
          <div className="hero-actions">
            <a className="btn-primary" href={OPERATIONS_HASH}>Open Rescue Operations</a>
            <a className="btn-secondary" href="#how-it-works">How It Works</a>
          </div>
        </div>
        <div className="hero-visual glass-panel">
          <NetworkGraph />
          <p className="visual-caption">Conceptual relay path: victim, nearby relays, backend, rescue operations.</p>
        </div>
      </section>

      <section id="problem" className="split-section" data-reveal>
        <div className="split-visual glass-panel">
          <div className="scene scene-problem" aria-hidden="true">
            <span className="scene-tower" />
            <span className="scene-break" />
            <span className="scene-phone" />
          </div>
        </div>
        <div className="split-copy">
          <p className="eyebrow">The problem</p>
          <h2>Disaster conditions break the path from a victim to a rescuer.</h2>
          <p>
            Earthquakes, floods, and similar events often damage or overload cellular and
            internet service. An SOS that cannot leave the device never reaches a coordinator.
            {PRODUCT_NAME} is built around that gap: keep the report on the phone, then move it
            through nearby devices until a connection to the rescue server exists.
          </p>
        </div>
      </section>

      <section className="split-section reverse" data-reveal>
        <div className="split-copy">
          <p className="eyebrow">The solution</p>
          <h2>Store locally, relay nearby, then surface the incident to operations.</h2>
          <p>
            The working path in this project is conceptual and already implemented across the
            mobile app, communication simulation, backend, and this dashboard:
          </p>
          <ArchitectureVisual />
        </div>
        <div className="split-visual glass-panel">
          <NetworkGraph />
        </div>
      </section>

      <section className="split-section" data-reveal>
        <div className="split-visual glass-panel">
          <div className="scene scene-impact" aria-hidden="true">
            <span className="impact-node" />
            <span className="impact-node" />
            <span className="impact-node" />
            <span className="impact-ring" />
          </div>
        </div>
        <div className="split-copy">
          <p className="eyebrow">Resilience</p>
          <h2>Keep the SOS alive until a responder can act on it.</h2>
          <ul className="impact-list">
            <li>
              <strong>Local persistence.</strong> Emergencies stay in SQLite on the device until they can be synced.
            </li>
            <li>
              <strong>Store-and-forward.</strong> Messages hop between devices with hop count, TTL, and duplicate detection in the communication module and dashboard simulation.
            </li>
            <li>
              <strong>Nearby relay.</strong> BLE is used to move SOS data to a neighboring device.
            </li>
            <li>
              <strong>Location when available.</strong> Latitude and longitude are stored with the report and plotted on the operations map.
            </li>
            <li>
              <strong>Responder visibility.</strong> Coordinators can filter, inspect, and update incident status from this dashboard.
            </li>
          </ul>
        </div>
      </section>

      <section className="tech-section" data-reveal>
        <div className="section-heading">
          <p className="eyebrow">Stack in this project</p>
          <h2>Technologies actually used</h2>
          <p>Only components that exist in the current codebase are listed here.</p>
        </div>
        <div className="tech-grid">
          {TECHNOLOGIES.map((item) => (
            <article key={item.name} className="tech-card">
              <span className="tech-icon">
                <TechIcon name={item.icon} />
              </span>
              <h3>{item.name}</h3>
              <p>{item.role}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="how-section" data-reveal>
        <div className="section-heading">
          <p className="eyebrow">How it works</p>
          <h2>From SOS on the device to the operations map</h2>
          <p>This is a visual explanation of the existing workflow. It does not change how emergencies are processed.</p>
        </div>
        <ol className="how-grid">
          {STEPS.map((step) => (
            <li key={step.id}>
              <span>{step.id}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="final-cta" data-reveal>
        <p className="eyebrow">{PRODUCT_LINE}</p>
        <h2>Enter Rescue Operations</h2>
        <p>
          Open the command view to load live emergencies from the backend, inspect the map,
          and run the existing offline communication simulation.
        </p>
        <a className="btn-primary" href={OPERATIONS_HASH}>Enter Rescue Operations</a>
      </section>

      <footer className="landing-footer">
        <BrandMark compact />
        <span>Academic prototype for disconnected emergency reporting.</span>
      </footer>
    </div>
  );
}
