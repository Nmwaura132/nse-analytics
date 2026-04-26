import React from 'react';
import { Icon } from '../icons.jsx';
import { Badge, Button, Modal } from '../ui.jsx';

const TIERS = [
  {
    id: 'free', name: 'Free', price: 0, color: '#10b981',
    features: ['10 AI requests / day', 'Basic charts', '5 watchlist slots', 'Email alerts'],
  },
  {
    id: 'pro', name: 'Pro', price: 1499, color: '#06b6d4', popular: true,
    features: ['200 AI requests / day', 'Advanced charts + forecasts', '50 watchlist slots', 'Telegram + SMS alerts', 'Backtesting'],
  },
  {
    id: 'club', name: 'Club', price: 4999, color: '#8b5cf6',
    features: ['Unlimited AI requests', 'Priority forecasts', 'Unlimited watchlist', 'Personal analyst chat', 'Custom strategies', 'Early features'],
  },
];

const MpesaModal = ({ open, onClose, plan, onConfirm }) => {
  const [phone, setPhone] = React.useState('0712 345 678');
  const [step, setStep] = React.useState('input');
  React.useEffect(() => { if (open) setStep('input'); }, [open]);

  const submit = () => {
    setStep('sending');
    setTimeout(() => {
      setStep('done');
      setTimeout(() => { onConfirm(plan); onClose(); }, 1200);
    }, 1600);
  };

  if (!plan) return null;
  return (
    <Modal open={open} onClose={onClose} maxWidth={420}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: '#00a651', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13, color: 'white' }}>
          M-PESA
        </div>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Pay with M-Pesa</h3>
          <p style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>Upgrade to {plan.name} · KES {plan.price.toLocaleString()}/mo</p>
        </div>
      </div>
      {step === 'input' && (
        <>
          <label style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block' }}>M-Pesa phone number</label>
          <input className="glass-input mono" value={phone} onChange={e => setPhone(e.target.value)} style={{ marginBottom: 14 }} />
          <div style={{ padding: 12, background: 'rgba(15,23,42,0.5)', borderRadius: 9, marginBottom: 16, fontSize: 12, color: 'rgba(203,213,225,0.85)', lineHeight: 1.5 }}>
            You'll get an STK push on this number to confirm <span className="mono" style={{ color: 'white', fontWeight: 700 }}>KES {plan.price.toLocaleString()}</span>. No card needed.
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Button variant="secondary" fullWidth onClick={onClose}>Cancel</Button>
            <Button variant="primary" fullWidth onClick={submit}>Send STK Push</Button>
          </div>
        </>
      )}
      {step === 'sending' && (
        <div style={{ padding: '32px 12px', textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, margin: '0 auto 16px', border: '3px solid rgba(16,185,129,0.2)', borderTop: '3px solid #10b981', borderRadius: '50%', animation: 'spinSlow 1s linear infinite' }} />
          <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Waiting for confirmation</div>
          <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>Check your phone for the M-Pesa prompt…</div>
        </div>
      )}
      {step === 'done' && (
        <div className="anim-fade-up" style={{ padding: '32px 12px', textAlign: 'center' }}>
          <div style={{ width: 64, height: 64, margin: '0 auto 16px', borderRadius: '50%', background: 'rgba(16,185,129,0.15)', border: '2px solid #10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="check" size={32} color="#10b981" strokeWidth={3} />
          </div>
          <div style={{ fontSize: 17, fontWeight: 800 }}>Payment confirmed!</div>
          <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', marginTop: 4 }}>Welcome to {plan.name} · Receipt sent</div>
        </div>
      )}
      <style>{`@keyframes spinSlow { to { transform: rotate(360deg); } }`}</style>
    </Modal>
  );
};

