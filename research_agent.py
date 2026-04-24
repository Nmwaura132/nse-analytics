"""
Deep stock research using browser-use + DeepSeek.
Called by the /research Pro command in nse_bot.py.

Requires env vars:
  DEEPSEEK_API_KEY — DeepSeek API key (openai-compatible endpoint)

Install deps: poetry add browser-use langchain-openai
"""

from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL    = "deepseek-chat"

RESEARCH_TASK = """
Research the NSE Kenya stock {ticker} ({company_name}).

Find and summarise:
1. Latest news and announcements (last 30 days)
2. Recent financial results or guidance
3. Analyst or market commentary
4. Any regulatory or corporate actions
5. Key risk factors or tailwinds

Format your response as 5 concise bullet points. Each bullet must be specific
(include numbers, dates, or names where available). End with one sentence
verdict: BUY / HOLD / SELL with a one-line reason.

Focus only on publicly available information. Do not speculate.
"""


async def deep_research(ticker: str, company_name: str = "") -> str:
    """
    Run browser-use agent to research an NSE stock.

    Returns a Markdown string with the research report.
    Raises RuntimeError if browser-use or DeepSeek are unavailable.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")

    try:
        from browser_use import Agent
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            f"browser-use / langchain-openai not installed: {exc}\n"
            "Run: poetry add browser-use langchain-openai"
        ) from exc

    llm = ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.3,
    )

    task = RESEARCH_TASK.format(
        ticker=ticker.upper(),
        company_name=company_name or ticker.upper(),
    )

    agent = Agent(task=task, llm=llm)

    try:
        result = await agent.run(max_steps=15)
        report = result.final_result() if hasattr(result, "final_result") else str(result)
    except Exception as exc:
        logger.error("deep_research failed for %s: %s", ticker, exc)
        raise RuntimeError(f"Research agent error: {exc}") from exc

    return report or "No report generated."


async def _demo(ticker: str) -> None:
    report = await deep_research(ticker)
    print(report)


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "SCOM"
    asyncio.run(_demo(t))
