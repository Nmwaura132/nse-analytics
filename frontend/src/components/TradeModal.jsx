import { useState, useEffect } from 'react';

function TradeModal({ onClose, onSuccess }) {
  const [stocks, setStocks] = useState([]);
  const [ticker, setTicker] = useState('');
  const [qty, setQty] = useState('');
  const [price, setPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/stocks')
      .then(r => r.json())
      .then(data => setStocks(data))
      .catch(err => console.error(err));
  }, []);

  const handleTickerChange = (e) => {
    const selected = e.target.value;
    setTicker(selected);
    const stock = stocks.find(s => s.ticker === selected);
    if (stock) {
      setPrice(stock.price.toFixed(2));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/portfolio/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: '1',
          ticker: ticker,
          qty: parseFloat(qty),
          price: parseFloat(price)
        })
      });
      const data = await res.json();
      
      if (data.success) {
        onSuccess(data.message);
      } else {
        setError(data.message || 'Failed to add trade');
      }
    } catch (err) {
      setError('Network error');
    }
    setLoading(false);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="trade-modal fade-in" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>➕ Add Manual Trade</h3>
          <button className="close-btn" onClick={onClose} type="button">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="trade-form">
          <div className="form-group">
            <label>Stock Ticker</label>
            <select value={ticker} onChange={handleTickerChange} required className="form-input">
              <option value="" disabled>Select a stock...</option>
              {stocks.map(s => (
                <option key={s.ticker} value={s.ticker}>{s.ticker} - {s.name}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Quantity</label>
              <input 
                type="number" 
                value={qty} 
                onChange={(e) => setQty(e.target.value)} 
                required 
                min="1"
                placeholder="100"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Price (KES)</label>
              <input 
                type="number" 
                value={price} 
                onChange={(e) => setPrice(e.target.value)} 
                required 
                step="0.01"
                placeholder="15.50"
                className="form-input"
              />
            </div>
          </div>

          {error && <div className="error-msg">{error}</div>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Adding...' : 'Confirm Trade'}
          </button>
        </form>
      </div>

      <style jsx="true">{`
        .modal-overlay {
          position: fixed; inset: 0; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(4px);
          display: flex; align-items: center; justify-content: center; z-index: 2000;
        }
        .trade-modal {
          background: var(--bg-slate-900); border: 1px solid rgba(255, 255, 255, 0.1);
          padding: 2rem; border-radius: 1rem; width: 100%; max-width: 450px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        .modal-header h3 { margin: 0; font-size: 1.25rem; }
        .close-btn { background: none; border: none; color: white; opacity: 0.5; cursor: pointer; font-size: 1.25rem; }
        .close-btn:hover { opacity: 1; }
        
        .trade-form { display: flex; flex-direction: column; gap: 1.5rem; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
        .form-input {
          width: 100%; background: rgba(255, 255, 255, 0.05); color: white;
          border: 1px solid rgba(255, 255, 255, 0.1); padding: 0.75rem 1rem;
          border-radius: 0.5rem; outline: none; transition: border-color 0.2s ease;
        }
        .form-input:focus { border-color: var(--accent-emerald); }
        .form-input option { background: var(--bg-slate-900); color: white; }
        
        .error-msg { background: rgba(244, 63, 94, 0.1); color: var(--accent-red); padding: 0.75rem; border-radius: 0.5rem; font-size: 0.85rem; border: 1px solid rgba(244, 63, 94, 0.2); }
        
        .submit-btn {
          background: linear-gradient(135deg, var(--accent-emerald), #059669);
          color: white; border: none; padding: 1rem; border-radius: 0.5rem; font-weight: 700; cursor: pointer; transition: transform 0.2s;
        }
        .submit-btn:hover:not(:disabled) { transform: translateY(-2px); }
        .submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }
      `}</style>
    </div>
  );
}

export default TradeModal;
