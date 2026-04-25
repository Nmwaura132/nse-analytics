import React from 'react';
import { Icon } from './icons.jsx';

export const Button = ({ variant = 'primary', size = 'md', children, icon, iconRight, onClick, disabled, fullWidth, type = 'button', style = {} }) => {
  const styles = {
    primary:  { background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white', border: '1px solid rgba(16,185,129,0.4)', boxShadow: '0 6px 20px -8px rgba(16,185,129,0.6)' },
    secondary:{ background: 'rgba(30,41,59,0.6)', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.12)' },
    ghost:    { background: 'transparent', color: '#cbd5e1', border: '1px solid transparent' },
    danger:   { background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', color: 'white', border: '1px solid rgba(239,68,68,0.4)' },
    telegram: { background: 'linear-gradient(135deg, #0088cc 0%, #0077b5 100%)', color: 'white', border: '1px solid rgba(0,136,204,0.4)', boxShadow: '0 6px 20px -8px rgba(0,136,204,0.6)' },
    cyan:     { background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', color: 'white', border: '1px solid rgba(6,182,212,0.4)' },
    purple:   { background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)', color: 'white', border: '1px solid rgba(139,92,246,0.4)', boxShadow: '0 6px 20px -8px rgba(139,92,246,0.6)' },
  };
  const sizes = {
    sm: { padding: '7px 12px', fontSize: 13, borderRadius: 9 },
    md: { padding: '11px 18px', fontSize: 14, borderRadius: 12 },
    lg: { padding: '14px 22px', fontSize: 15, borderRadius: 12 },
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      style={{
        ...styles[variant], ...sizes[size],
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        fontWeight: 600, letterSpacing: '-0.01em',
        cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1,
        width: fullWidth ? '100%' : undefined,
        transition: 'all 200ms cubic-bezier(0.16,1,0.3,1)',
        ...style,
      }}
      onMouseEnter={e => { if (!disabled) { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.filter = 'brightness(1.1)'; }}}
      onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.filter = ''; }}>
      {icon && <Icon name={icon} size={size === 'sm' ? 14 : 16} />}
      {children}
      {iconRight && <Icon name={iconRight} size={size === 'sm' ? 14 : 16} />}
    </button>
  );
};

export const Badge = ({ children, color = 'emerald', icon, size = 'md', pulse = false }) => {
  const colors = {
    emerald: { bg: 'rgba(16,185,129,0.15)',  text: '#10b981', border: 'rgba(16,185,129,0.3)' },
    red:     { bg: 'rgba(239,68,68,0.15)',   text: '#ef4444', border: 'rgba(239,68,68,0.3)' },
    cyan:    { bg: 'rgba(6,182,212,0.15)',   text: '#06b6d4', border: 'rgba(6,182,212,0.3)' },
    purple:  { bg: 'rgba(139,92,246,0.15)',  text: '#a78bfa', border: 'rgba(139,92,246,0.3)' },
    amber:   { bg: 'rgba(245,158,11,0.15)',  text: '#fbbf24', border: 'rgba(245,158,11,0.3)' },
    slate:   { bg: 'rgba(100,116,139,0.15)', text: '#cbd5e1', border: 'rgba(100,116,139,0.3)' },
  };
  const c = colors[color] || colors.emerald;
  const sizes = { sm: { padding: '3px 8px', fontSize: 11 }, md: { padding: '5px 11px', fontSize: 12 }, lg: { padding: '7px 14px', fontSize: 13 } };
  return (
    <span style={{
      ...sizes[size],
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      borderRadius: 999, display: 'inline-flex', alignItems: 'center', gap: 5,
      fontWeight: 600, letterSpacing: '-0.01em',
      animation: pulse ? 'pulseGlow 2s infinite' : undefined,
    }}>
      {icon && <Icon name={icon} size={11} />}
      {children}
    </span>
  );
};

export const QuotaPill = ({ used, total, label = 'AI requests' }) => {
  const pct = (used / total) * 100;
  const bar = pct >= 90 ? '#ef4444' : pct >= 70 ? '#fbbf24' : '#10b981';
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      padding: '6px 12px 6px 8px',
      background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 999, fontSize: 12, fontWeight: 600,
    }}>
      <Icon name="sparkles" size={14} color={bar} />
      <span className="mono" style={{ color: bar }}>{used}/{total}</span>
      <span style={{ color: 'rgba(148,163,184,0.7)', fontWeight: 500 }}>{label}</span>
      <div style={{ width: 36, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: bar, transition: 'all 400ms ease' }} />
      </div>
    </div>
  );
};

