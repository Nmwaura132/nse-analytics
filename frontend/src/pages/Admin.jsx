import React from 'react';
import { apiFetch } from '../api.js';
import { Icon } from '../icons.jsx';
import { Badge } from '../ui.jsx';

// ── Helpers ─────────────────────────────────────────────────────────────────

const fmtKES = n => 'KES ' + Number(n || 0).toLocaleString();
const fmtNum = n => Number(n || 0).toLocaleString();

// ── Sub-components ──────────────────────────────────────────────────────────

const StatCard = ({ icon, iconColor, label, value, sub, borderColor }) => (
  <div style={{
    background: 'rgba(30,41,59,0.7)', backdropFilter: 'blur(12px)',
    border: `1px solid rgba(255,255,255,0.08)`,
    borderTop: `2px solid ${borderColor}`,
    borderRadius: 14, padding: '20px 22px',
    boxShadow: `0 8px 32px -8px rgba(0,0,0,0.4)`,
  }}>
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
      <div>
        <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.7)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>{label}</div>
        <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em', fontFamily: '"JetBrains Mono", monospace' }}>{value}</div>
        {sub && <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.7)', marginTop: 5 }}>{sub}</div>}
      </div>
      <div style={{ width: 42, height: 42, borderRadius: 11, background: `${iconColor}20`, border: `1px solid ${iconColor}40`,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon name={icon} size={20} color={iconColor} />
      </div>
    </div>
  </div>
);

const TierBar = ({ label, count, total, color }) => {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
      <div style={{ width: 40, fontSize: 12, fontWeight: 600, color: 'rgba(203,213,225,0.8)', textAlign: 'right' }}>{label}</div>
      <div style={{ flex: 1, height: 8, background: 'rgba(255,255,255,0.06)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 800ms cubic-bezier(0.16,1,0.3,1)' }} />
      </div>
      <div style={{ width: 30, fontSize: 12, color, fontWeight: 700, fontFamily: '"JetBrains Mono", monospace' }}>{count}</div>
      <div style={{ width: 36, fontSize: 11, color: 'rgba(148,163,184,0.5)', fontFamily: '"JetBrains Mono", monospace' }}>{pct}%</div>
    </div>
  );
};

const DailyChart = ({ data }) => {
  if (!data || data.length === 0) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 120, color: 'rgba(148,163,184,0.4)', gap: 8 }}>
      <Icon name="chart" size={28} color="currentColor" />
      <span style={{ fontSize: 13 }}>No usage data yet</span>
    </div>
  );
  const maxVal = Math.max(...data.map(d => d.count), 1);
  const today = new Date().toISOString().slice(0, 10);
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 5, height: 120, paddingTop: 8 }}>
      {data.map((d, i) => {
        const isToday = d.date === today;
        const h = Math.max(4, Math.round((d.count / maxVal) * 100));
        const label = new Date(d.date + 'T12:00:00').toLocaleDateString('en-KE', { weekday: 'short' });
        return (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.5)', fontFamily: '"JetBrains Mono", monospace' }}>{d.count}</div>
            <div title={`${d.date}: ${d.count} req`} style={{
              width: '100%', height: `${h}px`, minHeight: 4,
              background: isToday ? '#10b981' : 'rgba(16,185,129,0.35)',
              borderRadius: '3px 3px 0 0',
              boxShadow: isToday ? '0 0 8px rgba(16,185,129,0.5)' : 'none',
            }} />
            <div style={{ fontSize: 10, color: isToday ? '#10b981' : 'rgba(148,163,184,0.4)', fontWeight: isToday ? 700 : 400 }}>{label}</div>
          </div>
        );
      })}
    </div>
  );
};

