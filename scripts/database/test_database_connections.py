#!/usr/bin/env python3
"""
数据库连接测试脚本 - TradingAgents
测试Redis和MongoDB连接是否正常
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_redis_connection():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")
    
    try:
        import redis
        
        # 从环境变量读取配置
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD", "tradingagents123")
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        print(f"  连接参数: {redis_host}:{redis_port}, DB:{redis_db}")
        
        # 创建Redis客户端
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            socket_timeout=5,
            decode_responses=True
        )
        
        # 测试连接
        response = client.ping()
        if response:
            print("  ✅ Redis连接成功")
            
            # 测试基本操作
            client.set("test_key", "Hello TradingAgents")
            value = client.get("test_key")
            if value == "Hello TradingAgents":
                print("  ✅ Redis读写测试成功")
                client.delete("test_key")
            else:
                print("  ❌ Redis读写测试失败")
                
            # 显示Redis信息
            info = client.info()
            print(f"  📊 Redis版本: {info.get('redis_version', 'Unknown')}")
            print(f"  📊 已用内存: {info.get('used_memory_human', 'Unknown')}")
            
            return True
        else:
            print("  ❌ Redis连接失败")
            return False
            
    except ImportError:
        print("  ❌ redis包未安装，请运行: pip install redis")
        return False
    except redis.AuthenticationError:
        print("  ❌ Redis认证失败，请检查密码配置")
        return False
    except redis.ConnectionError as e:
        print(f"  ❌ Redis连接错误: {e}")
        print("  💡 请确保Redis服务正在运行")
        return False
    except Exception as e:
        print(f"  ❌ Redis测试失败: {e}")
        return False

def test_mongodb_connection():
    """测试MongoDB连接"""
    print("\n🔍 测试MongoDB连接...")
    
    try:
        import pymongo
        from pymongo import MongoClient
        
        # 从环境变量读取配置
        mongodb_host = os.getenv("MONGODB_HOST", "localhost")
        mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongodb_username = os.getenv("MONGODB_USERNAME", "admin")
        mongodb_password = os.getenv("MONGODB_PASSWORD", "tradingagents123")
        mongodb_database = os.getenv("MONGODB_DATABASE", "tradingagents")
        mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
        
        print(f"  连接参数: {mongodb_host}:{mongodb_port}, DB:{mongodb_database}")
        
        # 构建连接字符串
        if mongodb_username and mongodb_password:
            connection_string = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_database}?authSource={mongodb_auth_source}"
        else:
            connection_string = f"mongodb://{mongodb_host}:{mongodb_port}/{mongodb_database}"
        
        # 创建MongoDB客户端
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # 测试连接
        client.admin.command('ping')
        print("  ✅ MongoDB连接成功")
        
        # 获取数据库
        db = client[mongodb_database]
        
        # 测试基本操作
        test_collection = db.test_collection
        test_doc = {"test_key": "Hello TradingAgents", "timestamp": "2024-01-01"}
        
        # 插入测试文档
        result = test_collection.insert_one(test_doc)
        if result.inserted_id:
            print("  ✅ MongoDB写入测试成功")
            
            # 读取测试文档
            found_doc = test_collection.find_one({"_id": result.inserted_id})
            if found_doc and found_doc["test_key"] == "Hello TradingAgents":
                print("  ✅ MongoDB读取测试成功")
                
                # 删除测试文档
                test_collection.delete_one({"_id": result.inserted_id})
            else:
                print("  ❌ MongoDB读取测试失败")
        else:
            print("  ❌ MongoDB写入测试失败")
        
        # 显示MongoDB信息
        server_info = client.server_info()
        print(f"  📊 MongoDB版本: {server_info.get('version', 'Unknown')}")
        
        # 显示数据库列表
        db_list = client.list_database_names()
        print(f"  📊 数据库列表: {', '.join(db_list)}")
        
        client.close()
        return True
        
    except ImportError:
        print("  ❌ pymongo包未安装，请运行: pip install pymongo")
        return False
    except pymongo.errors.OperationFailure as e:
        if "Authentication failed" in str(e):
            print("  ❌ MongoDB认证失败，请检查用户名和密码")
            print("  💡 提示：请确保已创建用户并启用认证")
        else:
            print(f"  ❌ MongoDB操作失败: {e}")
        return False
    except pymongo.errors.ServerSelectionTimeoutError:
        print("  ❌ MongoDB连接超时，请检查服务是否运行")
        print("  💡 请确保MongoDB服务正在运行")
        return False
    except Exception as e:
        print(f"  ❌ MongoDB测试失败: {e}")
        return False

def test_environment_variables():
    """测试环境变量配置"""
    print("\n🔍 检查环境变量配置...")
    
    # 检查.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        print("  ✅ .env文件存在")
        
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("  ✅ 环境变量加载成功")
        except ImportError:
            print("  ⚠️  python-dotenv未安装，使用系统环境变量")
    else:
        print("  ❌ .env文件不存在")
        return False
    
    # 检查数据库启用状态
    mongodb_enabled = os.getenv("MONGODB_ENABLED", "false").lower() == "true"
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    
    print(f"  📊 MongoDB启用: {mongodb_enabled}")
    print(f"  📊 Redis启用: {redis_enabled}")
    
    return True

def main():
    """主函数"""
    print("🚀 TradingAgents 数据库连接测试")
    print("=" * 50)
    
    # 测试环境变量
    env_ok = test_environment_variables()
    
    # 测试Redis连接
    redis_ok = test_redis_connection()
    
    # 测试MongoDB连接
    mongodb_ok = test_mongodb_connection()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  环境变量配置: {'✅ 正常' if env_ok else '❌ 异常'}")
    print(f"  Redis连接: {'✅ 正常' if redis_ok else '❌ 异常'}")
    print(f"  MongoDB连接: {'✅ 正常' if mongodb_ok else '❌ 异常'}")
    
    if redis_ok and mongodb_ok:
        print("\n🎉 所有数据库连接测试通过！")
        return True
    else:
        print("\n⚠️  部分数据库连接失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
