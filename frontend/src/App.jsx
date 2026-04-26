import React from 'react';
import { USER } from './data.js';
import { Navbar, Toast, Confetti } from './ui.jsx';
import LoginPage from './pages/Login.jsx';
import DashboardPage, { StockDrawer } from './pages/Dashboard.jsx';
import PortfolioPage from './pages/Portfolio.jsx';
import AnalyticsPage from './pages/Analytics.jsx';
import AccountPage from './pages/Account.jsx';
import NewsPage from './pages/News.jsx';
import AdminPage from './pages/Admin.jsx';
import { getToken, logout as apiLogout } from './api.js';

function App() {
  const [page, setPage] = React.useState(() => getToken() ? 'dashboard' : 'login');
  const [selectedStock, setSelectedStock] = React.useState(null);
  const [confetti, setConfetti] = React.useState(false);
  const [toast, setToast] = React.useState(null);
  const [tier, setTier] = React.useState('free');
  const [quota, setQuota] = React.useState({ used: 0, total: 10 });

  const QUOTA_TOTALS = { free: 10, pro: 50, club: 100, admin: 999 };

  React.useEffect(() => {
    document.body.dataset.tier = tier;
    setQuota(q => ({ ...q, total: QUOTA_TOTALS[tier] ?? 10 }));
  }, [tier]);

  const triggerConfetti = () => {
    setConfetti(true);
    setTimeout(() => setConfetti(false), 3500);
  };

  const addToast = (t) => setToast(t);

  const handleLogin = (authData = {}) => {
    if (authData.tier) setTier(authData.tier);
    setPage('dashboard');
    setQuota(q => ({ ...q, total: QUOTA_TOTALS[authData.tier] ?? q.total }));
    const firstName = USER.name.split(' ')[0];
    setTimeout(() => {
      setToast({ type: 'success', icon: 'check', title: `Welcome back, ${firstName}!`, message: '+10 XP for daily login · streak +1 day' });
    }, 600);
  };

  const handleLogout = () => {
    apiLogout();
    setPage('login');
  };

  const openStock = (s) => setSelectedStock(s);

  if (page === 'login') {
    return (
      <>
        <LoginPage onLogin={handleLogin} />
        {confetti && <Confetti />}
        <Toast toast={toast} onDismiss={() => setToast(null)} />
      </>
    );
  }

  return (
    <>
      <Navbar page={page} setPage={setPage} onLogout={handleLogout} user={USER} quota={quota} tier={tier} />
      <div key={page} className="anim-fade">
        {page === 'dashboard' && <DashboardPage user={USER} tier={tier} openStock={openStock} />}
        {page === 'portfolio' && <PortfolioPage user={USER} openStock={openStock} addToast={addToast} triggerConfetti={triggerConfetti} />}
        {page === 'analytics' && <AnalyticsPage tier={tier} addToast={addToast} triggerConfetti={triggerConfetti} />}
        {page === 'news' && <NewsPage openStock={openStock} />}
        {page === 'account' && <AccountPage user={USER} tier={tier} setTier={setTier} addToast={addToast} triggerConfetti={triggerConfetti} />}
        {page === 'admin' && <AdminPage addToast={addToast} setPage={setPage} />}
      </div>

      <StockDrawer stock={selectedStock} onClose={() => setSelectedStock(null)} />
      {confetti && <Confetti />}
      <Toast toast={toast} onDismiss={() => setToast(null)} />
    </>
  );
}

export default App;
