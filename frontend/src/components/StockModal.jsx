import { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

function StockModal({ ticker, onClose }) {
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (!ticker) { return; }
    
    setLoading(true);
    Promise.all([
      fetch(`/api/stock/${ticker}`).then(r => r.json()),
      fetch(`/api/history/${ticker}`).then(r => r.json())
    ]).then(([stockData, histData]) => {
      setData(stockData);
      setHistory(histData.error ? [] : histData);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [ticker]);

  const handleAddTrade = async () => {
    const qtyStr = window.prompt(`Add ${ticker} to simulator.\n\nEnter Quantity:`, "100");
    if (!qtyStr) { return; }
    const qty = parseFloat(qtyStr);
    if (isNaN(qty) || qty <= 0) { return alert('Invalid quantity'); }
    
    setAdding(true);
    try {
      const res = await fetch('/api/portfolio/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker,
          qty: qty,
          price: data.price,
          user_id: '1'
        })
      });
      const result = await res.json();
      if (result.success) {
        alert(`Bought ${qty} ${ticker} @ ${data.price}`);
        onClose();
      } else {
        alert(result.message);
      }
    } catch (_e) {
      alert('Network error adding trade');
    }
    setAdding(false);
  };

  if (!ticker) { return null; }

  const plotData = history.length > 0 ? [{
    x: history.map(d => d.Date),
    y: history.map(d => d.Close),
    type: 'scatter',
    mode: 'lines',
    line: { color: '#10b981', width: 2 },
    fill: 'tozeroy',
    fillcolor: 'rgba(16, 185, 129, 0.1)'
  }] : [];

  const plotLayout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8' },
    margin: { l: 0, r: 0, t: 10, b: 0 },
    showlegend: false,
    xaxis: { showgrid: false, display: false, visible: false },
    yaxis: { showgrid: false, display: false, visible: false },
    height: 150
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel fade-in" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">{ticker}</h2>
            <p className="modal-subtitle">{loading ? 'Fetching market data...' : data?.name}</p>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="loading" style={{ padding: '2rem', textAlign: 'center' }}>Loading analysis...</div>
        ) : !data ? (
          <div className="loading" style={{ padding: '2rem', textAlign: 'center', color: 'var(--accent-red)' }}>Failed to load stock data.</div>
        ) : (
          <div className="modal-content">
            {/* Header Stats */}
            <div className="detailed-stats-grid">
                <div className="glass-card stat-mini">
                    <label>Current Price</label>
                    <div className="value">KES {data.price?.toFixed(2) || '--'}</div>
                    <div className={data.change >= 0 ? 'green block' : 'red block'}>
                        {data.change >= 0 ? '+' : ''}{data.change?.toFixed(2)} ({data.change_pct?.toFixed(2)}%)
                    </div>
                </div>
                <div className="glass-card stat-mini">
                    <label>Composite Score</label>
                    <div className="value purple">{data.composite_score?.toFixed(0) || '--'}/100</div>
                    <div className="block">{data.signal || 'Neutral'}</div>
                </div>
                <div className="glass-card stat-mini">
                    <label>Day Range</label>
                    <div className="value">{data.day_low?.toFixed(2) || '--'} - {data.day_high?.toFixed(2) || '--'}</div>
                </div>
                <div className="glass-card stat-mini">
                    <label>Volume</label>
                    <div className="value">{data.volume?.toLocaleString() || '--'}</div>
                </div>
            </div>

            {/* Fundamentals */}
            <h3 className="section-title">Fundamental & Technical Analysis</h3>
            <div className="fundamentals-grid">
                <div className="glass-card param-box">
                    <label>P/E Ratio</label>
                    <div>{data.valuation?.pe_ratio?.toFixed(2) || '--'}</div>
                </div>
                <div className="glass-card param-box">
                    <label>Dividend Yield</label>
                    <div>{data.valuation?.dividend_yield?.toFixed(1) || '--'}%</div>
                </div>
                <div className="glass-card param-box">
                    <label>Risk Score</label>
                    <div className={data.risk_score > 70 ? 'red' : 'green'}>
                        {data.risk_score?.toFixed(0) || '--'}/100
                    </div>
                </div>
                <div className="glass-card param-box">
                    <label>Graham Number</label>
                    <div>{data.valuation?.graham_number?.toFixed(2) || '--'}</div>
                </div>
                <div className="glass-card param-box" style={{ gridColumn: 'span 2' }}>
                    <label>Intrinsic Valuation</label>
                    <div className="badge purple" style={{ marginTop: '0.2rem', display: 'inline-block' }}>
                        {data.valuation?.intrinsic_status || 'Unknown'}
                    </div>
                </div>
            </div>

            <div className="glass-card chart-mini-container">
              {history.length > 0 ? (
                <Plot
                    data={plotData}
                    layout={plotLayout}
                    config={{ displayModeBar: false }}
                    useResizeHandler={true}
                    style={{ width: "100%", height: "100%" }}
                />
              ) : (
                <div className="loading" style={{ padding: '2rem', textAlign: 'center' }}>No chart data</div>
              )}
            </div>

            <button 
                className="add-trade-btn" 
                onClick={handleAddTrade}
                disabled={adding}
            >
                {adding ? 'Adding...' : '➕ Add to Portfolio'}
            </button>
          </div>
        )}
      </div>

      <style jsx="true">{`
        .modal-overlay {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(4px);
            display: flex; justify-content: flex-end;
            z-index: 2000;
        }
        .modal-panel {
            width: 500px; max-width: 100%; height: 100%;
            background: var(--bg-slate-900);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            display: flex; flex-direction: column;
            overflow-y: auto;
        }
        .modal-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; }
        .modal-title { font-size: 2rem; font-weight: 800; margin: 0; }
        .modal-subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.2rem; }
        .close-btn { background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; opacity: 0.5; transition: opacity 0.2s; }
        .close-btn:hover { opacity: 1; }
        
        .detailed-stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }
        .stat-mini { padding: 1rem; }
        .stat-mini label { font-size: 0.7rem; text-transform: uppercase; color: var(--text-secondary); }
        .stat-mini .value { font-size: 1.3rem; font-weight: 800; font-family: monospace; margin: 0.2rem 0; }
        .block { font-size: 0.8rem; font-weight: 600; }
        
        .section-title { font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 1rem; letter-spacing: 1px; }
        .fundamentals-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }
        .param-box { padding: 0.8rem; text-align: center; }
        .param-box label { font-size: 0.65rem; color: var(--text-secondary); text-transform: uppercase; display: block; margin-bottom: 0.3rem; }
        .param-box div { font-family: monospace; font-size: 1rem; font-weight: 600; }
        .badge { padding: 0.2rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem !important; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.3); }
        
        .chart-mini-container { height: 180px; padding: 1rem; margin-bottom: 2rem; }
        .add-trade-btn {
            width: 100%; padding: 1rem;
            background: linear-gradient(135deg, var(--accent-emerald), #059669);
            color: white; border: none; border-radius: 0.5rem;
            font-size: 1rem; font-weight: 700; cursor: pointer;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .add-trade-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4); }
        .add-trade-btn:disabled { opacity: 0.7; cursor: not-allowed; }
        
        .green { color: var(--accent-emerald); }
        .red { color: var(--accent-red); }
        .purple { color: var(--accent-purple); }
      `}</style>
    </div>
  );
}

export default StockModal;
