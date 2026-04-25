import React from 'react';
import { NSE_STOCKS, NOTIFICATIONS, generateSparkline } from '../data.js';
import { Icon } from '../icons.jsx';
import { Badge, Button, Modal } from '../ui.jsx';
import { Sparkline, Counter } from '../charts.jsx';
import { fetchStocks } from '../api.js';

const StockCard = ({ stock, onClick, sparklineSeed = 1 }) => {
  const positive = stock.change >= 0;
  const color = positive ? '#10b981' : '#ef4444';
  const trend = positive ? 1 : -1;
  const sparkData = React.useMemo(() => generateSparkline(sparklineSeed, 24, trend), [sparklineSeed, trend]);

  return (
    <div className="glass lift" onClick={onClick}
      style={{ padding: 18, cursor: 'pointer', position: 'relative', overflow: 'hidden' }}>
      {stock.buy && (
        <div style={{ position: 'absolute', top: 12, right: 12 }}>
          <Badge color="emerald" size="sm" icon="lightning">BUY</Badge>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 14 }}>
        <div style={{
          width: 38, height: 38, borderRadius: 10,
          background: `linear-gradient(135deg, ${color}33, ${color}11)`,
          border: `1px solid ${color}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 800, color, letterSpacing: '-0.02em',
        }}>
          {stock.ticker.slice(0, 2)}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: '-0.01em' }}>{stock.ticker}</div>
          <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.75)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{stock.name}</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <div className="mono" style={{ fontSize: 19, fontWeight: 700, letterSpacing: '-0.02em' }}>
            {stock.price.toFixed(2)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
            <Icon name={positive ? 'arrow-up' : 'arrow-down'} size={11} color={color} strokeWidth={3} />
            <span className="mono" style={{ fontSize: 12, fontWeight: 700, color }}>
              {Math.abs(stock.change).toFixed(2)}%
            </span>
            <span style={{ fontSize: 10, color: 'rgba(148,163,184,0.6)' }}>· KES</span>
          </div>
        </div>
        <Sparkline data={sparkData} color={color} width={70} height={28} />
      </div>
    </div>
  );
};

const StatCard = ({ label, value, sub, icon, color = '#10b981', accent }) => (
  <div className="glass lift" style={{ padding: 18, position: 'relative', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', top: -20, right: -20, width: 120, height: 120,
      background: `radial-gradient(circle, ${color}22, transparent 70%)`, pointerEvents: 'none' }} />
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
      <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{label}</span>
      <div style={{ width: 28, height: 28, borderRadius: 8, background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon name={icon} size={14} color={color} />
      </div>
    </div>
    <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.1 }} className={typeof value === 'number' ? 'mono' : ''}>
      {value}
    </div>
    {sub && <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.8)', marginTop: 6 }}>{sub}</div>}
    {accent}
  </div>
);

const NotificationCenter = () => {
  const [items, setItems] = React.useState(NOTIFICATIONS);
  const dismiss = (id) => setItems(items.filter(i => i.id !== id));
  const colors = { signal: '#10b981', alert: '#06b6d4', news: '#a78bfa', xp: '#fbbf24' };
  return (
    <div className="glass" style={{ padding: 18, position: 'sticky', top: 84 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Icon name="bell" size={16} color="#10b981" />
          <h3 style={{ fontSize: 14, fontWeight: 700 }}>Live Alerts</h3>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', animation: 'pulseGlow 2s infinite', display: 'inline-block' }} />
        </div>
        <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)' }}>{items.length}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 520, overflowY: 'auto', marginRight: -8, paddingRight: 8 }}>
        {items.map(n => (
          <div key={n.id} className="anim-fade-up" style={{
            padding: 12, background: 'rgba(15,23,42,0.5)',
            border: `1px solid ${colors[n.type]}22`, borderRadius: 10,
          }}>
            <div style={{ display: 'flex', gap: 10 }}>
              <div style={{ width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                background: `${colors[n.type]}22`,
                display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon name={n.icon} size={13} color={colors[n.type]} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  {n.ticker && <span className="mono" style={{ fontSize: 11, fontWeight: 700, color: colors[n.type] }}>{n.ticker}</span>}
                  <span style={{ fontSize: 10, color: 'rgba(148,163,184,0.6)' }}>{n.time}</span>
                </div>
                <div style={{ fontSize: 12, color: '#e2e8f0', lineHeight: 1.4 }}>{n.text}</div>
              </div>
              <button onClick={() => dismiss(n.id)} style={{ padding: 2 }}>
                <Icon name="x" size={12} color="rgba(148,163,184,0.5)" />
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && <div style={{ padding: 24, textAlign: 'center', fontSize: 12, color: 'rgba(148,163,184,0.6)' }}>All caught up ✨</div>}
      </div>
    </div>
  );
};

const XPCard = ({ user }) => {
  const pct = (user.xp / user.nextLevelXp) * 100;
  return (
    <div className="glass" style={{ padding: 18, background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.08))', borderColor: 'rgba(139,92,246,0.25)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div style={{ width: 44, height: 44, borderRadius: 12,
          background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 800, color: 'white',
          boxShadow: '0 8px 20px -4px rgba(139,92,246,0.5)',
        }}>L{user.level}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 700 }}>Bull Trader · Lvl {user.level}</div>
          <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)' }}><Counter value={user.xp} /> / {user.nextLevelXp} XP</div>
        </div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 999 }}>
          <Icon name="fire" size={12} color="#fbbf24" />
          <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: '#fbbf24' }}>{user.streak}</span>
        </div>
      </div>
      <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 999, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%',
          background: 'linear-gradient(90deg, #8b5cf6, #06b6d4)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 3s linear infinite',
          transition: 'width 600ms ease' }} />
      </div>
      <div style={{ marginTop: 10, fontSize: 11, color: 'rgba(203,213,225,0.8)', display: 'flex', alignItems: 'center', gap: 6 }}>
        <Icon name="target" size={11} color="#a78bfa" />
        Next: complete 1 backtest to earn 100 XP
      </div>
    </div>
  );
};

export const StockDrawer = ({ stock, onClose }) => {
  if (!stock) return null;
  const positive = stock.change >= 0;
  const color = positive ? '#10b981' : '#ef4444';
  const candles = React.useMemo(() => generateCandles(stock.ticker.charCodeAt(0), 40, stock.price), [stock]);
  return (
    <div onClick={onClose} className="anim-fade" style={{
      position: 'fixed', inset: 0, zIndex: 100, background: 'rgba(0,0,0,0.6)',
      backdropFilter: 'blur(6px)', display: 'flex', justifyContent: 'flex-end',
    }}>
      <div onClick={e => e.stopPropagation()} className="anim-slide" style={{
        width: 'min(560px, 95vw)', height: '100vh', overflow: 'auto',
        background: 'rgba(15,23,42,0.98)', backdropFilter: 'blur(24px)',
        borderLeft: '1px solid rgba(255,255,255,0.08)', padding: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: `${color}22`, border: `1px solid ${color}44`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14, fontWeight: 800, color }}>{stock.ticker.slice(0,2)}</div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>{stock.ticker}</div>
              <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.8)' }}>{stock.name} · {stock.sector}</div>
            </div>
          </div>
          <button onClick={onClose} style={{ padding: 8, borderRadius: 8, background: 'rgba(255,255,255,0.05)' }}>
            <Icon name="x" size={16} />
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, marginBottom: 20 }}>
          <div className="mono" style={{ fontSize: 38, fontWeight: 800, letterSpacing: '-0.03em' }}>
            {stock.price.toFixed(2)}
          </div>
          <div style={{ paddingBottom: 8 }}>
            <Badge color={positive ? 'emerald' : 'red'} icon={positive ? 'arrow-up' : 'arrow-down'}>
              {positive ? '+' : ''}{stock.change.toFixed(2)}%
            </Badge>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)', marginTop: 4 }}>KES · Today</div>
          </div>
        </div>
        <div className="glass" style={{ padding: 12, marginBottom: 16 }}>
          <CandlestickChart data={candles} width={490} height={240} showVolume={false} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 16 }}>
          {[
            { l: 'Volume', v: stock.vol },
            { l: 'AI Score', v: stock.ai, color: stock.ai >= 80 ? '#10b981' : stock.ai >= 60 ? '#fbbf24' : '#ef4444' },
            { l: 'Sector', v: stock.sector },
          ].map(s => (
            <div key={s.l} className="glass" style={{ padding: 12 }}>
              <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.7)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{s.l}</div>
              <div className="mono" style={{ fontSize: 16, fontWeight: 700, color: s.color || 'white' }}>{s.v}</div>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button variant="primary" size="lg" fullWidth icon="bell">Track {stock.ticker}</Button>
          <Button variant="secondary" size="lg" icon="plus">Log Position</Button>
        </div>
        <div style={{ marginTop: 12, padding: 10, background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.18)', borderRadius: 9, fontSize: 11, color: 'rgba(203,213,225,0.75)', lineHeight: 1.5 }}>
          <Icon name="shield" size={11} color="#fbbf24" /> Advisory only. We don't place orders — take signals to your broker.
        </div>
      </div>
    </div>
  );
};

const DashboardPage = ({ user, tier, openStock }) => {
  const [filter, setFilter] = React.useState('all');
  const [stocks, setStocks] = React.useState(NSE_STOCKS);

  React.useEffect(() => {
    fetchStocks()
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          const merged = data.map(live => {
            const fallback = NSE_STOCKS.find(s => s.ticker === live.ticker) || {};
            return { ...fallback, ...live, price: live.price ?? fallback.price, change: live.change ?? fallback.change };
          });
          setStocks(merged);
        }
      })
      .catch(() => { /* keep static fallback */ });
  }, []);

  const filtered = filter === 'buy' ? stocks.filter(s => s.buy) : filter === 'gainers' ? stocks.filter(s => s.change > 0) : stocks;
  const topGainer = stocks.reduce((a, b) => b.change > a.change ? b : a, stocks[0] || NSE_STOCKS[0]);
  const buyCount = stocks.filter(s => s.buy).length;

  return (
    <div className="anim-fade" style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px 60px' }}>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' }}>
            Hey {user.name.split(' ')[0]} 👋
          </h1>
          <p style={{ fontSize: 14, color: 'rgba(148,163,184,0.85)', marginTop: 6 }}>
            Market opens in <span className="mono" style={{ color: '#10b981', fontWeight: 700 }}>02:14:36</span> · NSE 20 at <span className="mono" style={{ fontWeight: 700 }}>2,184.50</span> <Badge color="emerald" size="sm">+1.42%</Badge>
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="secondary" icon="search">Search</Button>
          <Button variant="primary" icon="bell">Set Alert</Button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 20 }}>
        <StatCard label="Market Sentiment" value="Bullish" icon="trend" color="#10b981"
          accent={<div style={{ marginTop: 8 }}><Badge color="emerald" size="sm">9 of 14 up</Badge></div>} />
        <StatCard label="Top Gainer" value={topGainer.ticker} icon="rocket" color="#10b981"
          sub={<><span className="mono" style={{ color: '#10b981', fontWeight: 700 }}>+{topGainer.change.toFixed(2)}%</span> · KES {topGainer.price.toFixed(2)}</>} />
        <StatCard label="Total Stocks" value={<Counter value={stocks.length} />} icon="briefcase" color="#06b6d4" sub="Across 6 sectors" />
        <StatCard label="Buy Signals" value={<Counter value={buyCount} />} icon="lightning" color="#8b5cf6"
          accent={<div style={{ marginTop: 8 }}><Badge color="purple" size="sm" icon="brain">AI verified</Badge></div>} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 320px', gap: 20 }} className="dash-grid">
        <div>
          <XPCard user={user} />
          <div style={{ height: 20 }} />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>NSE Stocks</h2>
            <div style={{ display: 'flex', gap: 4, padding: 4, background: 'rgba(15,23,42,0.6)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)' }}>
              {[
                { id: 'all', label: 'All' },
                { id: 'gainers', label: 'Gainers' },
                { id: 'buy', label: 'Buy Signals' },
              ].map(t => (
                <button key={t.id} onClick={() => setFilter(t.id)}
                  style={{ padding: '6px 12px', borderRadius: 7, fontSize: 12, fontWeight: 600,
                    color: filter === t.id ? 'white' : 'rgba(148,163,184,0.7)',
                    background: filter === t.id ? 'rgba(16,185,129,0.15)' : 'transparent',
                    border: filter === t.id ? '1px solid rgba(16,185,129,0.3)' : '1px solid transparent' }}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
            {filtered.map((s, i) => (
              <div key={s.ticker} className="anim-fade-up" style={{ animationDelay: `${i * 30}ms` }}>
                <StockCard stock={s} onClick={() => openStock(s)} sparklineSeed={s.ticker.charCodeAt(0) + s.ticker.charCodeAt(1)} />
              </div>
            ))}
          </div>
        </div>
        <div className="sidebar"><NotificationCenter /></div>
      </div>

      <style>{`
        @media (max-width: 1024px) {
          .dash-grid { grid-template-columns: 1fr !important; }
          .sidebar { order: -1; }
        }
      `}</style>
    </div>
  );
};

export default DashboardPage;