const AccountPage = ({ user, tier, setTier, addToast, triggerConfetti }) => {
  const [mpesaPlan, setMpesaPlan] = React.useState(null);

  const upgrade = (plan) => {
    if (plan.id === tier) return;
    if (plan.id === 'free') {
      setTier('free');
      addToast({ type: 'info', icon: 'check', message: 'Downgraded to Free' });
      return;
    }
    setMpesaPlan(plan);
  };

  const confirmUpgrade = (plan) => {
    setTier(plan.id);
    triggerConfetti();
    addToast({ type: 'xp', icon: 'crown', title: `Upgraded to ${plan.name}!`, message: '+500 XP earned · enjoy your perks' });
  };

  const xpPct = (user.xp / user.nextLevelXp) * 100;

  return (
    <div className="anim-fade" style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px 60px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' }}>Account</h1>
        <p style={{ fontSize: 14, color: 'rgba(148,163,184,0.85)', marginTop: 6 }}>Manage your profile, plan, and connected channels.</p>
      </div>

      <div className="glass" style={{ padding: 24, marginBottom: 18, position: 'relative', overflow: 'hidden',
        background: tier === 'club' ? 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.06))' :
                    tier === 'pro'  ? 'linear-gradient(135deg, rgba(6,182,212,0.15), rgba(16,185,129,0.06))' :
                                      'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(6,182,212,0.04))' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
          <div style={{ width: 80, height: 80, borderRadius: 22,
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, fontWeight: 800, color: 'white',
            boxShadow: '0 16px 40px -8px rgba(16,185,129,0.5)', position: 'relative' }}>
            {user.initials}
            <div style={{ position: 'absolute', bottom: -4, right: -4, padding: '3px 8px', borderRadius: 999,
              background: 'linear-gradient(135deg, #fbbf24, #f59e0b)', fontSize: 11, fontWeight: 800, color: '#0a1020',
              border: '2px solid #0a1020' }}>L{user.level}</div>
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em' }}>{user.name}</h2>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 6, flexWrap: 'wrap' }}>
              <Badge color={tier === 'admin' ? 'purple' : tier === 'club' ? 'purple' : tier === 'pro' ? 'cyan' : 'emerald'} icon={tier === 'admin' ? 'shield' : tier === 'club' ? 'crown' : tier === 'pro' ? 'rocket' : 'spark'}>
                {tier === 'admin' ? 'Admin' : (TIERS.find(t => t.id === tier)?.name ?? tier)} member
              </Badge>
              <span style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>· Joined {user.joined}</span>
              {user.telegramLinked && <Badge color="cyan" icon="telegram" size="sm">{user.telegram}</Badge>}
            </div>
            <div style={{ marginTop: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, fontSize: 11, color: 'rgba(148,163,184,0.85)' }}>
                <span><span className="mono" style={{ color: 'white', fontWeight: 700 }}>{user.xp}</span> / {user.nextLevelXp} XP</span>
                <span>{(user.nextLevelXp - user.xp).toLocaleString()} to L{user.level + 1}</span>
              </div>
              <div style={{ height: 8, background: 'rgba(255,255,255,0.06)', borderRadius: 999, overflow: 'hidden' }}>
                <div style={{ width: `${xpPct}%`, height: '100%',
                  background: 'linear-gradient(90deg, #8b5cf6, #06b6d4, #10b981)',
                  backgroundSize: '200% 100%', animation: 'shimmer 3s linear infinite' }} />
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'center', padding: '10px 14px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5 }}>
              <Icon name="fire" size={16} color="#fbbf24" />
              <div className="mono" style={{ fontSize: 22, fontWeight: 800, color: '#fbbf24' }}>{user.streak}</div>
            </div>
            <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 2 }}>day streak</div>
          </div>
        </div>

        <div style={{ marginTop: 20, paddingTop: 18, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.85)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, marginBottom: 10 }}>Achievements</div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {user.badges.map((b, i) => (
              <div key={b} className="anim-fade-up" style={{ animationDelay: `${i * 60}ms`,
                padding: '8px 14px', background: 'rgba(15,23,42,0.5)',
                border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10,
                display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <Icon name="trophy" size={14} color="#fbbf24" />
                <span style={{ fontSize: 12, fontWeight: 600 }}>{b}</span>
              </div>
            ))}
            {['Streak Master', 'Diamond Hands'].map(b => (
              <div key={b} style={{ padding: '8px 14px', background: 'rgba(15,23,42,0.3)',
                border: '1px dashed rgba(255,255,255,0.08)', borderRadius: 10,
                display: 'inline-flex', alignItems: 'center', gap: 8, opacity: 0.5 }}>
                <Icon name="lock" size={12} color="rgba(148,163,184,0.7)" />
                <span style={{ fontSize: 12, fontWeight: 600 }}>{b}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 18 }} className="acc-grid">
        <div>
          <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 12 }}>Choose your plan</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            {TIERS.map(plan => {
              const current = plan.id === tier;
              return (
                <div key={plan.id} className="lift" style={{ padding: 18, position: 'relative', borderRadius: 14,
                  background: current ? `${plan.color}11` : 'rgba(20,28,48,0.55)',
                  backdropFilter: 'blur(20px)',
                  border: current ? `1.5px solid ${plan.color}` : '1px solid rgba(255,255,255,0.08)',
                  boxShadow: current ? `0 12px 30px -8px ${plan.color}55` : 'none' }}>
                  {plan.popular && !current && (
                    <div style={{ position: 'absolute', top: -10, left: 14, padding: '3px 10px', background: 'linear-gradient(135deg, #06b6d4, #0891b2)', fontSize: 10, fontWeight: 800, color: 'white', borderRadius: 999, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Most Popular</div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <div style={{ width: 30, height: 30, borderRadius: 8, background: `${plan.color}22`, border: `1px solid ${plan.color}55`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon name={plan.id === 'club' ? 'crown' : plan.id === 'pro' ? 'rocket' : 'spark'} size={14} color={plan.color} />
                    </div>
                    <span style={{ fontSize: 15, fontWeight: 800 }}>{plan.name}</span>
                    {current && <Badge color={plan.id === 'club' ? 'purple' : plan.id === 'pro' ? 'cyan' : 'emerald'} size="sm">CURRENT</Badge>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 12 }}>
                    <span className="mono" style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em' }}>
                      {plan.price === 0 ? 'Free' : plan.price.toLocaleString()}
                    </span>
                    {plan.price > 0 && <span style={{ fontSize: 12, color: 'rgba(148,163,184,0.7)' }}>KES/mo</span>}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginBottom: 14, minHeight: 130 }}>
                    {plan.features.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: 12, color: 'rgba(203,213,225,0.85)' }}>
                        <Icon name="check" size={13} color={plan.color} strokeWidth={3} />
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>
                  <Button
                    variant={current ? 'secondary' : plan.id === 'club' ? 'purple' : plan.id === 'pro' ? 'cyan' : 'primary'}
                    fullWidth disabled={current}
                    icon={current ? 'check' : plan.price > 0 ? 'mpesa' : 'arrow-right'}
                    onClick={() => upgrade(plan)}>
                    {current ? 'Current plan' : plan.price === 0 ? 'Downgrade' : 'Upgrade with M-Pesa'}
                  </Button>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="glass" style={{ padding: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Icon name="sparkles" size={16} color="#10b981" />
              <h3 style={{ fontSize: 14, fontWeight: 700 }}>This month's usage</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'AI forecasts', used: 84, total: tier === 'club' ? 999 : tier === 'pro' ? 200 : 10, color: '#8b5cf6' },
                { label: 'Backtests run', used: 12, total: tier === 'club' ? 999 : tier === 'pro' ? 50 : 3, color: '#06b6d4' },
                { label: 'Active alerts', used: 8, total: tier === 'club' ? 999 : tier === 'pro' ? 25 : 5, color: '#10b981' },
              ].map(s => {
                const pct = Math.min(100, (s.used / s.total) * 100);
                const display = s.total >= 999 ? '∞' : s.total;
                return (
                  <div key={s.label}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, fontSize: 12 }}>
                      <span style={{ fontWeight: 600 }}>{s.label}</span>
                      <span className="mono" style={{ color: s.color, fontWeight: 700 }}>{s.used}<span style={{ color: 'rgba(148,163,184,0.5)' }}> / {display}</span></span>
                    </div>
                    <div style={{ height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 999, overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: s.color, transition: 'width 800ms ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass" style={{ padding: 18 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Connected</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { name: 'Telegram', sub: user.telegram, icon: 'telegram', color: '#0088cc', linked: true },
                { name: 'M-Pesa', sub: '+254 712 ••• 678', icon: 'mpesa', color: '#00a651', linked: true },
                { name: 'Email', sub: user.email, icon: 'mail', color: '#10b981', linked: true },
              ].map(c => (
                <div key={c.name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 10, background: 'rgba(15,23,42,0.4)', borderRadius: 9 }}>
                  <div style={{ width: 30, height: 30, borderRadius: 8, background: `${c.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon name={c.icon} size={14} color={c.color} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700 }}>{c.name}</div>
                    <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.sub}</div>
                  </div>
                  <Badge color="emerald" size="sm" icon="check">Linked</Badge>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <MpesaModal open={!!mpesaPlan} onClose={() => setMpesaPlan(null)} plan={mpesaPlan} onConfirm={confirmUpgrade} />

      <style>{`
        @media (max-width: 980px) { .acc-grid { grid-template-columns: 1fr !important; } }
      `}</style>
    </div>
  );
};

export default AccountPage;
