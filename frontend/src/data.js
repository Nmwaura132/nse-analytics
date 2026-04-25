export const NSE_STOCKS = [
  { ticker: 'SCOM',  name: 'Safaricom PLC',                price: 18.45, change: 2.34,  vol: '12.4M', sector: 'Telecom',    buy: true,  ai: 92 },
  { ticker: 'KCB',   name: 'KCB Group',                     price: 42.10, change: 1.82,  vol: '4.2M',  sector: 'Banking',   buy: true,  ai: 88 },
  { ticker: 'EQTY',  name: 'Equity Group Holdings',         price: 51.75, change: -0.96, vol: '3.8M',  sector: 'Banking',   buy: false, ai: 71 },
  { ticker: 'EABL',  name: 'East African Breweries',        price: 178.50, change: 3.21, vol: '890K',  sector: 'Consumer',  buy: true,  ai: 84 },
  { ticker: 'COOP',  name: 'Co-operative Bank',             price: 16.20, change: 0.62,  vol: '2.1M',  sector: 'Banking',   buy: false, ai: 64 },
  { ticker: 'BAT',   name: 'British American Tobacco K',    price: 412.00, change: -1.43, vol: '120K', sector: 'Consumer',  buy: false, ai: 58 },
  { ticker: 'ABSA',  name: 'Absa Bank Kenya',               price: 18.95, change: 1.07,  vol: '1.8M',  sector: 'Banking',   buy: false, ai: 73 },
  { ticker: 'KPLC',  name: 'Kenya Power & Lighting',        price: 4.32,  change: 4.85,  vol: '5.6M',  sector: 'Energy',    buy: true,  ai: 81 },
  { ticker: 'KEGN',  name: 'KenGen',                        price: 3.18,  change: -2.14, vol: '7.2M',  sector: 'Energy',    buy: false, ai: 49 },
  { ticker: 'BAMB',  name: 'Bamburi Cement',                price: 52.25, change: 0.48,  vol: '320K',  sector: 'Industrial', buy: false, ai: 67 },
  { ticker: 'JUB',   name: 'Jubilee Holdings',              price: 196.00, change: 1.55, vol: '85K',   sector: 'Insurance', buy: true,  ai: 79 },
  { ticker: 'NCBA',  name: 'NCBA Group',                    price: 51.50, change: 2.78,  vol: '1.4M',  sector: 'Banking',   buy: true,  ai: 86 },
  { ticker: 'STBK',  name: 'Stanbic Holdings',              price: 168.25, change: -0.74, vol: '210K', sector: 'Banking',   buy: false, ai: 62 },
  { ticker: 'SASN',  name: 'Sasini PLC',                    price: 22.80, change: 5.32,  vol: '420K',  sector: 'Agriculture', buy: true, ai: 90 },
];

export const HOLDINGS = [
  { ticker: 'SCOM', shares: 1200, avgCost: 16.20, current: 18.45 },
  { ticker: 'KCB',  shares: 450,  avgCost: 38.50, current: 42.10 },
  { ticker: 'EABL', shares: 80,   avgCost: 165.00, current: 178.50 },
  { ticker: 'KPLC', shares: 3000, avgCost: 4.10,  current: 4.32 },
  { ticker: 'EQTY', shares: 200,  avgCost: 54.20, current: 51.75 },
];

export const USER = {
  name: 'Kaniel Mwangi',
  initials: 'KM',
  email: 'kaniel@nseanalytics.co.ke',
  joined: 'March 2025',
  telegram: '@kaniel_trades',
  telegramLinked: true,
  streak: 12,
  xp: 2840,
  level: 7,
  nextLevelXp: 3500,
  badges: ['First Trade', 'Week Streak', 'Bull Run', 'AI Apprentice'],
};

export const NOTIFICATIONS = [
  { id: 1, type: 'signal', ticker: 'SCOM', text: 'Strong buy signal — RSI bounced from 32', time: '2m ago', icon: 'trend' },
  { id: 2, type: 'alert',  ticker: 'EABL', text: 'Crossed 50-day MA — bullish breakout', time: '14m ago', icon: 'bell' },
  { id: 3, type: 'news',   ticker: 'KCB',  text: 'Q1 earnings beat est. by 12%', time: '1h ago', icon: 'news' },
  { id: 4, type: 'xp',     ticker: null,    text: 'Daily streak +1 → 12 days! Earned 50 XP', time: '3h ago', icon: 'xp' },
  { id: 5, type: 'signal', ticker: 'SASN', text: 'Volume spike: 3.2× avg — watch closely', time: '5h ago', icon: 'trend' },
];

export const NEWS = [
  { id: 1, headline: 'CBK holds rate at 11.25% — banks expected to benefit', source: 'Business Daily', time: '32m', tag: 'Macro' },
  { id: 2, headline: 'Safaricom M-Pesa revenue crosses KES 100B milestone', source: 'The Standard', time: '2h', tag: 'SCOM' },
  { id: 3, headline: 'EABL to expand Tanzania ops with KES 8B investment', source: 'Reuters', time: '4h', tag: 'EABL' },
  { id: 4, headline: 'NSE 20 Index closes at 7-month high', source: 'NSE', time: '6h', tag: 'Market' },
  { id: 5, headline: 'Sasini posts strong Q1 — tea exports drive 24% revenue jump', source: 'Business Daily', time: '8h', tag: 'SASN' },
  { id: 6, headline: 'KenGen secures KES 12B for geothermal expansion', source: 'The Star', time: '12h', tag: 'KEGN' },
  { id: 7, headline: 'NCBA Group declares interim dividend of KES 2.25', source: 'Nation', time: '1d', tag: 'NCBA' },
  { id: 8, headline: 'Equity Bank launches AI-powered credit scoring', source: 'Reuters', time: '1d', tag: 'EQTY' },
];

export function generateCandles(seed = 1, count = 60, basePrice = 18) {
  const data = [];
  let price = basePrice;
  let rng = seed * 9301;
  const r = () => { rng = (rng * 9301 + 49297) % 233280; return rng / 233280; };
  for (let i = 0; i < count; i++) {
    const open = price;
    const change = (r() - 0.48) * basePrice * 0.04;
    const close = Math.max(0.5, open + change);
    const high = Math.max(open, close) + r() * basePrice * 0.015;
    const low = Math.min(open, close) - r() * basePrice * 0.015;
    data.push({ open, close, high, low, vol: Math.floor(r() * 1000000 + 200000) });
    price = close;
  }
  return data;
}

export function generateSparkline(seed, points = 24, trend = 0) {
  let rng = seed * 7919;
  const r = () => { rng = (rng * 9301 + 49297) % 233280; return rng / 233280; };
  const data = [];
  let v = 50;
  for (let i = 0; i < points; i++) {
    v += (r() - 0.5 + trend * 0.1) * 6;
    v = Math.max(10, Math.min(90, v));
    data.push(v);
  }
  return data;
}
