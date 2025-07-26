"""
基本面分析师 - 统一工具架构版本
使用统一工具自动识别股票类型并调用相应数据源
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

# 导入分析模块日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def _get_company_name_for_fundamentals(ticker: str, market_info: dict) -> str:
    """
    为基本面分析师获取公司名称

    Args:
        ticker: 股票代码
        market_info: 市场信息字典

    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)

            # 解析股票名称
            if "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.debug(f"📊 [基本面分析师] 从统一接口获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                logger.warning(f"⚠️ [基本面分析师] 无法从统一接口解析股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.improved_hk_utils import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"📊 [基本面分析师] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"📊 [基本面分析师] 改进港股工具获取名称失败: {e}")
                # 降级方案：生成友好的默认名称
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"

        elif market_info['is_us']:
            # 美股：使用简单映射或返回代码
            us_stock_names = {
                'AAPL': '苹果公司',
                'TSLA': '特斯拉',
                'NVDA': '英伟达',
                'MSFT': '微软',
                'GOOGL': '谷歌',
                'AMZN': '亚马逊',
                'META': 'Meta',
                'NFLX': '奈飞'
            }

            company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
            logger.debug(f"📊 [基本面分析师] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [基本面分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_fundamentals_analyst(llm, toolkit):
    @log_analyst_module("fundamentals")
    def fundamentals_analyst_node(state):
        logger.debug(f"📊 [DEBUG] ===== 基本面分析师节点开始 =====")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        start_date = '2025-05-28'

        logger.debug(f"📊 [DEBUG] 输入参数: ticker={ticker}, date={current_date}")
        logger.debug(f"📊 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        logger.debug(f"📊 [DEBUG] 现有基本面报告: {state.get('fundamentals_report', 'None')}")

        # 获取股票市场信息
        from tradingagents.utils.stock_utils import StockUtils
        logger.info(f"📊 [基本面分析师] 正在分析股票: {ticker}")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] 基本面分析师接收到的原始股票代码: '{ticker}' (类型: {type(ticker)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(ticker))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(ticker))}")

        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"🔍 [股票代码追踪] StockUtils.get_market_info 返回的市场信息: {market_info}")

        logger.debug(f"📊 [DEBUG] 股票类型检查: {ticker} -> {market_info['market_name']} ({market_info['currency_name']}")
        logger.debug(f"📊 [DEBUG] 详细市场信息: is_china={market_info['is_china']}, is_hk={market_info['is_hk']}, is_us={market_info['is_us']}")
        logger.debug(f"📊 [DEBUG] 工具配置检查: online_tools={toolkit.config['online_tools']}")

        # 获取公司名称
        company_name = _get_company_name_for_fundamentals(ticker, market_info)
        logger.debug(f"📊 [DEBUG] 公司名称: {ticker} -> {company_name}")

        # 选择工具
        if toolkit.config["online_tools"]:
            # 使用统一的基本面分析工具，工具内部会自动识别股票类型
            logger.info(f"📊 [基本面分析师] 使用统一基本面分析工具，自动识别股票类型")
            tools = [toolkit.get_stock_fundamentals_unified]
            # 安全地获取工具名称用于调试
            tool_names_debug = []
            for tool in tools:
                if hasattr(tool, 'name'):
                    tool_names_debug.append(tool.name)
                elif hasattr(tool, '__name__'):
                    tool_names_debug.append(tool.__name__)
                else:
                    tool_names_debug.append(str(tool))
            logger.debug(f"📊 [DEBUG] 选择的工具: {tool_names_debug}")
            logger.debug(f"📊 [DEBUG] 🔧 统一工具将自动处理: {market_info['market_name']}")
        else:
            # 离线模式：优先使用FinnHub数据，SimFin作为补充
            if market_info['is_china']:
                # A股使用本地缓存数据
                tools = [
                    toolkit.get_china_stock_data,
                    toolkit.get_china_fundamentals
                ]
            else:
                # 美股/港股：优先FinnHub，SimFin作为补充
                tools = [
                    toolkit.get_fundamentals_openai,  # 使用现有的OpenAI基本面数据工具
                    toolkit.get_finnhub_company_insider_sentiment,
                    toolkit.get_finnhub_company_insider_transactions,
                    toolkit.get_simfin_balance_sheet,
                    toolkit.get_simfin_cashflow,
                    toolkit.get_simfin_income_stmt,
                ]

        # 统一的系统提示，适用于所有股票类型
        system_message = (
            f"你是一位专业的股票基本面分析师。"
            f"⚠️ 绝对强制要求：你必须调用工具获取真实数据！不允许任何假设或编造！"
            f"任务：分析{company_name}（股票代码：{ticker}，{market_info['market_name']}）"
            f"🔴 立即调用 get_stock_fundamentals_unified 工具"
            f"参数：ticker='{ticker}', start_date='{start_date}', end_date='{current_date}', curr_date='{current_date}'"
            "📊 分析要求："
            "- 基于真实数据进行深度基本面分析"
            f"- 计算并提供合理价位区间（使用{market_info['currency_name']}{market_info['currency_symbol']}）"
            "- 分析当前股价是否被低估或高估"
            "- 提供基于基本面的目标价位建议"
            "- 包含PE、PB、PEG等估值指标分析"
            "- 结合市场特点进行分析"
            "🌍 语言和货币要求："
            "- 所有分析内容必须使用中文"
            "- 投资建议必须使用中文：买入、持有、卖出"
            "- 绝对不允许使用英文：buy、hold、sell"
            f"- 货币单位使用：{market_info['currency_name']}（{market_info['currency_symbol']}）"
            "🚫 严格禁止："
            "- 不允许说'我将调用工具'"
            "- 不允许假设任何数据"
            "- 不允许编造公司信息"
            "- 不允许直接回答而不调用工具"
            "- 不允许回复'无法确定价位'或'需要更多信息'"
            "- 不允许使用英文投资建议（buy/hold/sell）"
            "✅ 你必须："
            "- 立即调用统一基本面分析工具"
            "- 等待工具返回真实数据"
            "- 基于真实数据进行分析"
            "- 提供具体的价位区间和目标价"
            "- 使用中文投资建议（买入/持有/卖出）"
            "现在立即开始调用工具！不要说任何其他话！"
        )

        # 系统提示模板
        system_prompt = (
            "🔴 强制要求：你必须调用工具获取真实数据！"
            "🚫 绝对禁止：不允许假设、编造或直接回答任何问题！"
            "✅ 你必须：立即调用提供的工具获取真实数据，然后基于真实数据进行分析。"
            "可用工具：{tool_names}。\n{system_message}"
            "当前日期：{current_date}。"
            "分析目标：{company_name}（股票代码：{ticker}）。"
            "请确保在分析中正确区分公司名称和股票代码。"
        )

        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(system_message=system_message)
        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(company_name=company_name)

        # 检测阿里百炼模型并创建新实例
        if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
            logger.debug(f"📊 [DEBUG] 检测到阿里百炼模型，创建新实例以避免工具缓存")
            from tradingagents.llm_adapters import ChatDashScopeOpenAI
            fresh_llm = ChatDashScopeOpenAI(
                model=llm.model_name,
                temperature=llm.temperature,
                max_tokens=getattr(llm, 'max_tokens', 2000)
            )
        else:
            fresh_llm = llm

        logger.debug(f"📊 [DEBUG] 创建LLM链，工具数量: {len(tools)}")
        # 安全地获取工具名称用于调试
        debug_tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                debug_tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                debug_tool_names.append(tool.__name__)
            else:
                debug_tool_names.append(str(tool))
        logger.debug(f"📊 [DEBUG] 绑定的工具列表: {debug_tool_names}")
        logger.debug(f"📊 [DEBUG] 创建工具链，让模型自主决定是否调用工具")

        try:
            chain = prompt | fresh_llm.bind_tools(tools)
            logger.debug(f"📊 [DEBUG] ✅ 工具绑定成功，绑定了 {len(tools)} 个工具")
        except Exception as e:
            logger.error(f"📊 [DEBUG] ❌ 工具绑定失败: {e}")
            raise e

        logger.debug(f"📊 [DEBUG] 调用LLM链...")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] LLM调用前，ticker参数: '{ticker}'")
        logger.info(f"🔍 [股票代码追踪] 传递给LLM的消息数量: {len(state['messages'])}")

        # 检查消息内容中是否有其他股票代码
        for i, msg in enumerate(state["messages"]):
            if hasattr(msg, 'content') and msg.content:
                content = str(msg.content)
                if "002021" in content:
                    logger.warning(f"🔍 [股票代码追踪] 警告：消息 {i} 中包含错误股票代码 002021")
                    logger.warning(f"🔍 [股票代码追踪] 消息内容: {content[:200]}...")
                if "002027" in content:
                    logger.info(f"🔍 [股票代码追踪] 消息 {i} 中包含正确股票代码 002027")

        result = chain.invoke(state["messages"])
        logger.debug(f"📊 [DEBUG] LLM调用完成")

        # 检查LLM返回结果中的股票代码
        if hasattr(result, 'content') and result.content:
            content = str(result.content)
            if "002021" in content:
                logger.warning(f"🔍 [股票代码追踪] 警告：LLM返回内容中包含错误股票代码 002021")
                logger.warning(f"🔍 [股票代码追踪] LLM返回内容前500字符: {content[:500]}...")
            if "002027" in content:
                logger.info(f"🔍 [股票代码追踪] LLM返回内容中包含正确股票代码 002027")

        logger.debug(f"📊 [DEBUG] 结果类型: {type(result)}")
        logger.debug(f"📊 [DEBUG] 工具调用数量: {len(getattr(result, 'tool_calls', []))}")
        logger.debug(f"📊 [DEBUG] 内容长度: {len(result.content) if hasattr(result, 'content') else 0}")

        # 检查工具调用 - 安全地获取工具名称
        expected_tools = []
        for tool in tools:
            if hasattr(tool, 'name'):
                expected_tools.append(tool.name)
            elif hasattr(tool, '__name__'):
                expected_tools.append(tool.__name__)
            else:
                expected_tools.append(str(tool))

        actual_tools = [tc['name'] for tc in getattr(result, 'tool_calls', [])]

        logger.debug(f"📊 [DEBUG] 期望的工具: {expected_tools}")
        logger.debug(f"📊 [DEBUG] 实际调用的工具: {actual_tools}")

        # 处理基本面分析报告
        tool_calls = getattr(result, 'tool_calls', [])
        if len(tool_calls) > 0:
            # 有工具调用，记录工具调用信息
            tool_calls_info = []
            for tc in tool_calls:
                tool_calls_info.append(tc['name'])
                logger.debug(f"📊 [DEBUG] 工具调用 {len(tool_calls_info)}: {tc}")

            logger.info(f"📊 [基本面分析师] 工具调用: {tool_calls_info}")

            # 返回状态，让工具执行
            return {"messages": [result]}
        
        else:
            # 没有工具调用，使用阿里百炼强制工具调用修复
            logger.debug(f"📊 [DEBUG] 检测到模型未调用工具，启用强制工具调用模式")
            
            # 强制调用统一基本面分析工具
            try:
                logger.debug(f"📊 [DEBUG] 强制调用 get_stock_fundamentals_unified...")
                # 安全地查找统一基本面分析工具
                unified_tool = None
                for tool in tools:
                    tool_name = None
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__

                    if tool_name == 'get_stock_fundamentals_unified':
                        unified_tool = tool
                        break
                if unified_tool:
                    logger.info(f"🔍 [股票代码追踪] 强制调用统一工具，传入ticker: '{ticker}'")
                    combined_data = unified_tool.invoke({
                        'ticker': ticker,
                        'start_date': start_date,
                        'end_date': current_date,
                        'curr_date': current_date
                    })
                    logger.debug(f"📊 [DEBUG] 统一工具数据获取成功，长度: {len(combined_data)}字符")

                    # 检查工具返回数据中的股票代码
                    if "002021" in combined_data:
                        logger.warning(f"🔍 [股票代码追踪] 警告：统一工具返回数据中包含错误股票代码 002021")
                    if "002027" in combined_data:
                        logger.info(f"🔍 [股票代码追踪] 统一工具返回数据中包含正确股票代码 002027")
                else:
                    combined_data = "统一基本面分析工具不可用"
                    logger.debug(f"📊 [DEBUG] 统一工具未找到")
            except Exception as e:
                combined_data = f"统一基本面分析工具调用失败: {e}"
                logger.debug(f"📊 [DEBUG] 统一工具调用异常: {e}")
            
            currency_info = f"{market_info['currency_name']}（{market_info['currency_symbol']}）"
            
            # 生成基于真实数据的分析报告
            logger.info(f"🔍 [股票代码追踪] 生成分析提示词，使用ticker: '{ticker}', company_name: '{company_name}'")
            analysis_prompt = f"""基于以下真实数据，对{company_name}（股票代码：{ticker}）进行详细的基本面分析：

{combined_data}

请提供：
1. 公司基本信息分析（{company_name}，股票代码：{ticker}）
2. 财务状况评估
3. 盈利能力分析
4. 估值分析（使用{currency_info}）
5. 投资建议（买入/持有/卖出）

要求：
- 基于提供的真实数据进行分析
- 正确使用公司名称"{company_name}"和股票代码"{ticker}"
- 价格使用{currency_info}
- 投资建议使用中文
- 分析要详细且专业"""

            try:
                # 创建简单的分析链
                analysis_prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "你是专业的股票基本面分析师，基于提供的真实数据进行分析。"),
                    ("human", "{analysis_request}")
                ])
                
                analysis_chain = analysis_prompt_template | fresh_llm
                analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
                
                if hasattr(analysis_result, 'content'):
                    report = str(analysis_result.content)
                else:
                    report = str(analysis_result)

                # 检查最终报告中的股票代码并进行修正
                logger.info(f"🔍 [股票代码追踪] 最终报告生成完成，检查股票代码...")

                # 股票代码验证和修正
                def validate_and_fix_stock_code(content: str, correct_code: str) -> str:
                    """验证并修正股票代码"""
                    # 定义常见的错误映射
                    error_mappings = {
                        "002027": ["002021", "002026", "002028"],  # 分众传媒常见错误
                        "002021": ["002027"],  # 反向映射
                        "000001": ["000002", "000003"],  # 平安银行常见错误
                        "600036": ["600037", "600035"],  # 招商银行常见错误
                    }

                    if correct_code in error_mappings:
                        for wrong_code in error_mappings[correct_code]:
                            if wrong_code in content:
                                logger.warning(f"🔍 [股票代码验证] 发现错误代码 {wrong_code}，修正为 {correct_code}")
                                content = content.replace(wrong_code, correct_code)

                    return content

                # 应用股票代码验证和修正
                original_report = report
                report = validate_and_fix_stock_code(report, ticker)

                if report != original_report:
                    logger.info(f"🔍 [股票代码验证] 已修正报告中的错误股票代码")

                if "002021" in report:
                    logger.warning(f"🔍 [股票代码追踪] 警告：最终报告中仍包含错误股票代码 002021")
                    logger.warning(f"🔍 [股票代码追踪] 最终报告前500字符: {report[:500]}...")
                if "002027" in report:
                    logger.info(f"🔍 [股票代码追踪] 最终报告中包含正确股票代码 002027")

                logger.info(f"📊 [基本面分析师] 强制工具调用完成，报告长度: {len(report)}")
                
            except Exception as e:
                logger.error(f"❌ [DEBUG] 强制工具调用分析失败: {e}")
                report = f"基本面分析失败：{str(e)}"
            
            return {"fundamentals_report": report}

    return fundamentals_analyst_node
