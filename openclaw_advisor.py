"""
OpenClaw AI Advisor for NSE Pro.

Integrates with the OpenClaw local gateway to provide AI-generated market
commentary, stock Q&A, and daily market narrative.

Integration model:
  OpenClaw runs as a local gateway (default: http://localhost:18789).
  We call its /v1/chat/completions endpoint (OpenAI-compatible) with a
  structured JSON prompt containing computed financial metrics.
  The AI returns structured JSON with commentary, signal, and confidence.

Environment variables (see .env.example):
  OPENCLAW_API_URL   — gateway base URL (default: http://localhost:18789)
  OPENCLAW_API_KEY   — API key if required (leave empty for trust-local mode)
  OPENCLAW_MODEL     — model to use (default: depends on configured provider)

Failure behaviour:
  All methods return None / empty string on failure. The bot gracefully omits
  AI commentary rather than crashing if OpenClaw is unavailable.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_GATEWAY_URL = "http://localhost:18789"


class OpenClawAdvisor:
    """
    Wraps the OpenClaw gateway to generate AI commentary for NSE stocks.
    """

    SYSTEM_STOCK = (
        "You are a professional NSE (Nairobi Securities Exchange) financial analyst. "
        "Given quantitative stock metrics, produce a concise, actionable 2-3 sentence "
        "investment commentary appropriate for retail investors on the Kenyan market. "
        "Always acknowledge data limitations (single-day metrics, simulated history). "
        "Always append: 'This is not financial advice — consult a licensed broker.' "
        "Respond ONLY with valid JSON: "
        '{{"commentary": "...", "signal": "BUY|HOLD|SELL", "confidence": <0-100>}}'
    )

    SYSTEM_MARKET = (
        "You are a Nairobi Securities Exchange (NSE) market analyst writing a daily "
        "market briefing. Given aggregate market statistics, write 2-3 punchy sentences "
        "summarising the day's market mood and key observations. Be factual and concise. "
        "Do not include disclaimers in this summary. "
        "Respond ONLY with valid JSON: "
        '{{"summary": "..."}}'
    )

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 20,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("OPENCLAW_API_URL", DEFAULT_GATEWAY_URL)
        ).rstrip("/")
        self.api_key = api_key or os.getenv("OPENCLAW_API_KEY", "")
        self.model = model or os.getenv("OPENCLAW_MODEL", "")
        self.timeout = timeout

        self._session = requests.Session()
        if self.api_key:
            self._session.headers["Authorization"] = f"Bearer {self.api_key}"
        self._session.headers["Content-Type"] = "application/json"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _chat(self, system: str, user_content: str) -> Optional[dict]:
        """
        Send a chat completion request to the OpenClaw gateway.

        Returns the parsed JSON body from the AI, or None on any error.
        The gateway is expected to be OpenAI-compatible (/v1/chat/completions).
        """
        payload: dict = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user_content},
            ],
        }
        if self.model:
            payload["model"] = self.model

        try:
            resp = self._session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            body = resp.json()

            # Extract content from the first choice
            content = (
                body.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )
            if not content:
                logger.warning("OpenClaw returned empty content")
                return None

            # Strip markdown fences if the model wraps JSON in ```json ... ```
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.lower().startswith("json"):
                    content = content[4:]

            return json.loads(content.strip())

        except requests.exceptions.ConnectionError:
            logger.warning(
                "OpenClaw gateway not reachable at %s — AI commentary disabled",
                self.base_url,
            )
        except requests.exceptions.Timeout:
            logger.warning("OpenClaw request timed out")
        except json.JSONDecodeError as exc:
            logger.warning("OpenClaw returned non-JSON response: %s", exc)
        except Exception as exc:
            logger.warning("OpenClaw request failed: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_stock_commentary(
        self,
        ticker: str,
        metrics: dict,
    ) -> Optional[dict]:
        """
        Generate AI commentary for a single stock.

        Args:
            ticker:  Stock ticker symbol (e.g. "SCOM").
            metrics: Dict with keys like price, change_pct, rsi, sharpe_ratio,
                     trend, signal, risk_score, kelly_fraction, is_real_data.

        Returns:
            {"commentary": str, "signal": str, "confidence": int} or None.
        """
        user_msg = json.dumps({"ticker": ticker, **metrics}, default=str)
        result = self._chat(self.SYSTEM_STOCK, user_msg)

        if result and "commentary" not in result:
            logger.warning("OpenClaw stock commentary missing 'commentary' key")
            return None
        return result

    def get_market_summary(self, market_stats: dict) -> Optional[str]:
        """
        Generate a 2-3 sentence daily market narrative.

        Args:
            market_stats: Dict with total, gainers, losers, unchanged, top_gainer,
                          top_loser, most_active, avg_change_pct.

        Returns:
            Plain-text summary string, or None.
        """
        user_msg = json.dumps(market_stats, default=str)
        result = self._chat(self.SYSTEM_MARKET, user_msg)
        if result:
            return result.get("summary")
        return None

    def answer_stock_question(
        self,
        ticker: str,
        question: str,
        metrics: dict,
    ) -> Optional[str]:
        """
        Answer a freeform user question about a stock, grounded in its metrics.

        Args:
            ticker:   Stock ticker.
            question: User's question (e.g. "Is this a good entry point?").
            metrics:  Current quantitative metrics for context.

        Returns:
            Plain-text answer string (≤4 sentences), or None.
        """
        system = (
            "You are an NSE financial analyst answering retail investor questions. "
            "Ground your answer in the provided quantitative metrics. "
            "Be direct and concise (≤4 sentences). "
            "Always end with: 'This is not financial advice.' "
            "Respond ONLY with valid JSON: "
            '{{"answer": "..."}}'
        )
        user_msg = json.dumps(
            {"ticker": ticker, "question": question, "metrics": metrics},
            default=str,
        )
        result = self._chat(system, user_msg)
        if result:
            return result.get("answer")
        return None

    def is_available(self) -> bool:
        """Quick health-check ping to the gateway."""
        try:
            resp = self._session.get(
                f"{self.base_url}/health",
                timeout=5,
            )
            return resp.status_code < 500
        except Exception:
            return False