const PaymentsTable = ({ payments }) => {
  const [filter, setFilter] = React.useState('all');
  const filtered = payments.filter(p => filter === 'all' || p.type === filter);
  const statusColor = s => s === 'active' ? '#10b981' : s === 'pending' ? '#fbbf24' : '#ef4444';
  const tierColor = t => t === 'club' ? '#a78bfa' : t === 'pro' ? '#06b6d4' : '#94a3b8';

  return (
    <div>
      <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
        {['all', 'subscription', 'topup'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 600, cursor: 'pointer',
              background: filter === f ? 'rgba(16,185,129,0.15)' : 'transparent',
              border: filter === f ? '1px solid rgba(16,185,129,0.35)' : '1px solid rgba(255,255,255,0.08)',
              color: filter === f ? '#10b981' : 'rgba(148,163,184,0.7)',
            }}>
            {f === 'all' ? 'All' : f === 'subscription' ? 'Subscriptions' : 'Top-ups'}
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'rgba(148,163,184,0.4)', padding: '24px 0', fontSize: 13 }}>No payments yet</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              {['Type', 'Tier / Credits', 'Amount (KES)', 'Status', 'Date'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, fontWeight: 600, color: 'rgba(148,163,184,0.5)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '10px 10px' }}>
                  <Badge color={p.type === 'topup' ? 'amber' : 'emerald'} size="sm">{p.type === 'topup' ? 'Top-up' : 'Sub'}</Badge>
                </td>
                <td style={{ padding: '10px 10px', color: tierColor(p.tier), fontWeight: 600, fontFamily: '"JetBrains Mono", monospace' }}>{p.tier}</td>
                <td style={{ padding: '10px 10px', fontFamily: '"JetBrains Mono", monospace', fontWeight: 700 }}>{Number(p.amount).toLocaleString()}</td>
                <td style={{ padding: '10px 10px' }}>
                  <span style={{ color: statusColor(p.status), fontWeight: 600, fontSize: 12 }}>
                    {p.status === 'active' ? '✓ ' : p.status === 'pending' ? '⏳ ' : '✗ '}{p.status}
                  </span>
                </td>
                <td style={{ padding: '10px 10px', color: 'rgba(148,163,184,0.7)', fontFamily: '"JetBrains Mono", monospace' }}>
                  {new Date(p.date).toLocaleDateString('en-KE', { day: 'numeric', month: 'short' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

// ── Main Component ──────────────────────────────────────────────────────────

export default function AdminPage({ addToast, setPage }) {
  const [stats, setStats] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [lastUpdated, setLastUpdated] = React.useState(null);
  const [live, setLive] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      const res = await apiFetch('/admin/stats');
      if (res.status === 403) {
        addToast?.('Access denied', 'error');
        setPage?.('dashboard');
        return;
      }
      const data = await res.json();
      setStats(data);
      setLastUpdated(new Date());
    } catch (e) {
      addToast?.('Failed to load admin stats', 'error');
    } finally {
      setLoading(false);
    }
  }, [addToast, setPage]);

  React.useEffect(() => {
    load();
  }, [load]);

  // Auto-refresh when live mode is on
  React.useEffect(() => {
    if (!live) return;
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, [live, load]);

  const timeAgo = lastUpdated
    ? Math.floor((Date.now() - lastUpdated.getTime()) / 60000) + 'm ago'
    : '';

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 12, color: 'rgba(148,163,184,0.5)' }}>
      <div style={{ width: 20, height: 20, border: '2px solid rgba(139,92,246,0.3)', borderTopColor: '#8b5cf6', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
      Loading admin stats…
    </div>
  );

  if (!stats) return null;

  const { users, revenue, usage, system } = stats;
  const tierTotal = Object.values(users.by_tier).reduce((a, b) => a + b, 0);
  const usageTotal = Object.values(usage.by_tier_today).reduce((a, b) => a + b, 0);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '28px 24px 60px' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="shield" size={20} color="#a78bfa" />
          </div>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', color: '#a78bfa' }}>NSE Admin</h1>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.5)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Platform Dashboard</div>
          </div>
          <Badge color="purple" size="sm" icon="shield">Admin Only</Badge>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {lastUpdated && <span style={{ fontSize: 12, color: 'rgba(148,163,184,0.5)' }}>Updated {timeAgo}</span>}
          <button onClick={load} style={{
            padding: '8px 14px', borderRadius: 9, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)', color: '#06b6d4',
          }}>
            <Icon name="refresh" size={13} /> Refresh
          </button>
          <button onClick={() => setLive(l => !l)} style={{
            padding: '8px 14px', borderRadius: 9, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: live ? 'rgba(16,185,129,0.15)' : 'rgba(30,41,59,0.5)',
            border: live ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgba(255,255,255,0.08)',
            color: live ? '#10b981' : 'rgba(148,163,184,0.7)',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: live ? '#10b981' : '#94a3b8',
              boxShadow: live ? '0 0 6px #10b981' : 'none', display: 'inline-block' }} />
            {live ? 'Live' : 'Static'}
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 20 }}>
        <StatCard icon="users" iconColor="#06b6d4" label="Total Users" borderColor="#06b6d4"
          value={fmtNum(users.total)}
          sub={`+${users.new_today} today · +${users.new_this_week} this week`} />
        <StatCard icon="coins" iconColor="#10b981" label="Revenue (All Time)" borderColor="#10b981"
          value={fmtKES(revenue.total_kes)}
          sub={`${fmtKES(revenue.this_month_kes)} this month`} />
        <StatCard icon="spark" iconColor="#8b5cf6" label="AI Requests Today" borderColor="#8b5cf6"
          value={fmtNum(usage.requests_today)}
          sub={`${fmtNum(usage.requests_this_week)} this week`} />
        <StatCard icon={system.db_ok ? 'check' : 'alert'} iconColor={system.db_ok ? '#10b981' : '#ef4444'}
          label="System Status" borderColor={system.db_ok ? '#10b981' : '#ef4444'}
          value={system.db_ok ? 'All OK' : 'DB Error'}
          sub={`${fmtNum(system.stocks_count)} stocks · ${revenue.active_subscriptions} active subs`} />
      </div>

      {/* Middle row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 14, marginBottom: 20 }}>
        {/* Users by tier */}
        <div style={{ background: 'rgba(30,41,59,0.7)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '20px 22px' }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: 'rgba(203,213,225,0.9)' }}>Users by Tier</h3>
          <TierBar label="Free" count={users.by_tier.free || 0} total={tierTotal} color="#94a3b8" />
          <TierBar label="Pro"  count={users.by_tier.pro  || 0} total={tierTotal} color="#06b6d4" />
          <TierBar label="Club" count={users.by_tier.club || 0} total={tierTotal} color="#8b5cf6" />
          <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: 12, color: 'rgba(148,163,184,0.6)' }}>
            {fmtNum(users.total)} registered · {fmtNum(users.telegram_linked)} Telegram linked
          </div>
        </div>

        {/* Daily usage chart */}
        <div style={{ background: 'rgba(30,41,59,0.7)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '20px 22px' }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'rgba(203,213,225,0.9)' }}>Daily AI Usage — 7 Days</h3>
          <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.5)', marginBottom: 12 }}>Requests across all users</div>
          <DailyChart data={usage.daily_chart} />
        </div>
      </div>

      {/* Usage by tier today */}
      <div style={{ background: 'rgba(30,41,59,0.7)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '20px 22px', marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: 'rgba(203,213,225,0.9)' }}>AI Usage by Tier Today</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 8 }}>
          <TierBar label="Free" count={usage.by_tier_today.free || 0} total={usageTotal || 1} color="#94a3b8" />
          <TierBar label="Pro"  count={usage.by_tier_today.pro  || 0} total={usageTotal || 1} color="#06b6d4" />
          <TierBar label="Club" count={usage.by_tier_today.club || 0} total={usageTotal || 1} color="#8b5cf6" />
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: 'rgba(148,163,184,0.5)' }}>
          {fmtNum(usageTotal)} total requests today
        </div>
      </div>

      {/* Recent payments */}
      <div style={{ background: 'rgba(30,41,59,0.7)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '20px 22px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: 'rgba(203,213,225,0.9)' }}>Recent Payments</h3>
          <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.4)' }}>No emails shown · DPA compliant</span>
        </div>
        <PaymentsTable payments={revenue.recent_payments} />
      </div>

    </div>
  );
}
