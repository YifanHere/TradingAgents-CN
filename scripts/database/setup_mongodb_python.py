#!/usr/bin/env python3
"""
MongoDB 初始化脚本 - Python版本
适用于 MongoDB 8.1.2，无需 mongosh
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_mongodb():
    """设置MongoDB用户和数据库"""
    print("🚀 开始配置 MongoDB 8.1.2...")
    
    try:
        import pymongo
        from pymongo import MongoClient
        
        # 首先尝试无认证连接（新安装的MongoDB默认无认证）
        print("🔍 尝试连接到 MongoDB...")
        client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB连接成功")
        
        # 检查是否已经启用认证
        try:
            # 尝试获取用户列表，如果失败说明认证已启用
            admin_db = client.admin
            users = admin_db.command("usersInfo")
            print("📊 当前认证状态: 未启用认证")
            auth_enabled = False
        except pymongo.errors.OperationFailure as e:
            if "command usersInfo requires authentication" in str(e):
                print("📊 当前认证状态: 已启用认证")
                auth_enabled = True
            else:
                raise e
        
        if not auth_enabled:
            print("👤 创建管理员用户...")
            
            # 创建管理员用户
            admin_db = client.admin
            try:
                admin_db.command("createUser", "admin",
                    pwd="tradingagents123",
                    roles=[
                        {"role": "userAdminAnyDatabase", "db": "admin"},
                        {"role": "readWriteAnyDatabase", "db": "admin"},
                        {"role": "dbAdminAnyDatabase", "db": "admin"},
                        {"role": "clusterAdmin", "db": "admin"}
                    ]
                )
                print("✅ 管理员用户创建成功")
            except pymongo.errors.DuplicateKeyError:
                print("⚠️  管理员用户已存在，跳过创建")
            except pymongo.errors.OperationFailure as e:
                if "already exists" in str(e):
                    print("⚠️  管理员用户已存在，跳过创建")
                else:
                    raise e
            
            # 创建应用数据库和用户
            print("👤 创建应用用户...")
            tradingagents_db = client.tradingagents
            try:
                tradingagents_db.command("createUser", "tradingagents",
                    pwd="tradingagents123",
                    roles=[
                        {"role": "readWrite", "db": "tradingagents"},
                        {"role": "dbAdmin", "db": "tradingagents"}
                    ]
                )
                print("✅ 应用用户创建成功")
            except pymongo.errors.DuplicateKeyError:
                print("⚠️  应用用户已存在，跳过创建")
            except pymongo.errors.OperationFailure as e:
                if "already exists" in str(e):
                    print("⚠️  应用用户已存在，跳过创建")
                else:
                    raise e
        
        else:
            # 认证已启用，使用管理员账户连接
            print("🔐 使用管理员账户连接...")
            client.close()
            client = MongoClient(
                "mongodb://admin:tradingagents123@localhost:27017/?authSource=admin",
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            client.admin.command('ping')
            print("✅ 管理员认证成功")
        
        # 初始化数据库结构
        print("📁 初始化数据库结构...")
        
        # 获取tradingagents数据库
        if auth_enabled:
            db = client.tradingagents
        else:
            db = client.tradingagents
        
        # 创建集合
        collections = [
            "stock_data",
            "analysis_reports", 
            "user_sessions",
            "system_logs",
            "market_data",
            "fundamental_data",
            "news_data",
            "social_data",
            "analysis_results",
            "metadata"
        ]
        
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"  ✅ 创建集合: {collection_name}")
            else:
                print(f"  ⚠️  集合已存在: {collection_name}")
        
        # 创建索引
        print("🔍 创建数据库索引...")
        
        # 股票数据索引
        db.stock_data.create_index([("symbol", 1), ("date", 1)])
        db.stock_data.create_index([("market", 1)])
        db.stock_data.create_index([("created_at", 1)])
        
        # 市场数据索引
        db.market_data.create_index([("symbol", 1), ("timestamp", 1)])
        db.market_data.create_index([("data_type", 1)])
        
        # 基本面数据索引
        db.fundamental_data.create_index([("symbol", 1), ("report_date", 1)])
        db.fundamental_data.create_index([("data_source", 1)])
        
        # 新闻数据索引
        db.news_data.create_index([("symbol", 1), ("published_date", 1)])
        db.news_data.create_index([("source", 1)])
        
        # 社交数据索引
        db.social_data.create_index([("symbol", 1), ("timestamp", 1)])
        db.social_data.create_index([("platform", 1)])
        
        # 分析报告索引
        db.analysis_reports.create_index([("symbol", 1), ("analysis_type", 1)])
        db.analysis_reports.create_index([("created_at", 1)])
        
        # 分析结果索引
        db.analysis_results.create_index([("symbol", 1), ("analysis_date", 1)])
        db.analysis_results.create_index([("analyst_type", 1)])
        
        # 用户会话索引（24小时过期）
        db.user_sessions.create_index([("session_id", 1)])
        db.user_sessions.create_index([("created_at", 1)], expireAfterSeconds=86400)
        
        # 系统日志索引（7天过期）
        db.system_logs.create_index([("level", 1), ("timestamp", 1)])
        db.system_logs.create_index([("timestamp", 1)], expireAfterSeconds=604800)
        
        # 元数据索引
        db.metadata.create_index([("key", 1)], unique=True)
        
        print("✅ 索引创建完成")
        
        # 插入初始元数据
        print("📝 插入初始配置数据...")
        from datetime import datetime
        
        try:
            db.metadata.insert_one({
                "key": "database_version",
                "value": "1.0.0",
                "created_at": datetime.now(),
                "description": "TradingAgents 数据库版本"
            })
        except pymongo.errors.DuplicateKeyError:
            pass
        
        try:
            db.metadata.insert_one({
                "key": "initialization_date",
                "value": datetime.now(),
                "created_at": datetime.now(),
                "description": "数据库初始化日期"
            })
        except pymongo.errors.DuplicateKeyError:
            pass
        
        print("✅ 初始数据插入完成")
        
        # 显示数据库状态
        print("\n📊 数据库状态:")
        print(f"  数据库名称: {db.name}")
        collections = db.list_collection_names()
        print(f"  集合数量: {len(collections)}")
        print(f"  集合列表: {', '.join(collections)}")
        
        # 显示连接信息
        print("\n🔗 连接信息:")
        print("  管理员连接: mongodb://admin:tradingagents123@localhost:27017/?authSource=admin")
        print("  应用连接: mongodb://tradingagents:tradingagents123@localhost:27017/tradingagents?authSource=tradingagents")
        
        client.close()
        return True
        
    except ImportError:
        print("❌ pymongo包未安装，请运行: pip install pymongo")
        return False
    except pymongo.errors.ServerSelectionTimeoutError:
        print("❌ MongoDB连接超时，请检查服务是否运行")
        print("💡 请确保MongoDB服务正在运行: net start MongoDB")
        return False
    except Exception as e:
        print(f"❌ MongoDB配置失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 TradingAgents MongoDB 初始化")
    print("=" * 50)
    
    success = setup_mongodb()
    
    if success:
        print("\n🎉 MongoDB 配置完成！")
        print("现在可以运行数据库连接测试:")
        print("python scripts/test_database_connections.py")
    else:
        print("\n❌ MongoDB 配置失败")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
