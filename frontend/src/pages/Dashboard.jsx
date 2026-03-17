import { useState, useEffect } from 'react';
import NotificationCenter from '../components/NotificationCenter';
import StockModal from '../components/StockModal';

function Dashboard({ searchQuery }) {
    const [stocks, setStocks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTicker, setSelectedTicker] = useState(null);

    useEffect(() => {
        fetch('/api/stocks')
            .then(res => res.json())
            .then(data => {
                setStocks(data);
                setLoading(false);
            })
            .catch(err => console.error(err));
    }, []);

    const filteredStocks = stocks.filter(stock => 
        !searchQuery || 
        stock.ticker.toLowerCase().includes(searchQuery.toLowerCase()) || 
        stock.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const topGainer = stocks.reduce((max, stock) => (stock.change_pct > (max?.change_pct || -Infinity) ? stock : max), null);
    const gainersCount = stocks.filter(s => s.change_pct >= 0).length;
    const losersCount = stocks.length - gainersCount;
    const sentiment = gainersCount > losersCount ? 'Bullish' : (gainersCount < losersCount ? 'Bearish' : 'Neutral');
    const alertsCount = stocks.filter(s => s.signal && (s.signal.includes('Buy') || s.signal.includes('Bargain'))).length;

    return (
        <div className="page fade-in">
            <header className="page-header">
                <h2>Market Dashboard</h2>
                <div className="market-status">
                    <span className="status-indicator"></span> Market Open
                </div>
            </header>

            <div className="stats-grid">
                <div className="glass-card stat-card">
                    <label>Top Gainer</label>
                    <div className="value green">
                        {topGainer ? `${topGainer.ticker} (+${topGainer.change_pct.toFixed(2)}%)` : '--'}
                    </div>
                </div>
                <div className="glass-card stat-card">
                    <label>Market Sentiment</label>
                    <div className={`value ${sentiment === 'Bullish' ? 'cyan' : 'red'}`}>
                        {stocks.length > 0 ? sentiment : '--'}
                    </div>
                </div>
                <div className="glass-card stat-card">
                    <label>Alerts</label>
                    <div className="value purple">{alertsCount} New Picks</div>
                </div>
            </div>

            <div className="main-layout">
        <section className="stocks-section">
          <h3>Live NSE Tickers</h3>
          {loading ? (
            <div className="loading">Fetching market data...</div>
          ) : (
            <div className="stock-grid">
              {filteredStocks.map(stock => (
                <div 
                  key={stock.ticker} 
                  className="glass-card stock-card"
                  onClick={() => setSelectedTicker(stock.ticker)}
                >
                  <div className="stock-info">
                    <span className="ticker">{stock.ticker}</span>
                    <span className="name">{stock.name}</span>
                  </div>
                  <div className="stock-price">
                    <span className="price">KES {stock.price.toFixed(2)}</span>
                    <span className={`change ${stock.change >= 0 ? 'up' : 'down'}`}>
                      {stock.change >= 0 ? '▲' : '▼'} {Math.abs(stock.change_pct || 0).toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
              {filteredStocks.length === 0 && (
                <div style={{ color: 'var(--text-secondary)', padding: '2rem' }}>No stocks matched your search.</div>
              )}
            </div>
          )}
        </section>

        <aside className="alerts-sidebar">
          <NotificationCenter />
        </aside>
      </div>

      {selectedTicker && (
        <StockModal ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />
      )}

      <style jsx="true">{`
        .page { padding: 2rem; max-width: 1400px; margin: 0 auto; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        .market-status { font-size: 0.9rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.5rem; }
        .status-indicator { width: 8px; height: 8px; background: var(--accent-emerald); border-radius: 50%; box-shadow: 0 0 8px var(--accent-emerald); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-secondary); }
        .stat-card .value { font-size: 1.5rem; font-weight: 800; margin-top: 0.5rem; }
        .value.green { color: var(--accent-emerald); }
        .value.cyan { color: var(--accent-cyan); }
        .value.purple { color: var(--accent-purple); }
        
        .main-layout { display: grid; grid-template-columns: 1fr 400px; gap: 2rem; }
        .stocks-section h3 { margin-bottom: 1.5rem; }
        .stock-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
        .stock-card { display: flex; justify-content: space-between; align-items: center; transition: transform 0.2s ease; cursor: pointer; }
        .stock-card:hover { transform: translateY(-5px); border-color: rgba(255,255,255,0.2); }
        .stock-info { display: flex; flex-direction: column; }
        .ticker { font-weight: 800; font-size: 1.1rem; }
        .name { font-size: 0.8rem; color: var(--text-secondary); }
        .stock-price { text-align: right; }
        .price { display: block; font-weight: 700; font-family: 'monospace'; }
        .change { font-size: 0.85rem; font-weight: 600; }
        .change.up { color: var(--accent-emerald); }
        .change.down { color: var(--accent-red); }
      `}</style>
        </div>
    );
}

export default Dashboard;
