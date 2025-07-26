# TradingAgents/graph/propagation.py

from typing import Any
from langchain_core.messages import HumanMessage

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, company_name: str, trade_date: str
    ) -> AgentState:
        """Create the initial state for the agent graph."""
        return {
            "messages": [HumanMessage(content=company_name)],
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            "sender": "",  # 初始状态下没有发送者
            "investment_debate_state": InvestDebateState(
                {
                    "bull_history": "",
                    "bear_history": "",
                    "history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "investment_plan": "",  # 分析师生成的投资计划
            "trader_investment_plan": "",  # 交易员生成的投资计划
            "risk_debate_state": RiskDebateState(
                {
                    "risky_history": "",
                    "safe_history": "",
                    "neutral_history": "",
                    "history": "",
                    "latest_speaker": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "final_trade_decision": "",  # 风险分析师的最终决策
            "market_report": "",
            "fundamentals_report": "",
            "sentiment_report": "",
            "news_report": "",
        }

    def get_graph_args(self) -> dict[str, Any]:
        """Get arguments for the graph invocation."""
        return {
            "stream_mode": "values",
            "config": {"recursion_limit": self.max_recur_limit},
        }
