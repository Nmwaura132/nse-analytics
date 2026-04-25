import React from 'react';
import { NSE_STOCKS, NEWS } from '../data.js';
import { Icon } from '../icons.jsx';
import { Badge } from '../ui.jsx';

const NewsPage = ({ openStock }) => {
  return (
    <div className="anim-fade" style={{ maxWidth: 980, margin: '0 auto', padding: '24px 24px 60px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' }}>News & Insights</h1>
        <p style={{ fontSize: 14, color: 'rgba(148,163,184,0.85)', marginTop: 6 }}>Curated for your watchlist · Updated continuously</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {NEWS.map((n, i) => {
          const stock = NSE_STOCKS.find(s => s.ticker === n.tag);
          return (
            <div key={n.id} className="glass lift anim-fade-up" style={{ padding: 18, animationDelay: `${i * 40}ms`, cursor: stock ? 'pointer' : 'default' }}
              onClick={() => stock && openStock(stock)}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div style={{ width: 44, height: 44, flexShrink: 0, borderRadius: 11,
                  background: 'linear-gradient(135deg, rgba(16,185,129,0.18), rgba(6,182,212,0.1))',
                  border: '1px solid rgba(16,185,129,0.25)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon name="news" size={18} color="#10b981" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                    <Badge color={stock ? 'emerald' : 'cyan'} size="sm">{n.tag}</Badge>
                    <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.7)' }}>{n.source} · {n.time} ago</span>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.35, letterSpacing: '-0.01em' }}>{n.headline}</h3>
                </div>
                {stock && <Icon name="chevron-right" size={16} color="rgba(148,163,184,0.5)" />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NewsPage;
