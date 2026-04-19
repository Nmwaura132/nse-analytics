"""
OpenClaw HTTP client — wraps the Claude AI gateway running at OPENCLAW_API_URL.

Usage:
    from openclaw_client import ai_analyze, ai_portfolio_narrative, ai_explain_move

All calls are fire-and-return; they raise on network errors so callers should
wrap in try/except and fall back to rule-based output.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

_BASE = os.getenv("OPENCLAW_API_URL", "http://localhost:18789")
_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
_TIMEOUT = 30  # seconds


def _call(prompt: str, system: str = "") -> str:
    """POST a prompt to the OpenClaw gateway and return the text response."""
    headers = {"Content-Type": "application/json"}
    if _TOKEN:
        headers["Authorization"] = f"Bearer {_TOKEN}"

    payload = {"message": prompt}
    if system:
        payload["system"] = system

    resp = requests.post(
        f"{_BASE}/api/chat",
        json=payload,
        headers=headers,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    # OpenClaw returns {"message": "...", ...} or {"content": "..."}
    return data.get("message") or data.get("content") or str(data)


# ─── public helpers ──────────────────────────────────────────────────────────

SYSTEM_ANALYST = (
    "You are a concise, no-nonsense NSE Kenya stock analyst. "
    "Speak directly to a retail investor. Keep responses under 200 words. "
    "Focus on actionable insight, not disclaimers."
)


def ai_analyze(ticker: str, price: float, change_pct: float,
               rsi: float | None, macd: float | None,
               pe: float | None, div_yield: float | None,
               volume: float | None) -> str:
    """Return a 3-sentence AI narrative for a stock's current state."""
    indicators = []
    if rsi is not None:
        indicators.append(f"RSI={rsi:.1f}")
    if macd is not None:
        indicators.append(f"MACD={macd:.3f}")
    if pe is not None:
        indicators.append(f"P/E={pe:.1f}")
    if div_yield is not None:
        indicators.append(f"Div Yield={div_yield:.1f}%")
    if volume is not None:
        indicators.append(f"Volume={volume:,.0f}")

    prompt = (
        f"NSE Kenya stock: {ticker}\n"
        f"Price: KES {price:.2f}  Change: {change_pct:+.2f}%\n"
        f"Indicators: {', '.join(indicators) if indicators else 'N/A'}\n\n"
        "Give a 3-sentence analysis: (1) what the technicals say, "
        "(2) what the valuation says, (3) what a retail investor should watch."
    )
    return _call(prompt, SYSTEM_ANALYST)


def ai_portfolio_narrative(holdings: list[dict], total_pnl_pct: float,
                           risk_score: float) -> str:
    """Return a paragraph narrative of the user's portfolio."""
    lines = [f"- {h['ticker']}: {h['qty']} shares, P&L {h['pnl_pct']:+.1f}%"
             for h in holdings]
    prompt = (
        f"Portfolio summary:\n" + "\n".join(lines) + "\n\n"
        f"Overall P&L: {total_pnl_pct:+.1f}%  Risk score: {risk_score:.0f}/100\n\n"
        "Write a 3-sentence portfolio narrative covering: "
        "(1) sector concentration, (2) biggest risk, (3) one actionable suggestion."
    )
    return _call(prompt, SYSTEM_ANALYST)


def ai_explain_move(ticker: str, price: float, change_pct: float,
                    volume: float | None) -> str:
    """Explain why a stock might be moving significantly."""
    vol_note = f"  Volume: {volume:,.0f}" if volume else ""
    prompt = (
        f"{ticker} is moving {change_pct:+.1f}% today at KES {price:.2f}.{vol_note}\n\n"
        "In 2 sentences: what usually causes this kind of move on the NSE, "
        "and what should an investor check (announcements, dividends, index events)?"
    )
    return _call(prompt, SYSTEM_ANALYST)


def ai_ask(user_question: str, market_context: str = "") -> str:
    """Answer a freeform question about the NSE market."""
    prompt = user_question
    if market_context:
        prompt = f"Market context:\n{market_context}\n\nQuestion: {user_question}"
    return _call(prompt, SYSTEM_ANALYST)


def is_available() -> bool:
    """Return True if the OpenClaw gateway is reachable."""
    try:
        r = requests.get(f"{_BASE}/healthz", timeout=5)
        return r.ok
    except Exception:
        return False
