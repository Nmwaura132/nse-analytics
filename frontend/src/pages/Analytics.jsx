import React from 'react';
import { NSE_STOCKS, generateCandles } from '../data.js';
import { Icon } from '../icons.jsx';
import { Badge, Button } from '../ui.jsx';
import { CandlestickChart, LineChart } from '../charts.jsx';

const AnalyticsPage = ({ tier, addToast, triggerConfetti }) => {
  const [ticker, setTicker] = React.useState('SCOM');
  const [timeframe, setTimeframe] = React.useState('1M');
  const [running, setRunning] = React.useState(false);
  const [backtest, setBacktest] = React.useState(null);
  const [forecasted, setForecasted] = React.useState(false);

  const stock = NSE_STOCKS.find(s => s.ticker === ticker);
  const candles = React.useMemo(() => generateCandles(ticker.charCodeAt(0) + ticker.charCodeAt(1), 60, stock.price), [ticker, stock]);
  const lastClose = candles[candles.length - 1].close;
  const predicted = forecasted ? {
    open: lastClose,
    close: lastClose * (1 + (stock.ai - 50) / 800),
    high: lastClose * 1.025,
    low: lastClose * 0.985,
  } : null;

  const equityCurve = React.useMemo(() => {
    const data = [];
    let v = 100000;
    let rng = ticker.charCodeAt(0) * 13;
    const r = () => { rng = (rng * 9301 + 49297) % 233280; return rng / 233280; };
    for (let i = 0; i < 30; i++) { v *= 1 + (r() - 0.45) * 0.03; data.push(v); }
    return data;
  }, [ticker]);

  const benchmark = React.useMemo(() => {
    const data = [];
    let v = 100000;
    let rng = 7777;
    const r = () => { rng = (rng * 9301 + 49297) % 233280; return rng / 233280; };
    for (let i = 0; i < 30; i++) { v *= 1 + (r() - 0.48) * 0.018; data.push(v); }
    return data;
  }, []);

  const runBacktest = () => {
    setRunning(true);
    setBacktest(null);
    setTimeout(() => {
      setRunning(false);
      setBacktest({
        finalEquity: equityCurve[equityCurve.length - 1],
        return: ((equityCurve[equityCurve.length - 1] / 100000) - 1) * 100,
        winRate: 64.3,
        trades: 42,
        sharpe: 1.84,
        maxDD: -8.2,
      });
      addToast({ type: 'success', icon: 'check', title: 'Backtest complete', message: `${ticker} on ${timeframe} — ran 42 trades.` });
    }, 1600);
  };

  const forecast = () => {
    setForecasted(false);
    setTimeout(() => {
      setForecasted(true);
      triggerConfetti();
      addToast({ type: 'xp', icon: 'sparkles', title: '+50 XP earned', message: 'AI forecast generated.' });
    }, 600);
  };

  return (
    <div className="anim-fade" style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 24px 60px' }}>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' }}>Analytics Lab</h1>
          <p style={{ fontSize: 14, color: 'rgba(148,163,184,0.85)', marginTop: 6 }}>
            Charts, ML forecasts, and strategy backtesting · <Badge color="purple" size="sm" icon="brain">AI-powered</Badge>
          </p>
        </div>
        <Button variant="secondary" icon="arrow-down">Export Report</Button>
      </div>

      <div className="glass" style={{ padding: 14, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)', fontWeight: 600 }}>Ticker</span>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', flex: 1 }}>
          {NSE_STOCKS.slice(0, 10).map(s => (
            <button key={s.ticker} onClick={() => { setTicker(s.ticker); setForecasted(false); setBacktest(null); }}
              style={{ padding: '7px 12px', borderRadius: 8, fontSize: 12, fontWeight: 700,
                background: ticker === s.ticker ? 'rgba(16,185,129,0.18)' : 'rgba(15,23,42,0.5)',
                color: ticker === s.ticker ? '#6ee7b7' : 'rgba(203,213,225,0.7)',
                border: ticker === s.ticker ? '1px solid rgba(16,185,129,0.4)' : '1px solid rgba(255,255,255,0.06)' }}>
              {s.ticker}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 4, padding: 4, background: 'rgba(15,23,42,0.6)', borderRadius: 9, border: '1px solid rgba(255,255,255,0.06)' }}>
          {['1W', '1M', '3M', '1Y'].map(tf => (
            <button key={tf} onClick={() => setTimeframe(tf)}
              style={{ padding: '5px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                color: timeframe === tf ? 'white' : 'rgba(148,163,184,0.7)',
                background: timeframe === tf ? 'rgba(16,185,129,0.15)' : 'transparent' }}>
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div className="glass" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h3 style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>{stock.ticker}</h3>
              <Badge color={stock.change >= 0 ? 'emerald' : 'red'} icon={stock.change >= 0 ? 'arrow-up' : 'arrow-down'}>
                {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%
              </Badge>
            </div>
            <div style={{ fontSize: 12, color: 'rgba(148,163,184,0.8)' }}>{stock.name} · {stock.sector}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 18 }}>
            <div>
              <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.7)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last</div>
              <div className="mono" style={{ fontSize: 22, fontWeight: 800 }}>{lastClose.toFixed(2)}</div>
            </div>
            <Button variant="purple" size="md" icon="brain" onClick={forecast}>
              {forecasted ? 'Refresh forecast' : 'AI Forecast'}
            </Button>
          </div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <CandlestickChart data={candles} width={1280} height={360} predicted={predicted} />
        </div>
        {forecasted && (
          <div className="anim-fade" style={{ marginTop: 14, padding: 14, background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <Icon name="sparkles" size={18} color="#a78bfa" />
            <div style={{ flex: 1, minWidth: 240, fontSize: 13, color: '#e2e8f0' }}>
              <span style={{ fontWeight: 700, color: '#c4b5fd' }}>5-day forecast: </span>
              {predicted.close > lastClose ? 'Bullish bias' : 'Bearish bias'} — model targets <span className="mono" style={{ color: 'white', fontWeight: 700 }}>{predicted.close.toFixed(2)}</span> with {stock.ai}% confidence. Volume regime favors continuation.
            </div>
            <Badge color="purple" size="sm">Confidence {stock.ai}%</Badge>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 18 }} className="ana-grid">
        <div className="glass" style={{ padding: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
            <div style={{ width: 38, height: 38, borderRadius: 10, background: 'rgba(6,182,212,0.18)', border: '1px solid rgba(6,182,212,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon name="play" size={16} color="#06b6d4" />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700 }}>Strategy Backtest</h3>
              <p style={{ fontSize: 12, color: 'rgba(148,163,184,0.85)' }}>SMA cross + RSI filter on {ticker} · last 30 days</p>
            </div>
            <Button variant="cyan" size="md" icon={running ? null : 'play'} onClick={runBacktest} disabled={running}>
              {running ? 'Running…' : 'Run Backtest'}
            </Button>
          </div>

          <div style={{ background: 'rgba(15,23,42,0.4)', borderRadius: 10, padding: 14, marginBottom: 14 }}>
            <LineChart series={[
              { data: equityCurve, color: '#06b6d4' },
              { data: benchmark, color: '#64748b' },
            ]} width={620} height={220} />
            <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 11 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 12, height: 2, background: '#06b6d4', display: 'inline-block' }} />Strategy</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 12, height: 2, background: '#64748b', display: 'inline-block' }} />NSE 20</span>
            </div>
          </div>

          {backtest ? (
            <div className="anim-fade" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10 }}>
              {[
                { l: 'Return', v: `+${backtest.return.toFixed(1)}%`, c: '#10b981' },
                { l: 'Sharpe', v: backtest.sharpe, c: '#06b6d4' },
                { l: 'Win Rate', v: `${backtest.winRate}%`, c: '#10b981' },
                { l: 'Trades', v: backtest.trades, c: 'white' },
                { l: 'Max DD', v: `${backtest.maxDD}%`, c: '#ef4444' },
              ].map(s => (
                <div key={s.l} style={{ padding: 11, background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 9 }}>
                  <div style={{ fontSize: 10, color: 'rgba(148,163,184,0.7)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.l}</div>
                  <div className="mono" style={{ fontSize: 17, fontWeight: 800, color: s.c, marginTop: 2 }}>{s.v}</div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: 18, textAlign: 'center', fontSize: 12, color: 'rgba(148,163,184,0.6)', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: 10 }}>
              Run a backtest to see strategy stats →
            </div>
          )}
        </div>

        <div className="glass" style={{ padding: 22 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Technical Indicators</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { l: 'RSI (14)', v: 58.2, max: 100, color: '#10b981', tag: 'Neutral' },
              { l: 'MACD', v: 0.42, raw: '+0.42', max: 1, color: '#10b981', tag: 'Bullish' },
              { l: 'Bollinger %', v: 72, max: 100, color: '#fbbf24', tag: 'Upper band' },
              { l: 'Volume Z-score', v: 65, raw: '+1.8σ', max: 100, color: '#06b6d4', tag: 'High' },
              { l: 'ADX', v: 31, max: 50, color: '#10b981', tag: 'Trending' },
            ].map(ind => (
              <div key={ind.l}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{ind.l}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: ind.color }}>{ind.raw || ind.v}</span>
                    <Badge color={ind.color === '#10b981' ? 'emerald' : ind.color === '#fbbf24' ? 'amber' : 'cyan'} size="sm">{ind.tag}</Badge>
                  </div>
                </div>
                <div style={{ height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ width: `${(ind.v / ind.max) * 100}%`, height: '100%', background: ind.color, transition: 'width 800ms ease' }} />
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 18, padding: 12, background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Icon name="lightning" size={14} color="#10b981" />
              <span style={{ fontSize: 12, fontWeight: 700, color: '#6ee7b7' }}>Composite Signal</span>
            </div>
            <div style={{ fontSize: 12, color: 'rgba(203,213,225,0.85)' }}>4 of 5 indicators bullish — model favors a long entry on next pullback.</div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 980px) { .ana-grid { grid-template-columns: 1fr !important; } }
      `}</style>
    </div>
  );
};

export default AnalyticsPage;
