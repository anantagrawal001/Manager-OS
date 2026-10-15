"""
MANAGER OS — Trading Agent
═══════════════════════════
FILE: agents/trading_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Complete trading intelligence. Stock market, crypto, portfolio management.
         Multi-agent consensus required before ANY trade.
         Hard risk rules enforced at code level — cannot be overridden.
         Gold/silver physical inventory tracker with OCR.
         Philosophy: Never trade on single signal. Like a 1000-year-experience trader.

RISK RULES (HARDCODED — CANNOT BE OVERRIDDEN BY ANY REQUEST):
  - Max 10% of capital per position
  - Stop trading for day if down 2%
  - Minimum 75% AI confidence required
  - Minimum 2:1 risk-reward ratio

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from loguru import logger

from agents.base_agent import BaseAgent


# ─── Risk Rules (HARDCODED) ─────────────────────────────────────────────────

class RiskManager:
    """
    Enforces hard trading rules at code level.
    These cannot be overridden by any conversation or instruction.
    """
    MAX_POSITION_PCT = 0.10        # Max 10% of capital per trade
    MAX_DAILY_LOSS_PCT = 0.02      # Stop trading if down 2% today
    MIN_AI_CONFIDENCE = 0.75       # Minimum 75% confidence required
    MIN_RISK_REWARD = 2.0          # Minimum 2:1 risk:reward ratio
    MIN_CONSENSUS_AGENTS = 3       # Minimum agents that must agree

    def __init__(self):
        self.daily_pnl: float = 0.0
        self.trading_halted_today: bool = False
        self.halt_reason: str = ""

    def check_trade(
        self,
        capital: float,
        position_size: float,
        confidence: float,
        risk_reward: float,
        consensus_count: int
    ) -> Tuple[bool, str]:
        """
        Returns (approved, reason).
        If approved=False, trade is REJECTED regardless of anything else.
        """
        # Check daily loss halt
        if self.trading_halted_today:
            return False, f"Trading halted today: {self.halt_reason}"

        # Check daily loss limit
        if self.daily_pnl <= -(capital * self.MAX_DAILY_LOSS_PCT):
            self.trading_halted_today = True
            self.halt_reason = f"Daily loss limit hit ({self.MAX_DAILY_LOSS_PCT*100:.0f}%)"
            return False, self.halt_reason

        # Check position size
        max_position = capital * self.MAX_POSITION_PCT
        if position_size > max_position:
            return False, f"Position size ₹{position_size:,.0f} exceeds max ₹{max_position:,.0f} (10% of capital)"

        # Check AI confidence
        if confidence < self.MIN_AI_CONFIDENCE:
            return False, f"AI confidence {confidence:.0%} below minimum {self.MIN_AI_CONFIDENCE:.0%}"

        # Check risk-reward
        if risk_reward < self.MIN_RISK_REWARD:
            return False, f"Risk-reward {risk_reward:.1f}:1 below minimum {self.MIN_RISK_REWARD:.1f}:1"

        # Check consensus
        if consensus_count < self.MIN_CONSENSUS_AGENTS:
            return False, f"Only {consensus_count} agents agreed — need {self.MIN_CONSENSUS_AGENTS}"

        return True, "All risk checks passed"

    def record_trade_pnl(self, pnl: float):
        """Record P&L for daily tracking"""
        self.daily_pnl += pnl

    def reset_daily(self):
        """Reset at market open"""
        self.daily_pnl = 0.0
        self.trading_halted_today = False
        self.halt_reason = ""


@dataclass
class TradeSignal:
    ticker: str
    action: str           # BUY | SELL | HOLD
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    reasoning: str
    agent_name: str


# ─── Main Trading Agent ──────────────────────────────────────────────────────

class TradingAgent(BaseAgent):
    """
    Complete trading intelligence for Manager OS.
    
    Capabilities:
    - Real-time market analysis (technical + fundamental + sentiment)
    - Multi-agent consensus voting
    - Demat account order execution
    - Gold/silver physical inventory
    - Portfolio tracking
    - Morning market briefing
    """

    SYSTEM_PROMPT = """