export const Navbar = ({ page, setPage, onLogout, user, quota, tier }) => {
  const [menuOpen, setMenuOpen] = React.useState(false);
  const links = [
    { id: 'dashboard', label: 'Dashboard', icon: 'home' },
    { id: 'portfolio', label: 'Tracker',   icon: 'briefcase' },
    { id: 'analytics', label: 'Analytics', icon: 'chart' },
    { id: 'news',      label: 'News',      icon: 'news' },
  ];
  const tierColor = tier === 'pro' ? 'cyan' : tier === 'club' ? 'purple' : 'slate';
  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 50,
      background: 'rgba(10,16,32,0.7)',
      backdropFilter: 'blur(24px) saturate(150%)', WebkitBackdropFilter: 'blur(24px) saturate(150%)',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
    }}>
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '14px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 10, background: 'linear-gradient(135deg, #10b981, #059669)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 6px 20px -6px rgba(16,185,129,0.6)' }}>
            <Icon name="candlestick" size={18} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, letterSpacing: '-0.02em', lineHeight: 1 }}>NSE Analytics</div>
            <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.7)', letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: 2 }}>Nairobi</div>
          </div>
        </div>

        <div className="desktop-nav" style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 32 }}>
          {links.map(l => (
            <button key={l.id} onClick={() => setPage(l.id)}
              style={{
                padding: '9px 14px', borderRadius: 10, fontSize: 14, fontWeight: 600,
                color: page === l.id ? 'white' : 'rgba(203,213,225,0.7)',
                background: page === l.id ? 'rgba(16,185,129,0.12)' : 'transparent',
                border: page === l.id ? '1px solid rgba(16,185,129,0.25)' : '1px solid transparent',
                display: 'inline-flex', alignItems: 'center', gap: 7, transition: 'all 180ms ease',
              }}
              onMouseEnter={e => { if (page !== l.id) e.currentTarget.style.color = 'white'; }}
              onMouseLeave={e => { if (page !== l.id) e.currentTarget.style.color = 'rgba(203,213,225,0.7)'; }}>
              <Icon name={l.icon} size={15} />{l.label}
            </button>
          ))}
        </div>

        <div style={{ flex: 1 }} />
        <QuotaPill used={quota.used} total={quota.total} />

        <div className="desktop-nav" style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          padding: '6px 12px', background: 'rgba(245,158,11,0.1)',
          border: '1px solid rgba(245,158,11,0.25)', borderRadius: 999, fontSize: 12, fontWeight: 700,
        }}>
          <span style={{ animation: 'floatY 2s ease-in-out infinite', display: 'inline-flex' }}>
            <Icon name="fire" size={14} color="#fbbf24" />
          </span>
          <span className="mono" style={{ color: '#fbbf24' }}>{user.streak}</span>
        </div>

        <div style={{ position: 'relative' }}>
          <button onClick={() => setMenuOpen(o => !o)}
            style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '5px 10px 5px 5px',
              background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 999 }}>
            <div style={{ width: 30, height: 30, borderRadius: '50%',
              background: 'linear-gradient(135deg, #10b981, #06b6d4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 700, color: 'white' }}>
              {user.initials}
            </div>
            <Badge color={tierColor} size="sm">{tier.toUpperCase()}</Badge>
            <Icon name="chevron-down" size={14} color="rgba(148,163,184,0.7)" />
          </button>
          {menuOpen && (
            <>
              <div onClick={() => setMenuOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 50 }} />
              <div className="anim-fade" style={{
                position: 'absolute', top: 'calc(100% + 8px)', right: 0, zIndex: 51,
                minWidth: 220, padding: 6,
                background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(24px)',
                border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12,
                boxShadow: '0 16px 40px -8px rgba(0,0,0,0.6)',
              }}>
                <div style={{ padding: '10px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)', marginBottom: 4 }}>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>{user.name}</div>
                  <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)', marginTop: 2 }}>{user.email}</div>
                </div>
                {[
                  { label: 'Account', icon: 'user', action: () => { setPage('account'); setMenuOpen(false); } },
                  { label: 'Log out', icon: 'logout', action: () => { onLogout(); setMenuOpen(false); }, danger: true },
                ].map(item => (
                  <button key={item.label} onClick={item.action}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 9,
                      padding: '9px 12px', borderRadius: 8, fontSize: 13, fontWeight: 500,
                      color: item.danger ? '#f87171' : '#e2e8f0', transition: 'background 150ms' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <Icon name={item.icon} size={14} />{item.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export const Modal = ({ open, onClose, children, maxWidth = 480 }) => {
  if (!open) return null;
  return (
    <div onClick={onClose} className="anim-fade"
      style={{ position: 'fixed', inset: 0, zIndex: 100, background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div onClick={e => e.stopPropagation()} className="anim-fade-up"
        style={{ maxWidth, width: '100%', background: 'rgba(15,23,42,0.98)',
          backdropFilter: 'blur(24px)', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 18, padding: 28, boxShadow: '0 24px 60px -12px rgba(0,0,0,0.8)' }}>
        {children}
      </div>
    </div>
  );
};

export const Toast = ({ toast, onDismiss }) => {
  React.useEffect(() => {
    if (!toast) return;
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [toast]);
  if (!toast) return null;
  const colors = { success: '#10b981', error: '#ef4444', info: '#06b6d4', xp: '#8b5cf6' };
  const c = colors[toast.type] || '#10b981';
  return (
    <div className="anim-fade-up" style={{
      position: 'fixed', bottom: 24, right: 24, zIndex: 200,
      maxWidth: 360, padding: '14px 18px',
      background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(24px)',
      border: `1px solid ${c}55`, borderRadius: 14,
      boxShadow: `0 16px 40px -8px ${c}33`,
      display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <div style={{ width: 36, height: 36, borderRadius: 10, flexShrink: 0,
        background: `${c}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon name={toast.icon || 'check'} size={18} color={c} />
      </div>
      <div style={{ flex: 1 }}>
        {toast.title && <div style={{ fontWeight: 700, fontSize: 14 }}>{toast.title}</div>}
        <div style={{ fontSize: 13, color: 'rgba(203,213,225,0.85)', marginTop: toast.title ? 2 : 0 }}>{toast.message}</div>
      </div>
    </div>
  );
};

export const Confetti = () => {
  const pieces = React.useMemo(() =>
    Array.from({ length: 60 }, (_, i) => ({
      x: Math.random() * 100,
      delay: Math.random() * 0.5,
      duration: 1.5 + Math.random() * 1.5,
      color: ['#10b981', '#06b6d4', '#8b5cf6', '#fbbf24', '#ef4444'][i % 5],
      size: 6 + Math.random() * 8,
      rotate: Math.random() * 360,
    })), []);
  return (
    <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 300 }}>
      {pieces.map((p, i) => (
        <div key={i} style={{
          position: 'absolute', top: -20, left: `${p.x}%`,
          width: p.size, height: p.size, background: p.color,
          borderRadius: i % 3 === 0 ? '50%' : '2px',
          animation: `confetti ${p.duration}s ease-out ${p.delay}s forwards`,
          transform: `rotate(${p.rotate}deg)`,
        }} />
      ))}
    </div>
  );
};

export const SectionHeader = ({ title, subtitle, action }) => (
  <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 16, gap: 12 }}>
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 700, letterSpacing: '-0.02em' }}>{title}</h2>
      {subtitle && <p style={{ fontSize: 13, color: 'rgba(148,163,184,0.8)', marginTop: 4 }}>{subtitle}</p>}
    </div>
    {action}
  </div>
);
