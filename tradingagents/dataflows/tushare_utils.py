#!/usr/bin/env python3
"""
Tushare数据源工具类
提供A股市场数据获取功能，包括实时行情、历史数据、财务数据等
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Union
import warnings
import time

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger

# 导入缓存管理器
try:
    from .cache_manager import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("⚠️ 缓存管理器不可用")

# 导入Tushare
try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    ts = None  # 确保ts变量被定义，即使导入失败
    TUSHARE_AVAILABLE = False
    logger.error("❌ Tushare库未安装，请运行: pip install tushare")


class TushareProvider:
    """Tushare数据提供器"""
    
    def __init__(self, token: str | None = None, enable_cache: bool = True):
        """
        初始化Tushare提供器
        
        Args:
            token: Tushare API token
            enable_cache: 是否启用缓存
        """
        self.connected = False
        self.enable_cache = enable_cache and CACHE_AVAILABLE
        self.api = None
        
        # 初始化缓存管理器
        self.cache_manager = None
        if self.enable_cache:
            try:
                from .cache_manager import get_cache

                self.cache_manager = get_cache()
            except Exception as e:
                logger.warning(f"⚠️ 缓存管理器初始化失败: {e}")
                self.enable_cache = False

        # 获取API token
        if not token:
            token = os.getenv('TUSHARE_TOKEN')

        if not token:
            logger.warning("⚠️ 未找到Tushare API token，请设置TUSHARE_TOKEN环境变量")
            return

        # 初始化Tushare API
        if TUSHARE_AVAILABLE and ts is not None:
            try:
                ts.set_token(token)
                self.api = ts.pro_api()
                self.connected = True
                logger.info("✅ Tushare API连接成功")
            except Exception as e:
                logger.error(f"❌ Tushare API连接失败: {e}")
        else:
            logger.error("❌ Tushare库不可用")
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股股票列表
        
        Returns:
            DataFrame: 股票列表数据
        """
        if not self.connected or self.api is None:
            logger.error(f"❌ Tushare未连接或API对象为空")
            return pd.DataFrame()

        try:
            # 尝试从缓存获取
            if self.enable_cache and self.cache_manager is not None:
                cache_key = self.cache_manager.find_cached_stock_data(
                    symbol="tushare_stock_list",
                    max_age_hours=24  # 股票列表缓存24小时
                )

                if cache_key:
                    cached_data = self.cache_manager.load_stock_data(cache_key)
                    if cached_data is not None:
                        # 检查数据类型并验证是否有效
                        if isinstance(cached_data, pd.DataFrame) and not cached_data.empty:
                            logger.info(f"📦 从缓存获取股票列表: {len(cached_data)}条")
                            return cached_data
                        elif isinstance(cached_data, str) and cached_data.strip():
                            logger.info(f"📦 从缓存获取股票列表: 字符串格式，尝试解析为DataFrame")
                            try:
                                # 尝试将字符串解析为DataFrame
                                # 假设字符串是JSON格式或CSV格式
                                import json
                                if cached_data.strip().startswith('[') or cached_data.strip().startswith('{'):
                                    # JSON格式
                                    data_dict = json.loads(cached_data)
                                    df = pd.DataFrame(data_dict)
                                    if not df.empty:
                                        logger.info(f"✅ 成功解析缓存字符串为DataFrame: {len(df)}条")
                                        return df
                                else:
                                    # 可能是其他格式，记录警告并重新获取
                                    logger.warning(f"⚠️ 缓存数据格式不支持，将重新获取: {type(cached_data)}")
                            except Exception as e:
                                logger.warning(f"⚠️ 解析缓存字符串失败: {e}，将重新获取数据")

            logger.info(f"🔄 从Tushare获取A股股票列表...")

            # 获取股票基本信息
            stock_list = self.api.stock_basic(
                exchange='',
                list_status='L',  # 上市状态
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            if stock_list is not None and not stock_list.empty:
                logger.info(f"✅ 获取股票列表成功: {len(stock_list)}条")
                
                # 缓存数据
                if self.enable_cache and self.cache_manager:
                    try:
                        cache_key = self.cache_manager.save_stock_data(
                            symbol="tushare_stock_list",
                            data=stock_list,
                            data_source="tushare"
                        )
                        logger.info(f"💾 A股股票列表已缓存: tushare_stock_list (tushare) -> {cache_key}")
                    except Exception as e:
                        logger.error(f"⚠️ 缓存保存失败: {e}")
                
                return stock_list
            else:
                logger.warning(f"⚠️ Tushare返回空数据")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_daily(self, symbol: str, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码（如：000001.SZ）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            
        Returns:
            DataFrame: 日线数据
        """
        # 记录详细的调用信息
        logger.info(f"🔍 [Tushare详细日志] get_stock_daily 开始执行")
        logger.info(f"🔍 [Tushare详细日志] 输入参数: symbol='{symbol}', start_date='{start_date}', end_date='{end_date}'")
        logger.info(f"🔍 [Tushare详细日志] 连接状态: {self.connected}")
        logger.info(f"🔍 [Tushare详细日志] API对象: {type(self.api).__name__ if self.api else 'None'}")

        if not self.connected or self.api is None:
            logger.error(f"❌ [Tushare详细日志] Tushare未连接或API对象为空，无法获取数据")
            return pd.DataFrame()

        try:
            # 标准化股票代码
            logger.info(f"🔍 [股票代码追踪] get_stock_daily 调用 _normalize_symbol，传入参数: '{symbol}'")
            ts_code = self._normalize_symbol(symbol)
            logger.info(f"🔍 [股票代码追踪] _normalize_symbol 返回结果: '{ts_code}'")

            # 设置默认日期
            original_start = start_date
            original_end = end_date

            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
                logger.info(f"🔍 [Tushare详细日志] 结束日期为空，设置为当前日期: {end_date}")
            else:
                end_date = end_date.replace('-', '')
                logger.info(f"🔍 [Tushare详细日志] 结束日期转换: '{original_end}' -> '{end_date}'")

            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
                logger.info(f"🔍 [Tushare详细日志] 开始日期为空，设置为一年前: {start_date}")
            else:
                start_date = start_date.replace('-', '')
                logger.info(f"🔍 [Tushare详细日志] 开始日期转换: '{original_start}' -> '{start_date}'")

            logger.info(f"🔄 从Tushare获取{ts_code}数据 ({start_date} 到 {end_date})...")
            logger.info(f"🔍 [股票代码追踪] 调用 Tushare API daily，传入参数: ts_code='{ts_code}', start_date='{start_date}', end_date='{end_date}'")

            # 记录API调用前的状态
            api_start_time = time.time()
            logger.info(f"🔍 [Tushare详细日志] API调用开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")

            # 获取日线数据
            try:
                data = self.api.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                api_duration = time.time() - api_start_time
                logger.info(f"🔍 [Tushare详细日志] API调用完成，耗时: {api_duration:.3f}秒")

            except Exception as api_error:
                api_duration = time.time() - api_start_time
                logger.error(f"❌ [Tushare详细日志] API调用异常，耗时: {api_duration:.3f}秒")
                logger.error(f"❌ [Tushare详细日志] API异常类型: {type(api_error).__name__}")
                logger.error(f"❌ [Tushare详细日志] API异常信息: {str(api_error)}")
                raise api_error

            # 详细记录返回数据的信息
            logger.info(f"🔍 [股票代码追踪] Tushare API daily 返回数据形状: {data.shape if data is not None and hasattr(data, 'shape') else 'None'}")
            logger.info(f"🔍 [Tushare详细日志] 返回数据类型: {type(data)}")

            if data is not None:
                logger.info(f"🔍 [Tushare详细日志] 数据是否为空: {data.empty}")
                if not data.empty:
                    logger.info(f"🔍 [Tushare详细日志] 数据列名: {list(data.columns)}")
                    logger.info(f"🔍 [Tushare详细日志] 数据索引类型: {type(data.index)}")
                    if 'ts_code' in data.columns:
                        unique_codes = data['ts_code'].unique()
                        logger.info(f"🔍 [股票代码追踪] 返回数据中的ts_code: {unique_codes}")
                    if 'trade_date' in data.columns:
                        date_range = f"{data['trade_date'].min()} 到 {data['trade_date'].max()}"
                        logger.info(f"🔍 [Tushare详细日志] 数据日期范围: {date_range}")
                else:
                    logger.warning(f"⚠️ [Tushare详细日志] 返回的DataFrame为空")
            else:
                logger.warning(f"⚠️ [Tushare详细日志] 返回数据为None")

            if data is not None and not data.empty:
                # 数据预处理
                logger.info(f"🔍 [Tushare详细日志] 开始数据预处理...")
                data = data.sort_values('trade_date')
                data['trade_date'] = pd.to_datetime(data['trade_date'])
                logger.info(f"🔍 [Tushare详细日志] 数据预处理完成")

                logger.info(f"✅ 获取{ts_code}数据成功: {len(data)}条")

                # 缓存数据
                if self.enable_cache and self.cache_manager:
                    try:
                        logger.info(f"🔍 [Tushare详细日志] 开始缓存数据...")
                        cache_key = self.cache_manager.save_stock_data(
                            symbol=symbol,
                            data=data,
                            data_source="tushare"
                        )
                        logger.info(f"💾 A股历史数据已缓存: {symbol} (tushare) -> {cache_key}")
                        logger.info(f"🔍 [Tushare详细日志] 数据缓存完成")
                    except Exception as cache_error:
                        logger.error(f"⚠️ 缓存保存失败: {cache_error}")
                        logger.error(f"⚠️ [Tushare详细日志] 缓存异常类型: {type(cache_error).__name__}")

                logger.info(f"🔍 [Tushare详细日志] get_stock_daily 执行成功，返回数据")
                return data
            else:
                logger.warning(f"⚠️ Tushare返回空数据: {ts_code}")
                logger.warning(f"⚠️ [Tushare详细日志] 空数据详情: data={data}, empty={data.empty if data is not None else 'N/A'}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ 获取{symbol}数据失败: {e}")
            logger.error(f"❌ [Tushare详细日志] 异常类型: {type(e).__name__}")
            logger.error(f"❌ [Tushare详细日志] 异常信息: {str(e)}")
            import traceback
            logger.error(f"❌ [Tushare详细日志] 异常堆栈: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 股票基本信息
        """
        if not self.connected or self.api is None:
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}
        
        try:
            logger.info(f"🔍 [股票代码追踪] get_stock_info 调用 _normalize_symbol，传入参数: '{symbol}'")
            ts_code = self._normalize_symbol(symbol)
            logger.info(f"🔍 [股票代码追踪] _normalize_symbol 返回结果: '{ts_code}'")

            # 获取股票基本信息
            logger.info(f"🔍 [股票代码追踪] 调用 Tushare API stock_basic，传入参数: ts_code='{ts_code}'")
            basic_info = self.api.stock_basic(
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )

            logger.info(f"🔍 [股票代码追踪] Tushare API stock_basic 返回数据形状: {basic_info.shape if basic_info is not None and hasattr(basic_info, 'shape') else 'None'}")
            if basic_info is not None and not basic_info.empty:
                logger.info(f"🔍 [股票代码追踪] 返回数据内容: {basic_info.to_dict('records')}")
            
            if basic_info is not None and not basic_info.empty:
                info = basic_info.iloc[0]
                return {
                    'symbol': symbol,
                    'ts_code': info['ts_code'],
                    'name': info['name'],
                    'area': info.get('area', ''),
                    'industry': info.get('industry', ''),
                    'market': info.get('market', ''),
                    'list_date': info.get('list_date', ''),
                    'source': 'tushare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}
                
        except Exception as e:
            logger.error(f"❌ 获取{symbol}股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}
    
    def get_financial_data(self, symbol: str, period: str = "20231231") -> Dict:
        """
        获取财务数据
        
        Args:
            symbol: 股票代码
            period: 报告期（YYYYMMDD）
            
        Returns:
            Dict: 财务数据
        """
        if not self.connected or self.api is None:
            return {}
        
        try:
            ts_code = self._normalize_symbol(symbol)
            
            financials = {}
            
            # 获取资产负债表
            try:
                balance_sheet = self.api.balancesheet(
                    ts_code=ts_code,
                    period=period,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_assets,total_liab,total_hldr_eqy_exc_min_int'
                )
                financials['balance_sheet'] = balance_sheet.to_dict('records') if balance_sheet is not None and not balance_sheet.empty else []
            except Exception as e:
                logger.error(f"⚠️ 获取资产负债表失败: {e}")
                financials['balance_sheet'] = []
            
            # 获取利润表
            try:
                income_statement = self.api.income(
                    ts_code=ts_code,
                    period=period,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_revenue,total_cogs,operate_profit,total_profit,n_income'
                )
                financials['income_statement'] = income_statement.to_dict('records') if income_statement is not None and not income_statement.empty else []
            except Exception as e:
                logger.error(f"⚠️ 获取利润表失败: {e}")
                financials['income_statement'] = []
            
            # 获取现金流量表
            try:
                cash_flow = self.api.cashflow(
                    ts_code=ts_code,
                    period=period,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,net_profit,finan_exp,c_fr_sale_sg,c_paid_goods_s'
                )
                financials['cash_flow'] = cash_flow.to_dict('records') if cash_flow is not None and not cash_flow.empty else []
            except Exception as e:
                logger.error(f"⚠️ 获取现金流量表失败: {e}")
                financials['cash_flow'] = []
            
            return financials
            
        except Exception as e:
            logger.error(f"❌ 获取{symbol}财务数据失败: {e}")
            return {}
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码为Tushare格式

        Args:
            symbol: 原始股票代码

        Returns:
            str: Tushare格式的股票代码
        """
        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] _normalize_symbol 接收到的原始股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")

        original_symbol = symbol

        # 移除可能的前缀
        symbol = symbol.replace('sh.', '').replace('sz.', '')
        if symbol != original_symbol:
            logger.info(f"🔍 [股票代码追踪] 移除前缀后: '{original_symbol}' -> '{symbol}'")

        # 如果已经是Tushare格式，直接返回
        if '.' in symbol:
            logger.info(f"🔍 [股票代码追踪] 已经是Tushare格式，直接返回: '{symbol}'")
            return symbol

        # 根据代码判断交易所
        if symbol.startswith('6'):
            result = f"{symbol}.SH"  # 上海证券交易所
            logger.info(f"🔍 [股票代码追踪] 上海证券交易所: '{symbol}' -> '{result}'")
            return result
        elif symbol.startswith(('0', '3')):
            result = f"{symbol}.SZ"  # 深圳证券交易所
            logger.info(f"🔍 [股票代码追踪] 深圳证券交易所: '{symbol}' -> '{result}'")
            return result
        elif symbol.startswith('8'):
            result = f"{symbol}.BJ"  # 北京证券交易所
            logger.info(f"🔍 [股票代码追踪] 北京证券交易所: '{symbol}' -> '{result}'")
            return result
        else:
            # 默认深圳
            result = f"{symbol}.SZ"
            logger.info(f"🔍 [股票代码追踪] 默认深圳证券交易所: '{symbol}' -> '{result}'")
            return result
    
    def search_stocks(self, keyword: str) -> pd.DataFrame:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            DataFrame: 搜索结果
        """
        try:
            stock_list = self.get_stock_list()
            
            if stock_list.empty:
                return pd.DataFrame()
            
            # 按名称和代码搜索
            mask = (
                stock_list['name'].str.contains(keyword, na=False) |
                stock_list['symbol'].str.contains(keyword, na=False) |
                stock_list['ts_code'].str.contains(keyword, na=False)
            )
            
            results = stock_list[mask]
            logger.debug(f"🔍 搜索'{keyword}'找到{len(results)}只股票")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 搜索股票失败: {e}")
            return pd.DataFrame()


# 全局提供器实例
_tushare_provider = None

def get_tushare_provider() -> TushareProvider:
    """获取全局Tushare提供器实例"""
    global _tushare_provider
    if _tushare_provider is None:
        _tushare_provider = TushareProvider()
    return _tushare_provider


def get_china_stock_data_tushare(symbol: str, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """
    获取中国股票数据的便捷函数（Tushare数据源）
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame: 股票数据
    """
    provider = get_tushare_provider()
    return provider.get_stock_daily(symbol, start_date, end_date)


def get_china_stock_info_tushare(symbol: str) -> Dict:
    """
    获取中国股票信息的便捷函数（Tushare数据源）
    
    Args:
        symbol: 股票代码
        
    Returns:
        Dict: 股票信息
    """
    provider = get_tushare_provider()
    return provider.get_stock_info(symbol)