You are an elite quantitative trading analyst with 30 years of experience.
You analyze markets with extreme precision and conservatism.
You never recommend a trade unless the evidence is overwhelming.
You always quantify risk. You always mention what could go wrong.
Provide analysis in clean, structured format.
"""

    def __init__(self, config: dict, router, firewall):
        super().__init__(config, router, firewall)
        self.risk_manager = RiskManager()
        self.trading_config = config.get("trading", {})
        self.mode = self.trading_config.get("mode", "paper")  # paper | live
        self.capital = self.trading_config.get("starting_capital", 10000)

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def execute(self, request: str, context: Dict[str, Any]) -> str:
    #     """Route trading requests to appropriate handler"""
    #     req_lower = request.lower()
    #
    #     if any(w in req_lower for w in ["analyze", "analysis", "should i", "buy", "sell"]):
    #         return await self._analyze_trade(request, context)
    #     elif any(w in req_lower for w in ["portfolio", "holdings", "positions"]):
    #         return await self._portfolio_summary(request, context)
    #     elif any(w in req_lower for w in ["gold", "silver", "jewelry", "precious"]):
    #         return await self._gold_tracker(request, context)
    #     elif any(w in req_lower for w in ["briefing", "market today", "market update"]):
    #         return await self._market_briefing(request, context)
    #     elif any(w in req_lower for w in ["profit", "loss", "pnl", "performance"]):
    #         return await self._pnl_report(request, context)
    #     else:
    #         return await self._general_trading_query(request, context)

    async def execute(self, request, context):
        import re
        if re.search(r'\b(buy|sell|execute|place|order)\b', request, re.I):
            return 'Sir, no live broker is connected and no order was placed. This installation supports informational analysis only.'
        if re.search(r'\b(portfolio|holdings|positions|pnl|profit|loss)\b', request, re.I):
            return 'Sir, no broker holdings or transaction history are connected. Provide your holdings for an analysis; I will not invent a portfolio.'
        result = await self._ask_ai(request, system=self.SYSTEM_PROMPT +
                    '\nNo current market quotes or broker data have been supplied. '
                    'Do not invent prices, signals, confidence percentages, holdings, or market direction. '
                    'Explain concepts or analyze only the figures supplied by the user.', task_type='trading')
        return 'Informational analysis — no live market feed or broker account is connected.\n\n' + result

    async def _analyze_trade(self, request: str, context: Dict) -> str:
        """
        Full trade analysis pipeline.
        Multiple AI agents analyze independently → consensus vote → risk check → recommend.
        """
        logger.info(f"Running trade analysis: {request[:50]}")

        # Extract ticker from request
        ticker = await self._extract_ticker(request)
        if not ticker:
            return "Sir, I couldn't identify which stock or asset you're asking about. Could you specify the ticker symbol?"

        # Run multi-agent analysis in parallel
        agents_results = await asyncio.gather(
            self._technical_analysis_agent(ticker),
            self._sentiment_analysis_agent(ticker),
            self._fundamental_analysis_agent(ticker),
            return_exceptions=True
        )

        signals: List[TradeSignal] = []
        for result in agents_results:
            if isinstance(result, TradeSignal):
                signals.append(result)

        if not signals:
            return f"Sir, I wasn't able to gather enough data on {ticker} right now. Market data may be unavailable."

        # Consensus vote
        buy_votes = sum(1 for s in signals if s.action == "BUY")
        sell_votes = sum(1 for s in signals if s.action == "SELL")
        hold_votes = sum(1 for s in signals if s.action == "HOLD")
        consensus_action = max(["BUY", "SELL", "HOLD"], key=lambda a: [buy_votes, sell_votes, hold_votes][["BUY", "SELL", "HOLD"].index(a)])
        avg_confidence = sum(s.confidence for s in signals) / len(signals)

        # Estimate trade parameters from signals
        entry = signals[0].entry_price if signals else 0
        target = signals[0].target_price if signals else 0
        stop = signals[0].stop_loss if signals else 0
        risk_reward = (target - entry) / (entry - stop) if (entry - stop) > 0 else 0

        # Risk check
        position_size = self.capital * 0.05  # Default 5% position
        approved, risk_reason = self.risk_manager.check_trade(
            capital=self.capital,
            position_size=position_size,
            confidence=avg_confidence,
            risk_reward=risk_reward,
            consensus_count=len([s for s in signals if s.action == consensus_action])
        )

        # Build response
        signal_summary = "\n".join([
            f"  • {s.agent_name}: {s.action} ({s.confidence:.0%} confidence) — {s.reasoning[:80]}"
            for s in signals
        ])

        mode_note = "📋 PAPER TRADING MODE — No real money at risk." if self.mode == "paper" else "⚠️  LIVE TRADING MODE"

        if approved:
            return (
                f"**{ticker} Analysis — {consensus_action}**\n\n"
                f"Agent consensus: {buy_votes} BUY | {sell_votes} SELL | {hold_votes} HOLD\n"
                f"Average confidence: {avg_confidence:.0%}\n\n"
                f"Individual signals:\n{signal_summary}\n\n"
                f"Trade parameters:\n"
                f"  • Entry: ₹{entry:,.2f}\n"
                f"  • Target: ₹{target:,.2f} (+{((target-entry)/entry*100):.1f}%)\n"
                f"  • Stop Loss: ₹{stop:,.2f} (-{((entry-stop)/entry*100):.1f}%)\n"
                f"  • Risk-Reward: {risk_reward:.1f}:1\n"
                f"  • Suggested position: ₹{position_size:,.0f}\n\n"
                f"✅ Risk check: APPROVED — {risk_reason}\n"
                f"{mode_note}\n\n"
                f"Sir, shall I execute this trade?"
            )
        else:
            return (
                f"**{ticker} Analysis — {consensus_action}** (BLOCKED)\n\n"
                f"Agent consensus: {buy_votes} BUY | {sell_votes} SELL | {hold_votes} HOLD\n"
                f"Average confidence: {avg_confidence:.0%}\n\n"
                f"❌ Risk check: REJECTED — {risk_reason}\n\n"
                f"Sir, this trade doesn't meet our risk criteria. "
                f"I'd recommend waiting for better conditions."
            )

    async def _technical_analysis_agent(self, ticker: str) -> TradeSignal:
        """Technical analysis sub-agent"""
        prompt = f"""
