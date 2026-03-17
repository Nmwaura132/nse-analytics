import { Link, useLocation } from 'react-router-dom';

function Navbar({ searchQuery, setSearchQuery }) {
    const location = useLocation();

    const isActive = (path) => location.pathname === path;

    const handleRefresh = async () => {
        try {
            await fetch('/api/refresh', { method: 'POST' });
            window.location.reload();
        } catch (e) {
            console.error("Refresh failed:", e);
        }
    };

    return (
        <nav className="glass-navigation">
            <div className="nav-content">
                <div className="logo-section">
                    <span className="logo-icon">📈</span>
                    <h1 className="gradient-text">NSE PRO</h1>
                </div>

                <div className="links-section">
                    <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>Dashboard</Link>
                    <Link to="/portfolio" className={`nav-link ${isActive('/portfolio') ? 'active' : ''}`}>Portfolio</Link>
                    <Link to="/datascience" className={`nav-link ${isActive('/datascience') ? 'active' : ''}`}>Data Science</Link>
                </div>

                <div className="search-section" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    {location.pathname === '/' && (
                        <input 
                            type="text" 
                            placeholder="Search Ticker..." 
                            className="search-input" 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    )}
                    <button onClick={handleRefresh} className="refresh-btn">
                        <span>🔄</span> Refresh
                    </button>
                </div>
            </div>

            <style jsx="true">{`
        .glass-navigation {
          background: rgba(15, 23, 42, 0.8);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          padding: 1rem 2rem;
          sticky top: 0;
          z-index: 1000;
        }
        .nav-content {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .logo-section {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .logo-section h1 {
          font-size: 1.5rem;
          font-weight: 800;
          letter-spacing: -0.025em;
        }
        .links-section {
          display: flex;
          gap: 2rem;
        }
        .search-input {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 2rem;
          outline: none;
          width: 200px;
          transition: all 0.2s ease;
        }
        .search-input:focus {
          width: 250px;
          background: rgba(255, 255, 255, 0.1);
          border-color: var(--accent-cyan);
        }
        .refresh-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 0.5rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 500;
          transition: all 0.2s ease;
        }
        .refresh-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          border-color: var(--accent-cyan);
        }
      `}</style>
        </nav>
    );
}

export default Navbar;
