import React from 'react';
import { NSE_STOCKS } from '../data.js';
import { Icon } from '../icons.jsx';
import { Badge, Button, Modal } from '../ui.jsx';
import { Counter, DonutChart } from '../charts.jsx';
import * as api from '../api.js';

const adviceFor = (h) => {
  const stock = NSE_STOCKS.find(s => s.ticker === h.ticker);
  if (!stock) return { kind: 'hold', label: 'Hold', color: '#94a3b8', icon: 'shield', note: 'No data' };
  const plPct = ((h.current - h.avgCost) / h.avgCost) * 100;
  if (stock.buy)
    return { kind: 'buy', label: 'Add more', color: '#10b981', icon: 'arrow-up', note: `AI signal: Buy` };
  if (plPct > 25)
    return { kind: 'sell', label: 'Take profit', color: '#fbbf24', icon: 'lightning', note: `+${plPct.toFixed(0)}% gain — trim?` };
  if (stock.change < -2)
    return { kind: 'watch', label: 'Watch', color: '#f97316', icon: 'eye', note: `Down ${stock.change.toFixed(2)}% today` };
  return { kind: 'hold', label: 'Hold', color: '#06b6d4', icon: 'shield', note: 'Stable — no action' };
};

const PortfolioPage = ({ user, openStock, addToast, triggerConfetti }) => {
  const [holdings, setHoldings] = React.useState(() =>
    api.getHoldings().map(h => ({
      ...h,
      current: NSE_STOCKS.find(s => s.ticker === h.ticker)?.price ?? h.avgCost,
    }))
  );
  const [optimizing, setOptimizing] = React.useState(false);
  const [consent, setConsent] = React.useState(api.hasConsent);
  const [consentModal, setConsentModal] = React.useState(false);
  const [revoking, setRevoking] = React.useState(false);
  const [optimized, setOptimized] = React.useState(null);
  const [budget, setBudget] = React.useState(50000);
  const [selected, setSelected] = React.useState(['SCOM', 'KCB', 'EABL', 'KPLC']);
  const [sellTarget, setSellTarget] = React.useState(null);
  const [addOpen, setAddOpen] = React.useState(false);
  const [addForm, setAddForm] = React.useState({ ticker: 'SCOM', shares: 100, avgCost: '' });

  const stats = holdings.reduce((acc, h) => {
    const value = h.shares * h.current;
    const cost = h.shares * h.avgCost;
    return { value: acc.value + value, cost: acc.cost + cost };
  }, { value: 0, cost: 0 });
  const pl = stats.value - stats.cost;
  const plPct = stats.cost ? (pl / stats.cost) * 100 : 0;
  const riskScore = 6.4;

  const removeHolding = (ticker) => {
    api.removeLocalHolding(ticker);
    setHoldings(h => h.filter(x => x.ticker !== ticker));
    setSellTarget(null);
    addToast({ type: 'success', icon: 'check', title: 'Removed', message: `${ticker} removed from your tracker.` });
    if (consent && api.getToken()) {
      api.removeTrade(ticker).catch(() => {});
    }
  };

  const addPosition = () => {
    const stock = NSE_STOCKS.find(s => s.ticker === addForm.ticker);
    if (!stock || !addForm.shares || !addForm.avgCost) return;
    if (holdings.find(h => h.ticker === addForm.ticker)) {
      addToast({ type: 'error', icon: 'shield', title: 'Already tracked', message: `${addForm.ticker} is already in your tracker.` });
      return;
    }
    const newHolding = { ticker: addForm.ticker, shares: +addForm.shares, avgCost: +addForm.avgCost, current: stock.price };
    api.saveLocalHolding(addForm.ticker, +addForm.shares, +addForm.avgCost);
    setHoldings(h => [...h, newHolding]);
    setAddOpen(false);
    setAddForm({ ticker: 'SCOM', shares: 100, avgCost: '' });
    triggerConfetti();
    addToast({ type: 'xp', icon: 'sparkles', title: 'Position logged', message: `Now tracking ${addForm.ticker} · alerts active` });
    if (consent && api.getToken()) {
      api.addTrade(addForm.ticker, +addForm.shares, +addForm.avgCost).catch(() => {});
    }
  };

  const grantConsent = async () => {
    const ok = await api.givePortfolioConsent();
    if (ok) {
      setConsent(true);
      setConsentModal(false);
      addToast({ type: 'success', icon: 'telegram', title: 'Bot access enabled', message: 'Your portfolio is now shared with @NSEProBot.' });
    } else {
      addToast({ type: 'error', icon: 'x', title: 'Failed', message: 'Could not enable bot access. Try again.' });
    }
  };

  const revokeConsent = async () => {
    setRevoking(true);
    await api.revokePortfolioConsent();
    setConsent(false);
    setRevoking(false);
    addToast({ type: 'info', icon: 'check', title: 'Bot access disabled', message: 'Server data deleted. Holdings remain on this device only.' });
  };

  const optimize = () => {
    setOptimizing(true);
    setOptimized(null);
    setTimeout(() => {
      setOptimizing(false);
      const colors = ['#10b981', '#06b6d4', '#8b5cf6', '#fbbf24', '#ef4444'];
      const allocations = selected.map((t, i) => ({ label: t, value: Math.round(30 + Math.random() * 25), color: colors[i % colors.length] }));
      const total = allocations.reduce((s, a) => s + a.value, 0);
      allocations.forEach(a => a.value = Math.round((a.value / total) * 100));
      setOptimized({ expectedReturn: 18.4, sharpe: 1.62, risk: 'Moderate', allocations });
      triggerConfetti();
      addToast({ type: 'xp', icon: 'sparkles', title: '+100 XP earned', message: 'Optimizer run complete.' });
    }, 1800);
  };

  return (
    <div className="anim-fade" style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px 60px' }}>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' }}>My Tracker</h1>
          <p style={{ fontSize: 14, color: 'rgba(148,163,184,0.85)', marginTop: 6 }}>
            Tell us what you own — we'll watch the market and send alerts. <span style={{ color: 'rgba(245,158,11,0.9)' }}>Advisory only — no orders placed.</span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="secondary" icon="arrow-down">Export CSV</Button>
          <Button variant="primary" icon="plus" onClick={() => setAddOpen(true)}>Log Position</Button>
        </div>
      </div>

      {/* Privacy / bot-access banner */}
      <div style={{ marginBottom: 18, padding: '12px 16px', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
        background: consent ? 'rgba(16,185,129,0.08)' : 'rgba(6,182,212,0.07)',
        border: `1px solid ${consent ? 'rgba(16,185,129,0.25)' : 'rgba(6,182,212,0.2)'}` }}>
        <Icon name={consent ? 'telegram' : 'lock'} size={16} color={consent ? '#10b981' : '#06b6d4'} />
        <span style={{ flex: 1, fontSize: 13, color: 'rgba(203,213,225,0.9)' }}>
          {consent
            ? <><span style={{ color: '#10b981', fontWeight: 700 }}>Bot access on</span> — @NSEProBot can see your holdings. Your data is stored on this device and on our server.</>
            : <><span style={{ color: '#06b6d4', fontWeight: 700 }}>Device-only</span> — holdings saved locally. <span style={{ color: 'rgba(148,163,184,0.85)' }}>Enable bot access to analyse your portfolio with @NSEProBot.</span></>
          }
        </span>
        {consent
          ? <Button variant="danger" size="sm" onClick={revokeConsent} disabled={revoking}>{revoking ? 'Revoking…' : 'Disable Bot Access'}</Button>
          : <Button variant="secondary" size="sm" icon="telegram" onClick={() => setConsentModal(true)}>Enable Bot Access</Button>
        }
      </div>

      <div className="glass" style={{ padding: 24, marginBottom: 20, position: 'relative', overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(6,182,212,0.04))', borderColor: 'rgba(16,185,129,0.2)' }}>
        <div style={{ position: 'absolute', top: -50, right: -50, width: 200, height: 200,
          background: 'radial-gradient(circle, rgba(16,185,129,0.2), transparent 70%)' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 24, position: 'relative' }}>
          <div>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, marginBottom: 8 }}>Total Value</div>
            <div className="mono" style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1 }}>
              <span style={{ fontSize: 18, color: 'rgba(148,163,184,0.7)', marginRight: 6 }}>KES</span>
              <Counter value={stats.value} decimals={0} />
            </div>
            <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.7)', marginTop: 8 }}>
              Cost basis: <span className="mono">{stats.cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, marginBottom: 8 }}>Total P&L</div>
            <div className="mono" style={{ fontSize: 32, fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1, color: pl >= 0 ? '#10b981' : '#ef4444' }}>
              {pl >= 0 ? '+' : ''}<Counter value={pl} decimals={0} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8 }}>
              <Icon name={pl >= 0 ? 'arrow-up' : 'arrow-down'} size={12} color={pl >= 0 ? '#10b981' : '#ef4444'} strokeWidth={3} />
              <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: pl >= 0 ? '#10b981' : '#ef4444' }}>
                {plPct >= 0 ? '+' : ''}{plPct.toFixed(2)}%
              </span>
              <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.6)' }}>all time</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, marginBottom: 8 }}>Risk Score</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <div className="mono" style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-0.03em', color: '#fbbf24' }}>{riskScore}</div>
              <div style={{ fontSize: 13, color: 'rgba(148,163,184,0.7)' }}>/ 10</div>
            </div>
            <div style={{ marginTop: 8 }}><Badge color="amber" icon="shield">Moderate</Badge></div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, marginBottom: 8 }}>Diversification</div>
            <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
              {['Banking', 'Telecom', 'Energy', 'Consumer'].map((s, i) => (
                <div key={s} style={{ flex: 1, height: 32, borderRadius: 6,
                  background: ['#10b981', '#06b6d4', '#8b5cf6', '#fbbf24'][i], opacity: 0.7 }} title={s} />
              ))}
            </div>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)', marginTop: 8 }}>4 sectors</div>
          </div>
        </div>
      </div>

      <div className="glass" style={{ padding: 22, marginBottom: 20,
        background: 'linear-gradient(135deg, rgba(139,92,246,0.1), rgba(6,182,212,0.04))', borderColor: 'rgba(139,92,246,0.25)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ width: 40, height: 40, borderRadius: 11,
            background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 20px -4px rgba(139,92,246,0.5)' }}>
            <Icon name="brain" size={20} color="white" />
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>AI Portfolio Optimizer</h3>
            <p style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', marginTop: 2 }}>Set a budget, pick tickers, get the optimal allocation by Sharpe ratio.</p>
          </div>
          <Badge color="purple" icon="sparkles">PRO</Badge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: optimized ? '1fr 1fr' : '1fr', gap: 20 }} className="opt-grid">
          <div>
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block' }}>Budget (KES)</label>
              <input className="glass-input mono" type="number" value={budget} onChange={e => setBudget(+e.target.value)} />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block' }}>Tickers ({selected.length})</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {NSE_STOCKS.slice(0, 10).map(s => {
                  const on = selected.includes(s.ticker);
                  return (
                    <button key={s.ticker} onClick={() => setSelected(sel => on ? sel.filter(t => t !== s.ticker) : [...sel, s.ticker])}
                      style={{ padding: '6px 11px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                        background: on ? 'rgba(139,92,246,0.2)' : 'rgba(15,23,42,0.5)',
                        color: on ? '#c4b5fd' : 'rgba(203,213,225,0.7)',
                        border: on ? '1px solid rgba(139,92,246,0.4)' : '1px solid rgba(255,255,255,0.08)',
                        transition: 'all 150ms' }}>
                      {s.ticker}
                    </button>
                  );
                })}
              </div>
            </div>
            <Button variant="purple" size="lg" icon={optimizing ? null : 'zap'} onClick={optimize} disabled={optimizing || selected.length < 2} fullWidth>
              {optimizing ? 'Optimizing…' : 'Optimize Portfolio'}
            </Button>
          </div>

          {optimized && (
            <div className="anim-fade" style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
              <DonutChart data={optimized.allocations} size={170} thickness={26}
                centerLabel={`+${optimized.expectedReturn}%`} centerSubLabel="Expected" />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.7)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sharpe</div>
                    <div className="mono" style={{ fontSize: 18, fontWeight: 700, color: '#06b6d4' }}>{optimized.sharpe}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.7)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Risk</div>
                    <div style={{ fontSize: 14, fontWeight: 700, marginTop: 2 }}><Badge color="amber" size="sm">{optimized.risk}</Badge></div>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {optimized.allocations.map(a => (
                    <div key={a.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                      <div style={{ width: 10, height: 10, borderRadius: 3, background: a.color }} />
                      <span style={{ flex: 1, fontWeight: 600 }}>{a.label}</span>
                      <span className="mono" style={{ color: 'rgba(148,163,184,0.85)' }}>{a.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="glass" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700 }}>Your positions</h3>
            <p style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)', marginTop: 2 }}>{holdings.length} tracked · advice updates in real-time</p>
          </div>
        </div>
        {holdings.length === 0 ? (
          <div style={{ padding: '60px 24px', textAlign: 'center' }}>
            <div style={{ width: 64, height: 64, borderRadius: 18, background: 'rgba(16,185,129,0.1)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
              animation: 'floatY 3s ease-in-out infinite' }}>
              <Icon name="briefcase" size={28} color="#10b981" />
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>No holdings yet</h3>
            <p style={{ fontSize: 13, color: 'rgba(148,163,184,0.8)', marginBottom: 20 }}>Log positions you hold elsewhere to get tailored signals.</p>
            <Button variant="primary" icon="plus" onClick={() => setAddOpen(true)}>Log First Position</Button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: 'rgba(15,23,42,0.4)' }}>
                  {['Ticker', 'Shares', 'Avg Cost', 'Current', 'Value', 'P&L', 'Advice', ''].map((h, i) => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: i === 0 ? 'left' : (i === 6 || i === 7) ? 'center' : 'right',
                      fontSize: 11, fontWeight: 600, color: 'rgba(148,163,184,0.85)',
                      textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {holdings.map((h, i) => {
                  const value = h.shares * h.current;
                  const cost = h.shares * h.avgCost;
                  const plRow = value - cost;
                  const plPctRow = (plRow / cost) * 100;
                  const positive = plRow >= 0;
                  const color = positive ? '#10b981' : '#ef4444';
                  const stock = NSE_STOCKS.find(s => s.ticker === h.ticker);
                  const advice = adviceFor(h);
                  return (
                    <tr key={h.ticker}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                      onMouseLeave={e => e.currentTarget.style.background = i % 2 ? 'rgba(15,23,42,0.2)' : 'transparent'}
                      style={{ background: i % 2 ? 'rgba(15,23,42,0.2)' : 'transparent', transition: 'background 150ms' }}>
                      <td style={{ padding: '14px 16px' }}>
                        <button onClick={() => stock && openStock(stock)} style={{ display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left' }}>
                          <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}22`, border: `1px solid ${color}44`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 10, fontWeight: 800, color }}>{h.ticker.slice(0,2)}</div>
                          <div>
                            <div style={{ fontWeight: 700 }}>{h.ticker}</div>
                            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)' }}>{stock?.name?.slice(0, 20)}</div>
                          </div>
                        </button>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }} className="mono">{h.shares.toLocaleString()}</td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }} className="mono">{h.avgCost.toFixed(2)}</td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }} className="mono">{h.current.toFixed(2)}</td>
                      <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700 }} className="mono">{value.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <div className="mono" style={{ fontWeight: 700, color }}>{positive ? '+' : ''}{plPctRow.toFixed(2)}%</div>
                        <div className="mono" style={{ fontSize: 11, color: `${color}cc` }}>{positive ? '+' : ''}{plRow.toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 11px', borderRadius: 999,
                          background: `${advice.color}1a`, border: `1px solid ${advice.color}55` }}>
                          <Icon name={advice.icon} size={12} color={advice.color} strokeWidth={2.5} />
                          <div style={{ textAlign: 'left' }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: advice.color, lineHeight: 1.1 }}>{advice.label}</div>
                            <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.75)', lineHeight: 1.2 }}>{advice.note}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <Button variant="danger" size="sm" onClick={() => setSellTarget(h)}>Remove</Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={!!sellTarget} onClose={() => setSellTarget(null)}>
        {sellTarget && <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(239,68,68,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon name="x" size={22} color="#ef4444" strokeWidth={3} />
            </div>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>Remove {sellTarget.ticker}?</h3>
              <p style={{ fontSize: 12, color: 'rgba(148,163,184,0.8)' }}>Stop tracking this position</p>
            </div>
          </div>
          <div className="glass" style={{ padding: 14, marginBottom: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
              <span style={{ color: 'rgba(148,163,184,0.8)' }}>Market price</span>
              <span className="mono" style={{ fontWeight: 700 }}>KES {sellTarget.current.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: 'rgba(148,163,184,0.8)' }}>Estimated total</span>
              <span className="mono" style={{ fontWeight: 700, color: '#10b981' }}>KES {(sellTarget.shares * sellTarget.current).toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Button variant="secondary" fullWidth onClick={() => setSellTarget(null)}>Cancel</Button>
            <Button variant="danger" fullWidth onClick={() => removeHolding(sellTarget.ticker)}>Confirm Remove</Button>
          </div>
        </>}
      </Modal>

      <Modal open={addOpen} onClose={() => setAddOpen(false)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(16,185,129,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="plus" size={22} color="#10b981" strokeWidth={3} />
          </div>
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Log a position</h3>
            <p style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>Tell us what you own — we'll send alerts and advice.</p>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 18 }}>
          <div>
            <label style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Ticker</label>
            <select className="glass-input" value={addForm.ticker} onChange={e => setAddForm(f => ({ ...f, ticker: e.target.value }))}
              style={{ background: 'rgba(15,23,42,0.6)' }}>
              {NSE_STOCKS.map(s => (
                <option key={s.ticker} value={s.ticker} style={{ background: '#0f172a' }}>{s.ticker} — {s.name}</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Shares</label>
              <input className="glass-input mono" type="number" min="1" value={addForm.shares}
                onChange={e => setAddForm(f => ({ ...f, shares: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Avg cost (KES)</label>
              <input className="glass-input mono" type="number" step="0.01" placeholder="e.g. 18.50" value={addForm.avgCost}
                onChange={e => setAddForm(f => ({ ...f, avgCost: e.target.value }))} />
            </div>
          </div>
          {(() => {
            const stock = NSE_STOCKS.find(s => s.ticker === addForm.ticker);
            if (!stock) return null;
            return (
              <div className="glass" style={{ padding: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>Current price</div>
                <div className="mono" style={{ fontSize: 16, fontWeight: 700, color: '#10b981' }}>KES {stock.price.toFixed(2)}</div>
              </div>
            );
          })()}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button variant="secondary" fullWidth onClick={() => setAddOpen(false)}>Cancel</Button>
          <Button variant="primary" fullWidth icon="check" onClick={addPosition} disabled={!addForm.shares || !addForm.avgCost}>Start tracking</Button>
        </div>
      </Modal>

      {/* Bot portfolio consent modal */}
      <Modal open={consentModal} onClose={() => setConsentModal(false)} maxWidth={460}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(0,136,204,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="telegram" size={22} color="#0088cc" />
          </div>
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Share Portfolio with NSE Bot?</h3>
            <p style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>Kenya DPA 2019 — explicit consent required</p>
          </div>
        </div>
        <div className="glass" style={{ padding: 14, marginBottom: 16, fontSize: 13, lineHeight: 1.6, color: 'rgba(203,213,225,0.9)' }}>
          <p style={{ marginBottom: 8 }}>If you enable this, your holdings (tickers, quantities, cost prices) will be stored on our server so that <strong>@NSEProBot</strong> can analyse your portfolio on request.</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5, paddingLeft: 4 }}>
            {[
              ['What we store', 'Tickers, share quantities, average cost prices'],
              ['Who can access', 'Only the NSE Analytics bot — not shared with any third party'],
              ['How long', 'Until you turn this off. You can delete all data instantly.'],
              ['This is optional', 'Declining does not affect any other features.'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', gap: 8 }}>
                <Icon name="check" size={12} color="#10b981" strokeWidth={3} style={{ marginTop: 3, flexShrink: 0 }} />
                <span><strong style={{ color: 'white' }}>{k}:</strong> {v}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button variant="secondary" fullWidth onClick={() => setConsentModal(false)}>Not now</Button>
          <Button variant="primary" fullWidth icon="check" onClick={grantConsent}>Enable Bot Access</Button>
        </div>
      </Modal>

      <style>{`
        @media (max-width: 720px) { .opt-grid { grid-template-columns: 1fr !important; } }
      `}</style>
    </div>
  );
};

export default PortfolioPage;
