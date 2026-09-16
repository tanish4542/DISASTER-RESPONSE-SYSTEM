import { useEffect, useState } from 'react';
import LandingPage from './pages/LandingPage';
import OperationsDashboard from './pages/OperationsDashboard';
import ResolvedEmergencies from './pages/ResolvedEmergencies';
import EmergencyDetails from './pages/EmergencyDetails';
import { OPERATIONS_HASH } from './brand';

function currentView() {
  const hash = window.location.hash;
  if (hash.startsWith('#emergency/')) return 'details';
  if (hash === '#resolved') return 'resolved';
  return hash === OPERATIONS_HASH ? 'operations' : 'home';
}

function App() {
  const [view, setView] = useState(currentView);

  useEffect(() => {
    const syncView = () => setView(currentView());
    window.addEventListener('hashchange', syncView);
    return () => window.removeEventListener('hashchange', syncView);
  }, []);

  if (view === 'details') {
    const id = window.location.hash.split('/')[1];
    return <EmergencyDetails id={id} />;
  }
  if (view === 'resolved') return <ResolvedEmergencies />;
  return view === 'operations' ? <OperationsDashboard /> : <LandingPage />;
}

export default App;
