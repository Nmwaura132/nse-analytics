import { useState } from 'react';
import Plot from 'react-plotly.js';

function DataScience() {
  const [ticker, setTicker] = useState('SCOM');
  const [strategy, setStrategy] = useState('MACD');
  const [capital, setCapital] = useState(100000);
  const [data, setData] = useState({ history: [], ml: null, bt: null });
  const [loading, setLoading] = useState(false);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const [hist, pred, bt] = await Promise.all([
        fetch(`/api/history/${ticker}`).then(r => r.json()),
        fetch(`/api/predict/${ticker}`).then(r => r.json()),
        fetch(`/api/backtest/${ticker}?strategy=${strategy}&initial_capital=${capital}`).then(r => r.json())
      ]);
      setData({ history: hist, ml: pred, bt: bt });
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const plotData = [
    {
      x: data.history.map(d => d.Date),
      open: data.history.map(d => d.Open),
      high: data.history.map(d => d.High),
      low: data.history.map(d => d.Low),
      close: data.history.map(d => d.Close),
      type: 'candlestick',
      name: ticker,
      increasing: { line: { color: '#10b981' } },
      decreasing: { line: { color: '#ef4444' } }
    }
  ];
  
  // Add Equity Curve if available
  if (data.bt?.equity_curve) {
    plotData.push({
      x: data.bt.equity_curve.map(c => c.date),
      y: data.bt.equity_curve.map(c => c.strategy_value),
      type: 'scatter',
      mode: 'lines',
      name: 'Strategy Equity',
      line: { color: '#8b5cf6', width: 2 },
      yaxis: 'y2'
    });
  }

  const plotLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#94a3b8' },
    margin: { l: 40, r: 60, t: 20, b: 40 },
    showlegend: true,
    xaxis: { gridcolor: '#1e293b', rangeslider: { visible: false } },
    yaxis: { gridcolor: '#1e293b', title: 'Price' },
    yaxis2: { overlaying: 'y', side: 'right', title: 'Equity', showgrid: false }
  };
  
  return (
    <div className="page fade-in">
      <header className="page-header">
        <h2>Data Science & ML Insights</h2>
      </header>

      <div className="controls glass-card" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '1rem' }}>
        <input 
          type="text" 
          value={ticker} 
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          className="ticker-input"
          placeholder="Enter Ticker..."
          style={{ maxWidth: '150px' }}
        />
        <select 
          value={strategy} 
          onChange={(e) => setStrategy(e.target.value)}
          className="ticker-input"
        >
          <option value="MACD">MACD</option>
          <option value="RSI">RSI</option>
          <option value="SMA_Crossover">SMA Crossover</option>
          <option value="Bollinger">Bollinger Bands</option>
        </select>
        <input 
          type="number" 
          value={capital} 
          onChange={(e) => setCapital(e.target.value)}
          className="ticker-input"
          placeholder="Initial Capital"
          style={{ maxWidth: '180px' }}
        />
        <button 
          className="analyze-btn" 
          onClick={runAnalysis}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Run Models & Backtest'}
        </button>
      </div>

      <div className="ds-grid">
        <div className="glass-card chart-container">
          {data.history.length > 0 ? (
            <Plot
              data={plotData}
              layout={plotLayout}
              useResizeHandler={true}
              style={{ width: "100%", height: "100%" }}
            />
          ) : (
            <div className="chart-placeholder">
              <span className="icon">📊</span>
              <p>Enter a ticker and click 'Run ML Models' to start</p>
            </div>
          )}
        </div>

        <div className="glass-card side-metrics">
          <section className="metric-group">
            <label>ML Price Forecast</label>
            <div className="metric-item">
              <span>Next Close:</span>
              <span className="value cyan">
                {data.ml?.price_forecast?.predicted_price?.toFixed(2) || '--.--'}
              </span>
            </div>
            <div className="metric-item">
              <span>Model MSE:</span>
              <span className="value">
                {data.ml?.price_forecast?.mse?.toFixed(4) || '0.0000'}
              </span>
            </div>
          </section>

          <section className="metric-group">
            <label>Strategy Backtest ({data.bt?.strategy || 'MACD'})</label>
            <div className="metric-item">
              <span>Alpha:</span>
              <span className={`value ${data.bt?.metrics?.alpha >= 0 ? 'green' : 'red'}`}>
                {data.bt?.metrics?.alpha?.toFixed(2) || '0.0'}%
              </span>
            </div>
            <div className="metric-item">
              <span>Win Rate:</span>
              <span className="value">
                {data.bt?.metrics?.win_rate_pct?.toFixed(1) || '0.0'}%
              </span>
            </div>
          </section>
        </div>
      </div>

      <style jsx="true">{`
        .page { padding: 2rem; max-width: 1200px; margin: 0 auto; }
        .page-header { margin-bottom: 2rem; }
        .controls { display: flex; gap: 1rem; margin-bottom: 2rem; }
        .ticker-input { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: white; padding: 0.8rem 1.2rem; border-radius: 0.5rem; flex: 1; outline: none; }
        .ticker-input:focus { border-color: var(--accent-cyan); }
        .ticker-input option { background: var(--bg-slate-900); color: white; }
        .analyze-btn { background: linear-gradient(135deg, var(--accent-purple), #7e22ce); color: white; padding: 0.8rem 2rem; border-radius: 0.5rem; font-weight: 700; border: none; cursor: pointer; transition: transform 0.2s; white-space: nowrap; }
        .analyze-btn:hover:not(:disabled) { transform: translateY(-2px); }
        .ds-grid { display: grid; grid-template-columns: 3fr 1fr; gap: 1.5rem; }
        .chart-placeholder { min-height: 500px; display: flex; align-items: center; justify-content: center; text-align: center; border-style: dashed; }
        .placeholder-content .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }
        .placeholder-content p { color: var(--text-secondary); }
        .hint { font-size: 0.8rem; margin-top: 1rem; background: rgba(139, 92, 246, 0.1); padding: 0.5rem; border-radius: 0.3rem; }
        .metric-group { margin-bottom: 2rem; }
        .metric-group label { font-size: 0.7rem; text-transform: uppercase; color: var(--text-secondary); border-bottom: 1px solid var(--border); display: block; padding-bottom: 0.5rem; margin-bottom: 1rem; }
        .metric-item { display: flex; justify-content: space-between; margin-bottom: 0.75rem; font-size: 0.9rem; }
        .value { font-weight: 700; }
        .cyan { color: var(--accent-cyan); }
        .green { color: var(--accent-emerald); }
      `}</style>
    </div>
  );
}

export default DataScience;
