import { useState, useEffect } from 'react';
import TradeModal from '../components/TradeModal';
import Plot from 'react-plotly.js';

function Portfolio() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [budget, setBudget] = useState(100000);
    const [tickers, setTickers] = useState('SCOM, EQTY, KCB, EABL, ABSA');
    const [optimization, setOptimization] = useState(null);
    const [showTradeModal, setShowTradeModal] = useState(false);

    const fetchPortfolio = () => {
        fetch('/api/portfolio?user_id=1')
            .then(res => res.json())
            .then(d => {
                setData(d);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchPortfolio();
    }, []);

    const runOptimizer = () => {
        setOptimization({ loading: true });
        const tickersArr = tickers.split(',').map(t => t.trim()).filter(Boolean);
        fetch('/api/portfolio/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ budget: parseFloat(budget), tickers: tickersArr })
        })
        .then(res => res.json())
        .then(resData => setOptimization({ ...resData, loading: false }))
        .catch(err => setOptimization({ error: err.message, loading: false }));
    };

    const removeTrade = (ticker) => {
        if (!window.confirm(`Remove ${ticker}?`)) { return; }
        fetch('/api/portfolio/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, user_id: '1' })
        }).then(() => fetchPortfolio());
    };

    return (
        <div className="page fade-in">
            <div className="portfolio-layout">
        <aside className="portfolio-sidebar">
          <div className="glass-card optimizer-card">
            <h3>AI Optimizer</h3>
            <p className="hint">Find optimal weights for your capital</p>
            <div className="opt-form">
              <label>Budget (KES)</label>
              <input 
                type="number" 
                value={budget} 
                onChange={(e) => setBudget(e.target.value)} 
              />
              <label style={{ marginTop: '1rem' }}>Candidate Stocks</label>
              <input 
                type="text" 
                value={tickers} 
                placeholder="SCOM, EQTY..."
                onChange={(e) => setTickers(e.target.value)} 
              />
              <button 
                className="opt-btn" 
                onClick={runOptimizer}
                disabled={optimization?.loading}
              >
                {optimization?.loading ? 'Running...' : 'Optimize Portfolio'}
              </button>
            </div>

            {optimization && !optimization.loading && (
              <div className="opt-results fade-in">
                <div className="opt-stat">
                  <span>Exp. Return:</span>
                  <span className="green">{optimization.metrics?.expected_annual_return}%</span>
                </div>
                <div className="opt-stat" style={{ marginBottom: '1rem' }}>
                  <span>Sharpe Ratio:</span>
                  <span className="purple">{optimization.metrics?.sharpe_ratio}</span>
                </div>
                <div style={{ height: '220px', width: '100%' }}>
                  <Plot
                    data={[{
                      values: optimization.allocations?.map(a => a.percentage),
                      labels: optimization.allocations?.map(a => a.ticker),
                      type: 'pie',
                      hole: 0.6,
                      textinfo: 'label+percent',
                      hoverinfo: 'label+percent+value',
                      marker: {
                        colors: ['#10b981', '#3b82f6', '#f43f5e', '#a855f7', '#f59e0b', '#06b6d4']
                      }
                    }]}
                    layout={{
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      margin: { t: 10, b: 10, l: 10, r: 10 },
                      showlegend: false,
                      font: { color: '#94a3b8' }
                    }}
                    config={{ displayModeBar: false }}
                    useResizeHandler={true}
                    style={{ width: "100%", height: "100%" }}
                  />
                </div>
              </div>
            )}
          </div>
        </aside>

        {loading ? (
          <div className="loading">Loading holdings...</div>
        ) : (
          <div className="portfolio-main">
            <header className="page-header">
                <h2>My Investment Portfolio</h2>
                <button className="primary-btn" onClick={() => setShowTradeModal(true)}>➕ Add Trade</button>
            </header>
            
            {data.is_offline && (
              <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '0.5rem', marginBottom: '1.5rem', color: 'var(--accent-red)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.2rem' }}>⚠️</span>
                <div>
                  <strong>Offline Mode Active:</strong> Live market data unavailable. Showing last known prices.
                </div>
              </div>
            )}
                    <div className="stats-row">
                        <div className="glass-card stat-box">
                            <label>Total Value</label>
                            <div className="amount">KES {data.summary.total_value.toLocaleString()}</div>
                        </div>
                        <div className="glass-card stat-box">
                            <label>Total Profit/Loss</label>
                            <div className={`amount ${data.summary.total_pnl >= 0 ? 'up' : 'down'}`}>
                                {data.summary.total_pnl >= 0 ? '+' : '-'} KES {Math.abs(data.summary.total_pnl).toLocaleString()}
                            </div>
                        </div>
                        <div className="glass-card stat-box">
                            <label>Risk Score</label>
                            <div className="amount purple">{data.summary.risk_score.toFixed(1)}/100</div>
                        </div>
                    </div>

                    <section className="holdings-section glass-card">
                        <h3>Current Holdings</h3>
                        <table className="holdings-table">
                            <thead>
                                <tr>
                                    <th>Ticker</th>
                                    <th>Quantity</th>
                                    <th>Avg Cost</th>
                                    <th>Value</th>
                                    <th>P/L</th>
                                    <th style={{ textAlign: 'right' }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.holdings.map(h => (
                                    <tr key={h.ticker}>
                                        <td className="ticker-cell">{h.ticker}</td>
                                        <td>{h.qty}</td>
                                        <td>{h.avg_cost.toFixed(2)}</td>
                                        <td>{(h.qty * h.current_price).toLocaleString()}</td>
                                        <td className={h.pnl >= 0 ? 'up' : 'down'}>
                                            {h.pnl >= 0 ? '▲' : '▼'} {h.pnl_pct.toFixed(2)}%
                                        </td>
                                        <td style={{ textAlign: 'right' }}>
                                            <button 
                                                onClick={() => removeTrade(h.ticker)}
                                                style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--accent-red)', border: '1px solid rgba(239,68,68,0.2)', padding: '0.3rem 0.6rem', borderRadius: '0.3rem', fontSize: '0.8rem', cursor: 'pointer' }}
                                            >
                                                Sell
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </section>
                </div>
            )}
            </div>

            {showTradeModal && (
                <TradeModal 
                  onClose={() => setShowTradeModal(false)} 
                  onSuccess={(_msg) => {
                    setShowTradeModal(false);
                    fetchPortfolio();
                  }} 
                />
            )}

            <style jsx="true">{`
        .page { padding: 2rem; max-width: 1400px; margin: 0 auto; }
        .portfolio-layout { display: grid; grid-template-columns: 350px 1fr; gap: 2rem; align-items: start; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        .primary-btn { background: linear-gradient(135deg, var(--accent-emerald), var(--accent-cyan)); color: black; padding: 0.6rem 1.2rem; border-radius: 0.5rem; font-weight: 700; }
        
        .optimizer-card h3 { margin-bottom: 0.5rem; }
        .opt-form { margin-top: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
        .opt-form label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; }
        .opt-form input { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: white; padding: 0.75rem; border-radius: 0.5rem; }
        .opt-btn { background: var(--accent-purple); color: white; padding: 0.75rem; border-radius: 0.5rem; }
        
        .opt-results { margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
        .opt-stat { display: flex; justify-content: space-between; margin-bottom: 1rem; font-weight: 700; }
        .opt-row { display: flex; justify-content: space-between; padding: 0.5rem 0; font-size: 0.9rem; border-bottom: 1px solid rgba(255,255,255,0.03); }

        .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-box { text-align: center; }
        .stat-box label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
        .amount { font-size: 1.6rem; font-weight: 900; margin-top: 0.5rem; font-family: 'monospace'; }
        .amount.up { color: var(--accent-emerald); }
        .amount.down { color: var(--accent-red); }
        .holdings-section { margin-top: 2rem; padding: 0; overflow: hidden; }
        .holdings-section h3 { padding: 1.5rem; border-bottom: 1px solid var(--border); }
        .holdings-table { width: 100%; border-collapse: collapse; }
        .holdings-table th { text-align: left; padding: 1rem 1.5rem; background: rgba(255,255,255,0.03); color: var(--text-secondary); font-size: 0.8rem; }
        .holdings-table td { padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); }
        .ticker-cell { font-weight: 800; color: var(--accent-cyan); }
        .up { color: var(--accent-emerald); }
        .down { color: var(--accent-red); }
      `}</style>
        </div>
    );
}

export default Portfolio;
