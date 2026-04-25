const BASE = '/api';
const TOKEN_KEY = 'nse_access';
const REFRESH_KEY = 'nse_refresh';

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

const saveTokens = ({ access, refresh }) => {
  if (access) localStorage.setItem(TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
};

const authHdr = () => {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
};

const tryRefresh = async () => {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) { logout(); return false; }
    const d = await res.json();
    if (d.access) { localStorage.setItem(TOKEN_KEY, d.access); return true; }
  } catch { return false; }
  return false;
};

const apiFetch = async (path, opts = {}) => {
  const hdrs = { 'Content-Type': 'application/json', ...authHdr(), ...opts.headers };
  const res = await fetch(`${BASE}${path}`, { ...opts, headers: hdrs });
  if (res.status === 401) {
    if (await tryRefresh()) {
      return fetch(`${BASE}${path}`, {
        ...opts,
        headers: { 'Content-Type': 'application/json', ...authHdr(), ...opts.headers },
      });
    }
    logout();
    throw new Error('Session expired');
  }
  return res;
};

export const login = async (email, password) => {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  saveTokens(data);
  return data; // { access, refresh, tier, subscription_end }
};

export const register = async (email, password) => {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Registration failed');
  saveTokens(data);
  return data; // { access, refresh, tier }
};

export const telegramLogin = async (telegramId, firstName = '') => {
  const res = await fetch(`${BASE}/auth/telegram-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ telegram_id: String(telegramId), first_name: firstName }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Telegram login failed');
  saveTokens(data);
  return data; // { access, tier, is_pro }
};

export const fetchStocks = async () => {
  const res = await apiFetch('/stocks');
  if (!res.ok) throw new Error('Failed to fetch stocks');
  return res.json();
};

export const fetchPortfolio = async () => {
  const res = await apiFetch('/portfolio');
  if (!res.ok) throw new Error('Failed to fetch portfolio');
  return res.json();
};

export const addTrade = async (ticker, qty, avgCost) => {
  const res = await apiFetch('/portfolio/add', {
    method: 'POST',
    body: JSON.stringify({ ticker, qty, avg_cost: avgCost }),
  });
  if (!res.ok) throw new Error('Failed to add trade');
  return res.json();
};

export const removeTrade = async (ticker) => {
  const res = await apiFetch('/portfolio/remove', {
    method: 'POST',
    body: JSON.stringify({ ticker }),
  });
  if (!res.ok) throw new Error('Failed to remove trade');
  return res.json();
};

export const fetchQuota = async (telegramId) => {
  try {
    const res = await apiFetch(`/rate-limit/status/${telegramId}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};
