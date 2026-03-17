import { useState, useEffect } from 'react';
import { Bell, Info, AlertTriangle, CheckCircle } from 'lucide-react';

function NotificationCenter() {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const fetchNotifications = () => {
      fetch('/api/notifications')
        .then(res => res.json())
        .then(data => setNotifications(data))
        .catch(err => console.error("Notification fetch failed:", err));
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const getIcon = (type) => {
    switch(type) {
      case 'success': return <CheckCircle size={16} className="text-emerald-400" />;
      case 'warning': return <AlertTriangle size={16} className="text-yellow-400" />;
      case 'error': return <AlertTriangle size={16} className="text-red-400" />;
      default: return <Info size={16} className="text-cyan-400" />;
    }
  };

  return (
    <div className="notification-center glass-card">
      <div className="center-header">
        <Bell size={18} />
        <h3>Live Market Alerts</h3>
      </div>
      
      <div className="notifications-list">
        {notifications.length === 0 ? (
          <div className="no-notifications">No recent alerts</div>
        ) : (
          notifications.map(n => (
            <div key={n.id} className={`notification-item ${n.type}`}>
              <div className="notif-icon">{getIcon(n.type)}</div>
              <div className="notif-content">
                <p className="notif-message">{n.message}</p>
                <span className="notif-time">{n.timestamp}</span>
              </div>
            </div>
          ))
        )}
      </div>

      <style jsx="true">{`
        .notification-center {
          height: 100%;
          display: flex;
          flex-direction: column;
          padding: 0;
          overflow: hidden;
        }
        .center-header {
          padding: 1.25rem;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .center-header h3 { font-size: 1rem; margin: 0; }
        .notifications-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
        }
        .no-notifications {
          padding: 2rem;
          text-align: center;
          color: var(--text-secondary);
          font-size: 0.9rem;
        }
        .notification-item {
          display: flex;
          gap: 1rem;
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--border);
          transition: background 0.2s ease;
        }
        .notification-item:hover { background: rgba(255,255,255,0.03); }
        .notif-content { display: flex; flex-direction: column; gap: 0.25rem; }
        .notif-message { font-size: 0.85rem; line-height: 1.4; margin: 0; }
        .notif-time { font-size: 0.7rem; color: var(--text-secondary); }
      `}</style>
    </div>
  );
}

export default NotificationCenter;