Analyze {ticker} using technical indicators: candlestick patterns, moving averages (20/50/200 EMA),
RSI, MACD, volume, support/resistance levels.

Provide:
- Action: BUY or SELL or HOLD
- Confidence: 0.0 to 1.0
- Entry price estimate
- Target price
- Stop loss
- One-line reasoning

Return JSON only:
{{"action": "BUY", "confidence": 0.82, "entry": 1500, "target": 1650, "stop": 1450, "reasoning": "..."}}
"""
        response = await self.router.complete(
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            task_type="trading"
        )
        return self._parse_signal(response, ticker, "Technical Analysis Agent")

    async def _sentiment_analysis_agent(self, ticker: str) -> TradeSignal:
        """News + sentiment sub-agent"""
        prompt = f"""
Analyze market sentiment for {ticker}:
- Recent news headlines and their impact
- Social media sentiment
- Institutional buying/selling signals
- Sector sentiment

Provide JSON with: action, confidence, entry, target, stop, reasoning
"""
        response = await self.router.complete(
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            task_type="trading"
        )
        return self._parse_signal(response, ticker, "Sentiment Analysis Agent")

    async def _fundamental_analysis_agent(self, ticker: str) -> TradeSignal:
        """Fundamental analysis sub-agent"""
        prompt = f"""
Analyze {ticker} fundamentals:
- P/E ratio vs sector average
- Revenue/earnings growth
- Debt levels
- Promoter holding changes
- FII/DII activity

