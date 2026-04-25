import React from 'react';

export const Sparkline = ({ data, color = '#10b981', width = 80, height = 28, fill = true }) => {
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const pts = data.map((v, i) => [i * step, height - ((v - min) / range) * (height - 4) - 2]);
  const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const area = path + ` L ${width} ${height} L 0 ${height} Z`;
  const id = 'spark-' + color.replace('#', '');
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={area} fill={`url(#${id})`} />}
      <path d={path} fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

export const CandlestickChart = ({ data, width = 700, height = 320, showVolume = true, predicted = null }) => {
  const padding = { top: 16, right: 56, bottom: showVolume ? 60 : 16, left: 8 };
  const w = width - padding.left - padding.right;
  const h = height - padding.top - padding.bottom;
  const allHi = Math.max(...data.map(d => d.high), predicted ? predicted.high : -Infinity);
  const allLo = Math.min(...data.map(d => d.low), predicted ? predicted.low : Infinity);
  const range = allHi - allLo;
  const candleWidth = Math.max(2, (w / data.length) * 0.7);
  const step = w / data.length;
  const yScale = v => padding.top + h - ((v - allLo) / range) * h;
  const maxVol = Math.max(...data.map(d => d.vol));
  const volH = 40;
  const volTop = height - padding.bottom + 12;
  const gridPrices = [];
  for (let i = 0; i <= 4; i++) gridPrices.push(allLo + (range * i / 4));

  return (
    <svg width={width} height={height} style={{ display: 'block', maxWidth: '100%' }}>
      <defs>
        <linearGradient id="predZone" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.25" />
        </linearGradient>
      </defs>
      {gridPrices.map((p, i) => (
        <g key={i}>
          <line x1={padding.left} x2={width - padding.right} y1={yScale(p)} y2={yScale(p)}
            stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4" />
          <text x={width - padding.right + 6} y={yScale(p) + 4} fontSize="10" fill="rgba(148,163,184,0.7)" fontFamily="JetBrains Mono">
            {p.toFixed(2)}
          </text>
        </g>
      ))}
      {data.map((c, i) => {
        const x = padding.left + i * step + step / 2;
        const up = c.close >= c.open;
        const color = up ? '#10b981' : '#ef4444';
        const yO = yScale(c.open), yC = yScale(c.close);
        const yH = yScale(c.high), yL = yScale(c.low);
        return (
          <g key={i}>
            <line x1={x} x2={x} y1={yH} y2={yL} stroke={color} strokeWidth="1" />
            <rect x={x - candleWidth/2} y={Math.min(yO, yC)} width={candleWidth}
              height={Math.max(1, Math.abs(yC - yO))} fill={color} opacity="0.95" />
            {showVolume && (
              <rect x={x - candleWidth/2} y={volTop + volH - (c.vol / maxVol) * volH}
                width={candleWidth} height={(c.vol / maxVol) * volH}
                fill={color} opacity="0.35" />
            )}
          </g>
        );
      })}
      {predicted && (
        <g>
          <rect x={padding.left + data.length * step} y={yScale(predicted.high)}
            width={step * 3} height={yScale(predicted.low) - yScale(predicted.high)}
            fill="url(#predZone)" />
          <line x1={padding.left + data.length * step} x2={padding.left + data.length * step + step * 3}
            y1={yScale(predicted.close)} y2={yScale(predicted.close)}
            stroke="#8b5cf6" strokeWidth="2" strokeDasharray="3 3" />
          <circle cx={padding.left + data.length * step + step * 1.5} cy={yScale(predicted.close)} r="4" fill="#8b5cf6">
            <animate attributeName="r" values="4;7;4" dur="2s" repeatCount="indefinite" />
          </circle>
        </g>
      )}
    </svg>
  );
};

export const LineChart = ({ series, width = 600, height = 220, showAxis = true }) => {
  const padding = { top: 16, right: 16, bottom: showAxis ? 24 : 8, left: showAxis ? 40 : 8 };
  const w = width - padding.left - padding.right;
  const h = height - padding.top - padding.bottom;
  const allValues = series.flatMap(s => s.data);
  const min = Math.min(...allValues), max = Math.max(...allValues);
  const range = max - min || 1;
  return (
    <svg width={width} height={height} style={{ display: 'block', maxWidth: '100%' }}>
      <defs>
        {series.map((s, i) => (
          <linearGradient key={i} id={`line-grad-${i}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={s.color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={s.color} stopOpacity="0" />
          </linearGradient>
        ))}
      </defs>
      {showAxis && [0, 0.25, 0.5, 0.75, 1].map((t, i) => (
        <g key={i}>
          <line x1={padding.left} x2={width - padding.right}
            y1={padding.top + h * t} y2={padding.top + h * t}
            stroke="rgba(255,255,255,0.04)" />
          <text x={padding.left - 6} y={padding.top + h * t + 4} fontSize="10"
            fill="rgba(148,163,184,0.6)" textAnchor="end" fontFamily="JetBrains Mono">
            {(max - range * t).toFixed(0)}
          </text>
        </g>
      ))}
      {series.map((s, si) => {
        const step = w / (s.data.length - 1);
        const pts = s.data.map((v, i) => [
          padding.left + i * step,
          padding.top + h - ((v - min) / range) * h
        ]);
        const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
        const area = path + ` L ${pts[pts.length-1][0]} ${padding.top + h} L ${pts[0][0]} ${padding.top + h} Z`;
        return (
          <g key={si}>
            <path d={area} fill={`url(#line-grad-${si})`} />
            <path d={path} fill="none" stroke={s.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </g>
        );
      })}
    </svg>
  );
};

export const DonutChart = ({ data, size = 180, thickness = 28, centerLabel, centerSubLabel }) => {
  const total = data.reduce((s, d) => s + d.value, 0);
  const r = size / 2 - thickness / 2;
  const cx = size / 2, cy = size / 2;
  let cum = 0;
  return (
    <svg width={size} height={size} style={{ display: 'block' }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={thickness} />
      {data.map((d, i) => {
        const start = cum / total;
        cum += d.value;
        const end = cum / total;
        const startAngle = start * Math.PI * 2 - Math.PI / 2;
        const endAngle = end * Math.PI * 2 - Math.PI / 2;
        const x1 = cx + r * Math.cos(startAngle), y1 = cy + r * Math.sin(startAngle);
        const x2 = cx + r * Math.cos(endAngle), y2 = cy + r * Math.sin(endAngle);
        const large = end - start > 0.5 ? 1 : 0;
        return (
          <path key={i}
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`}
            stroke={d.color} strokeWidth={thickness} fill="none" strokeLinecap="butt" />
        );
      })}
      {centerLabel && (
        <text x={cx} y={cy - 2} textAnchor="middle" fontSize="20" fill="white" fontWeight="700" fontFamily="JetBrains Mono">{centerLabel}</text>
      )}
      {centerSubLabel && (
        <text x={cx} y={cy + 16} textAnchor="middle" fontSize="10" fill="rgba(148,163,184,0.8)" fontWeight="500">{centerSubLabel}</text>
      )}
    </svg>
  );
};

export const Counter = ({ value, duration = 800, decimals = 0, prefix = '', suffix = '' }) => {
  const [display, setDisplay] = React.useState(0);
  const startRef = React.useRef(null);
  const fromRef = React.useRef(0);
  React.useEffect(() => {
    fromRef.current = display;
    startRef.current = null;
    let raf;
    const step = (ts) => {
      if (!startRef.current) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(fromRef.current + (value - fromRef.current) * eased);
      if (t < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return <span>{prefix}{display.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}</span>;
};
