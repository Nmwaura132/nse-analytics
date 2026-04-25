import React from 'react';
import { Icon } from '../icons.jsx';
import { Button } from '../ui.jsx';
import * as api from '../api.js';

const LoginPage = ({ onLogin }) => {
  const [mode, setMode] = React.useState('login');
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [name, setName] = React.useState('');
  const [showPassword, setShowPassword] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [tgPrompt, setTgPrompt] = React.useState(false);
  const [tgId, setTgId] = React.useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email.includes('@')) { setError('Enter a valid email'); return; }
    if (password.length < 4) { setError('Password too short'); return; }
    setLoading(true);
    try {
      let data;
      if (mode === 'register') {
        if (!name.trim()) { setError('Enter your name'); setLoading(false); return; }
        data = await api.register(email, password);
      } else {
        data = await api.login(email, password);
      }
      onLogin(data);
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const telegramLogin = async () => {
    if (!tgId.trim()) { setTgPrompt(true); return; }
    setLoading(true);
    setTgPrompt(false);
    try {
      const data = await api.telegramLogin(tgId.trim(), name.trim());
      onLogin(data);
    } catch (err) {
      setError(err.message || 'Telegram login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, position: 'relative' }}>
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        {['SCOM +2.34%', 'KCB +1.82%', 'EABL +3.21%', 'EQTY -0.96%', 'SASN +5.32%'].map((t, i) => {
          const positive = !t.includes('-');
          return (
            <div key={i} className="mono" style={{
              position: 'absolute',
              top: `${15 + i * 15}%`,
              left: i % 2 === 0 ? '-10%' : '70%',
              fontSize: 13, fontWeight: 600,
              color: positive ? 'rgba(16,185,129,0.18)' : 'rgba(239,68,68,0.18)',
              animation: `slideMarquee${i} ${30 + i * 4}s linear infinite`,
            }}>{t}</div>
          );
        })}
      </div>

      <div className="anim-fade-up" style={{ width: '100%', maxWidth: 440, position: 'relative', zIndex: 2 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 28 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: 'linear-gradient(135deg, #10b981, #059669)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 12px 32px -8px rgba(16, 185, 129, 0.6)',
            animation: 'floatY 3s ease-in-out infinite',
          }}>
            <Icon name="candlestick" size={26} color="white" />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1 }}>NSE Analytics</div>
            <div style={{ fontSize: 11, color: '#10b981', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4, fontWeight: 700 }}>Nairobi · Live</div>
          </div>
        </div>

        <div className="glass-strong" style={{ padding: 32, borderRadius: 20 }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 6 }}>
              {mode === 'login' ? 'Welcome back' : 'Smarter market intelligence'}
            </h1>
            <p style={{ fontSize: 13, color: 'rgba(148,163,184,0.85)' }}>
              Kenya's Premier Stock Intelligence Platform
            </p>
          </div>

          <div style={{
            display: 'flex', padding: 4, marginBottom: 22,
            background: 'rgba(15,23,42,0.6)', borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.06)',
          }}>
            {['login', 'register'].map(m => (
              <button key={m} onClick={() => setMode(m)}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 9, fontSize: 13, fontWeight: 600,
                  color: mode === m ? 'white' : 'rgba(148,163,184,0.7)',
                  background: mode === m ? 'rgba(16,185,129,0.15)' : 'transparent',
                  border: mode === m ? '1px solid rgba(16,185,129,0.3)' : '1px solid transparent',
                  transition: 'all 200ms',
                }}>
                {m === 'login' ? 'Sign in' : 'Register'}
              </button>
            ))}
          </div>

          <form onSubmit={submit}>
            {mode === 'register' && (
              <div style={{ marginBottom: 14 }} className="anim-fade">
                <label style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block' }}>Full name</label>
                <input className="glass-input" type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Kaniel Mwangi" />
              </div>
            )}
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block' }}>Email</label>
              <div style={{ position: 'relative' }}>
                <input className="glass-input" type="email" value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com" style={{ paddingLeft: 42 }} />
                <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}>
                  <Icon name="mail" size={16} color="rgba(148,163,184,0.6)" />
                </div>
              </div>
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600, marginBottom: 6, display: 'block' }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input className="glass-input" type={showPassword ? 'text' : 'password'} value={password}
                  onChange={e => setPassword(e.target.value)} placeholder="••••••••" style={{ paddingLeft: 42, paddingRight: 42 }} />
                <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}>
                  <Icon name="lock" size={16} color="rgba(148,163,184,0.6)" />
                </div>
                <button type="button" onClick={() => setShowPassword(s => !s)}
                  style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', padding: 4 }}>
                  <Icon name="eye" size={16} color="rgba(148,163,184,0.6)" />
                </button>
              </div>
            </div>

            {error && (
              <div className="anim-fade" style={{ padding: '8px 12px', marginBottom: 14, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 9, fontSize: 12, color: '#fca5a5' }}>
                {error}
              </div>
            )}

            <Button type="submit" variant="primary" size="lg" fullWidth disabled={loading} icon={loading ? null : 'arrow-right'}>
              {loading ? 'Signing in…' : (mode === 'login' ? 'Sign In' : 'Create Account')}
            </Button>
          </form>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0' }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.08)' }} />
            <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.6)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>or continue with</span>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.08)' }} />
          </div>

          {tgPrompt ? (
            <div className="anim-fade" style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <input className="glass-input" style={{ flex: 1 }} type="text"
                value={tgId} onChange={e => setTgId(e.target.value)}
                placeholder="Your Telegram ID (e.g. 5649100063)" autoFocus
                onKeyDown={e => e.key === 'Enter' && telegramLogin()} />
              <Button variant="telegram" size="md" onClick={telegramLogin} disabled={loading}>Go</Button>
            </div>
          ) : (
            <Button variant="telegram" size="lg" fullWidth icon="telegram" onClick={telegramLogin} disabled={loading}>
              Sign in with Telegram
            </Button>
          )}

          <p style={{ textAlign: 'center', fontSize: 12, color: 'rgba(148,163,184,0.7)', marginTop: 20 }}>
            {mode === 'login' ? "Don't have an account?" : 'Already a member?'}{' '}
            <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
              style={{ color: '#10b981', fontWeight: 700 }}>
              {mode === 'login' ? 'Register' : 'Sign in'}
            </button>
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 22, padding: '0 8px' }}>
          {[
            { k: '14K+', v: 'Active members' },
            { k: '47', v: 'NSE tickers' },
            { k: '92%', v: 'Signal accuracy' },
          ].map(s => (
            <div key={s.v} style={{ textAlign: 'center' }}>
              <div className="mono" style={{ fontSize: 18, fontWeight: 700, color: '#10b981' }}>{s.k}</div>
              <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)', marginTop: 2 }}>{s.v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