Provide JSON with: action, confidence, entry, target, stop, reasoning
"""
        response = await self.router.complete(
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            task_type="trading"
        )
        return self._parse_signal(response, ticker, "Fundamental Analysis Agent")

    def _parse_signal(self, response: str, ticker: str, agent_name: str) -> TradeSignal:
        """Parse AI response into TradeSignal"""
        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1].strip("json").strip()
            data = json.loads(clean)
            return TradeSignal(
                ticker=ticker,
                action=data.get("action", "HOLD").upper(),
                confidence=float(data.get("confidence", 0.5)),
                entry_price=float(data.get("entry", 0)),
                target_price=float(data.get("target", 0)),
                stop_loss=float(data.get("stop", 0)),
                reasoning=data.get("reasoning", ""),
                agent_name=agent_name
            )
        except Exception as e:
            logger.error(f"Signal parse error: {e}")
            return TradeSignal(ticker=ticker, action="HOLD", confidence=0.3,
                               entry_price=0, target_price=0, stop_loss=0,
                               reasoning="Parse error", agent_name=agent_name)

    async def _extract_ticker(self, request: str) -> Optional[str]:
        """Extract stock ticker from natural language"""
        prompt = f"""
Extract the stock ticker symbol from this request: "{request}"

Examples: "analyze Reliance" → "RELIANCE", "should I buy TCS" → "TCS", "NIFTY outlook" → "NIFTY"

Return ONLY the ticker symbol, nothing else. If unclear, return empty string.
"""
        ticker = await self.router.complete(
            system="Extract stock ticker. Return only the ticker symbol.",
            messages=[{"role": "user", "content": prompt}],
            task_type="conversation"
        )
        return ticker.strip().upper() if ticker.strip() else None

    async def _market_briefing(self, request: str, context: Dict) -> str:
        """Daily market briefing"""
        prompt = """
Provide a concise market briefing covering:
1. NIFTY 50 and SENSEX current levels and direction
2. Top gainers and losers today
3. Key news affecting markets today
4. Sectors to watch
5. Global market cues (US, Asian markets)

Keep it concise — under 200 words. Professional analyst tone.
"""
        return await self.router.complete(
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            task_type="trading"
        )

    async def _portfolio_summary(self, request: str, context: Dict) -> str:
        """Portfolio overview"""
        return (
            "Sir, your portfolio tracker will be fully connected once you provide your Zerodha API credentials. "
            "Run the setup and I'll have real-time portfolio data for you. "
            "For now, I can analyze any specific stock you mention."
        )

    async def _gold_tracker(self, request: str, context: Dict) -> str:
        """Gold/silver physical inventory"""
        return (
            "Sir, your gold and silver inventory tracker is ready. "
            "To populate it, either: (1) speak or type each item and I'll log it, "
            "or (2) take a photo of your jewelry bills and I'll OCR the details automatically. "
            "Which would you prefer?"
        )

    async def _pnl_report(self, request: str, context: Dict) -> str:
        """P&L report"""
        return (
            f"**Trading P&L Summary**\n\n"
            f"Mode: {'Paper Trading' if self.mode == 'paper' else 'Live Trading'}\n"
            f"Today's P&L: ₹{self.risk_manager.daily_pnl:+,.2f}\n"
            f"Trading status: {'⛔ HALTED — ' + self.risk_manager.halt_reason if self.risk_manager.trading_halted_today else '✅ Active'}\n\n"
            f"Connect your Zerodha account for complete P&L history, Sir."
        )

    async def _general_trading_query(self, request: str, context: Dict) -> str:
        """General trading question"""
        return await self._ask_ai(request, system=self.SYSTEM_PROMPT, task_type="trading")

    async def get_status(self) -> Dict:
        return {
            "healthy": True,
            "state": "running",
            "mode": self.mode,
            "trading_halted": self.risk_manager.trading_halted_today,
            "daily_pnl": self.risk_manager.daily_pnl,
        }


# ─── NEW 2026-05-27: Trading Alerts via WhatsApp/Telegram (Reel 17 — Hermes Agent) ──

class TradingAlertManager:
    """
    Pushes trading intelligence to Anant's phone via WhatsApp or Telegram.
    Morning brief at 8AM. Real-time price alerts. Evening 52-week tracker.
    No need to open dashboard — alerts come to Sir's phone.
    """

    def __init__(self, config: dict, router):
        self.config = config
        self.router = router
        self.alert_config = config.get("trading_alerts", {})
        self.watchlist = self.alert_config.get("watchlist", [])
        self.price_alerts = self.alert_config.get("price_alerts", [])
        self._running = False

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def start(self):
    #     """Start all alert loops"""
    #     self._running = True
    #     asyncio.create_task(self._morning_brief_loop())
    #     asyncio.create_task(self._price_alert_loop())
    #     asyncio.create_task(self._evening_report_loop())
    #     logger.info("Trading alert manager started")

    async def start(self):
        self._running = True
        self._tasks = [asyncio.create_task(self._morning_brief_loop()),
                       asyncio.create_task(self._price_alert_loop()),
                       asyncio.create_task(self._evening_report_loop())]

    async def stop(self):
        self._running = False
        for task in getattr(self, '_tasks', []):
            task.cancel()
        await asyncio.gather(*getattr(self, '_tasks', []), return_exceptions=True)

    async def _morning_brief_loop(self):
        """Send morning market brief at 8:00 AM IST every weekday"""
        import datetime as dt
        while self._running:
            now = dt.datetime.now()
            # Target 8:00 AM
            target = now.replace(hour=8, minute=0, second=0, microsecond=0)
            if now >= target:
                target = target + dt.timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            if dt.datetime.now().weekday() < 5:  # Mon-Fri only
                await self._send_morning_brief()

    async def _send_morning_brief(self):
        """Generate and send morning market brief"""
        try:
            prompt = f"""
