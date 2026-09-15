import { useEffect, useState } from 'react';
import LandingPage from './pages/LandingPage';
import OperationsDashboard from './pages/OperationsDashboard';
import { OPERATIONS_HASH } from './brand';

function currentView() {
  return window.location.hash === OPERATIONS_HASH ? 'operations' : 'home';
}

function App() {
  const [view, setView] = useState(currentView);

  useEffect(() => {
    const syncView = () => setView(currentView());
    window.addEventListener('hashchange', syncView);
    return () => window.removeEventListener('hashchange', syncView);
  }, []);

  return view === 'operations' ? <OperationsDashboard /> : <LandingPage />;
}

export default App;
