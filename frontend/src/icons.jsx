import React from 'react';

export const Icon = ({ name, size = 18, color = 'currentColor', className = '', strokeWidth = 2 }) => {
  const props = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: color, strokeWidth, strokeLinecap: 'round', strokeLinejoin: 'round', className };
  switch (name) {
    case 'candlestick':
      return (
        <svg {...props}>
          <line x1="6" y1="3" x2="6" y2="21" />
          <rect x="3" y="7" width="6" height="9" fill={color} />
          <line x1="18" y1="3" x2="18" y2="21" />
          <rect x="15" y="10" width="6" height="8" fill={color} fillOpacity="0.4" />
        </svg>
      );
    case 'home':       return <svg {...props}><path d="M3 12L12 3l9 9" /><path d="M5 10v10h14V10" /></svg>;
    case 'briefcase':  return <svg {...props}><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2" /></svg>;
    case 'chart':      return <svg {...props}><path d="M3 3v18h18" /><path d="M7 14l3-3 3 3 5-7" /></svg>;
    case 'news':       return <svg {...props}><path d="M4 4h13a2 2 0 012 2v12a2 2 0 01-2 2H4z" /><path d="M8 8h8M8 12h8M8 16h5" /></svg>;
    case 'user':       return <svg {...props}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-7 8-7s8 3 8 7" /></svg>;
    case 'bell':       return <svg {...props}><path d="M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 004 0" /></svg>;
    case 'trend':      return <svg {...props}><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg>;
    case 'spark':      return <svg {...props}><path d="M12 2l2.5 7H22l-6 4.5 2.5 7-6.5-4.5L5 20.5l2.5-7L1 9h7.5z" fill={color} /></svg>;
    case 'xp':         return <svg {...props}><path d="M12 2l3 7 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z" fill={color} /></svg>;
    case 'fire':       return <svg {...props}><path d="M12 2c0 4-3 5-3 9a3 3 0 006 0c0-1.5-1-2.5-1-4 3 1 5 4 5 7a7 7 0 01-14 0c0-5 4-7 7-12z" fill={color} /></svg>;
    case 'arrow-up':   return <svg {...props}><path d="M12 19V5M5 12l7-7 7 7" /></svg>;
    case 'arrow-down': return <svg {...props}><path d="M12 5v14M5 12l7 7 7-7" /></svg>;
    case 'arrow-right':return <svg {...props}><path d="M5 12h14M13 5l7 7-7 7" /></svg>;
    case 'plus':       return <svg {...props}><path d="M12 5v14M5 12h14" /></svg>;
    case 'check':      return <svg {...props}><path d="M5 13l4 4L19 7" /></svg>;
    case 'x':          return <svg {...props}><path d="M6 6l12 12M18 6L6 18" /></svg>;
    case 'lock':       return <svg {...props}><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>;
    case 'mail':       return <svg {...props}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 7 9-7" /></svg>;
    case 'eye':        return <svg {...props}><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>;
    case 'sparkles':   return <svg {...props}><path d="M12 3l1.5 4 4 1.5-4 1.5L12 14l-1.5-4L6.5 8.5l4-1.5z" fill={color} /><path d="M19 14l.8 2 2 .8-2 .8L19 20l-.8-2-2-.8 2-.8z" fill={color} /></svg>;
    case 'lightning':  return <svg {...props}><path d="M13 2L4 14h7l-2 8 9-12h-7z" fill={color} /></svg>;
    case 'trophy':     return <svg {...props}><path d="M8 4h8v6a4 4 0 01-8 0z" fill={color} fillOpacity="0.4" /><path d="M8 4H5v3a3 3 0 003 3M16 4h3v3a3 3 0 01-3 3M9 14h6v3H9zM7 21h10" /></svg>;
    case 'shield':     return <svg {...props}><path d="M12 2l8 3v7c0 5-4 9-8 10-4-1-8-5-8-10V5z" /></svg>;
    case 'menu':       return <svg {...props}><path d="M4 6h16M4 12h16M4 18h16" /></svg>;
    case 'search':     return <svg {...props}><circle cx="11" cy="11" r="7" /><path d="M21 21l-5-5" /></svg>;
    case 'settings':   return <svg {...props}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z" /></svg>;
    case 'logout':     return <svg {...props}><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" /></svg>;
    case 'telegram':   return <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M21.94 4.32L18.7 19.62c-.24 1.08-.88 1.34-1.78.84l-4.92-3.62-2.37 2.28c-.26.26-.48.48-.99.48l.35-5.02 9.13-8.25c.4-.35-.09-.55-.61-.2L6.21 13.05.34 11.18c-1.27-.4-1.3-1.27.27-1.88L20.28 2.6c1.06-.4 1.99.25 1.66 1.72z"/></svg>;
    case 'mpesa':      return <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M3 6h18v12H3z" fillOpacity="0.2"/><path d="M3 6h18v12H3z" fill="none" stroke={color} strokeWidth="2"/><circle cx="8" cy="12" r="2" fill={color}/><circle cx="16" cy="12" r="2" fill={color}/></svg>;
    case 'crown':      return <svg {...props}><path d="M3 7l4 4 5-7 5 7 4-4-2 12H5z" fill={color} fillOpacity="0.4"/></svg>;
    case 'rocket':     return <svg {...props}><path d="M5 19l4-1 11-11a3 3 0 00-3-3L6 15l-1 4z" /><path d="M14 6l3 3" /><path d="M5 19l-2 2" /></svg>;
    case 'circle-dot': return <svg {...props}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="2" fill={color}/></svg>;
    case 'chevron-down':  return <svg {...props}><path d="M6 9l6 6 6-6" /></svg>;
    case 'chevron-right': return <svg {...props}><path d="M9 6l6 6-6 6" /></svg>;
    case 'play':       return <svg {...props}><path d="M6 4l14 8-14 8z" fill={color}/></svg>;
    case 'target':     return <svg {...props}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" fill={color}/></svg>;
    case 'brain':      return <svg {...props}><path d="M9 4a3 3 0 00-3 3v1a3 3 0 00-2 3 3 3 0 002 3 3 3 0 003 3v0a3 3 0 003-3V7a3 3 0 00-3-3zM15 4a3 3 0 013 3v1a3 3 0 012 3 3 3 0 01-2 3 3 3 0 01-3 3v0a3 3 0 01-3-3V7a3 3 0 013-3z" /></svg>;
    case 'zap':        return <svg {...props}><path d="M13 2L4 14h7l-2 8 9-12h-7z" /></svg>;
    case 'gift':       return <svg {...props}><rect x="3" y="8" width="18" height="13" rx="1" /><path d="M3 12h18M12 8v13M12 8c-2-3-6-3-6 0s3 0 6 0zM12 8c2-3 6-3 6 0s-3 0-6 0z" /></svg>;
    case 'users':      return <svg {...props}><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" /></svg>;
    case 'coins':      return <svg {...props}><circle cx="8" cy="8" r="5" /><path d="M21 21c0-2.76-2.24-5-5-5s-5 2.24-5 5" /><path d="M21 8c0-2.76-2.24-5-5-5" /><circle cx="16" cy="8" r="5" /></svg>;
    case 'alert':      return <svg {...props}><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>;
    case 'refresh':    return <svg {...props}><path d="M23 4v6h-6M1 20v-6h6" /><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" /></svg>;
    default: return <svg {...props}><circle cx="12" cy="12" r="9" /></svg>;
  }
};