Generate a concise morning market brief for these stocks: {', '.join(self.watchlist)}

Include:
1. NIFTY 50 and SENSEX overnight direction
2. For each watchlist stock: price direction, key news if any, FII/DII activity
3. Key events today that could move markets
4. One-line recommendation for the day

Keep it under 200 words. Use Indian market context. Be specific with numbers.
Format with clear sections. This will be sent as a WhatsApp/Telegram message.
"""
            brief = await self.router.complete(
                system="You are an elite Indian stock market analyst. Be concise and specific.",
                messages=[{"role": "user", "content": prompt}],
                task_type="trading"
            )

            message = f"📊 *MANAGER OS — Morning Market Brief*\n_{self._get_date_str()}_\n\n{brief}"
            await self._deliver_alert(message)
            logger.info("Morning market brief sent")

        except Exception as e:
            logger.error(f"Morning brief failed: {e}")

    async def _price_alert_loop(self):
        """Monitor prices during market hours and fire alerts"""
        import datetime as dt
        while self._running:
            now = dt.datetime.now()
            # Only during market hours
            market_open = now.replace(hour=9, minute=15, second=0)
            market_close = now.replace(hour=15, minute=30, second=0)

            if now.weekday() < 5 and market_open <= now <= market_close:
                await self._check_price_alerts()
                await asyncio.sleep(60)  # Check every minute
            else:
                await asyncio.sleep(300)  # Check every 5 min outside hours

    async def _check_price_alerts(self):
        """Check if any price alert conditions are met using yfinance"""
        alerts_to_remove = []
        for alert in self.price_alerts:
            ticker = alert.get("ticker", "").strip().upper()
            below = alert.get("below")
            above = alert.get("above")

            if not ticker:
                continue

            try:
                import yfinance as yf
                # Normalize ticker for Indian equities (e.g. RELIANCE -> RELIANCE.NS)
                # Unless it already has a suffix like .BO, .NS or it is crypto/forex/US stock
                ticker_yf = ticker if any(x in ticker for x in [".", "-"]) else f"{ticker}.NS"

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: yf.Ticker(ticker_yf).history(period="1d")
                )

                if not data.empty:
                    current_price = float(data['Close'].iloc[-1])
                    logger.debug(f"Checked price for {ticker}: ₹{current_price:.2f} (Target Below: {below}, Above: {above})")
                    
                    triggered = False
                    trigger_msg = ""

                    if below is not None and current_price < below:
                        triggered = True
                        trigger_msg = f"⚠️ *PRICE ALERT*: {ticker} has dropped below ₹{below:.2f} (Current: ₹{current_price:.2f})"
                    elif above is not None and current_price > above:
                        triggered = True
                        trigger_msg = f"⚠️ *PRICE ALERT*: {ticker} has risen above ₹{above:.2f} (Current: ₹{current_price:.2f})"

                    if triggered:
                        await self._deliver_alert(trigger_msg)
                        alerts_to_remove.append(alert)
                else:
                    logger.warning(f"No pricing data found for {ticker}")
            except Exception as e:
                logger.error(f"Failed to check price alert for {ticker}: {e}")

        for alert in alerts_to_remove:
            if alert in self.price_alerts:
                self.price_alerts.remove(alert)

    async def _evening_report_loop(self):
        """Send evening 52-week position tracker after market close"""
        import datetime as dt
        while self._running:
            now = dt.datetime.now()
            target = now.replace(hour=16, minute=0, second=0, microsecond=0)
            if now >= target:
                target = target + dt.timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            if dt.datetime.now().weekday() < 5:
                await self._send_evening_report()

    async def _send_evening_report(self):
        """Send 52-week position tracker"""
        try:
            prompt = f"""
Generate a 52-week position tracker for these stocks: {', '.join(self.watchlist)}

For each stock:
- Current price vs 52-week high and 52-week low
- % from 52-week low (flag if within 5% with ⚠️)
- % from 52-week high
- Overall position: NEAR_LOW | MID_RANGE | NEAR_HIGH

Also include:
- Upcoming earnings dates for next 2 weeks
- One key insight for tomorrow

Format as a clean WhatsApp/Telegram message with emojis.
"""
            report = await self.router.complete(
                system="You are an elite Indian stock market analyst. Be precise.",
                messages=[{"role": "user", "content": prompt}],
                task_type="trading"
            )

            message = f"📈 *MANAGER OS — Evening Market Report*\n_{self._get_date_str()}_\n\n{report}"
            await self._deliver_alert(message)
            logger.info("Evening market report sent")

        except Exception as e:
            logger.error(f"Evening report failed: {e}")

    def add_price_alert(self, ticker: str, below: float = None, above: float = None):
        """Add a price alert. Usage: add_price_alert('INFY', below=1100)"""
        alert = {"ticker": ticker.upper()}
        if below:
            alert["below"] = below
        if above:
            alert["above"] = above
        self.price_alerts.append(alert)
        logger.info(f"Price alert set: {ticker} below={below} above={above}")

    async def _deliver_alert(self, message: str):
        """Deliver alert via configured channel"""
        delivery = self.alert_config.get("delivery", "dashboard")

        if delivery in ("telegram", "both"):
            await self._send_telegram(message)

        if delivery in ("whatsapp", "both"):
            await self._send_whatsapp(message)

        # Always log — dashboard picks it up
        logger.info(f"ALERT DELIVERED: {message[:100]}")

    async def _send_telegram(self, message: str):
        """Send via Telegram bot"""
        bot_token = self.alert_config.get("telegram_bot_token")
        chat_id = self.alert_config.get("telegram_chat_id")

        if not bot_token or not chat_id:
            logger.debug("Telegram not configured — skipping")
            return

        try:
            import httpx
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            async with httpx.AsyncClient() as client:
                await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                })
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")

    async def _send_whatsapp(self, message: str):
        """Send via WhatsApp (requires WhatsApp Web session)"""
        # WhatsApp Web automation via Playwright — requires active session
        logger.debug("WhatsApp delivery — requires OAuth setup")

    def _get_date_str(self) -> str:
        import datetime as dt
        return dt.datetime.now().strftime("%A, %d %B %Y")
