# 数据库配置文件说明

本目录包含TradingAgents项目的数据库配置相关文件。

## 📁 文件结构

### 配置文件 (config/)
- `redis.conf` - Redis 8.0.3 配置文件
- `mongod_8011.cfg` - MongoDB 8.1.2 配置文件

### 脚本文件 (scripts/database/)
- `setup_mongodb_python.py` - MongoDB初始化脚本 (Python版本)
- `test_database_connections.py` - 数据库连接测试脚本
- `mongodb_8011_install_guide.md` - MongoDB安装指南

### Docker配置 (scripts/docker/)
- `mongo-init.js` - Docker环境MongoDB初始化脚本

## 🚀 使用方法

### 1. 安装数据库
按照 `mongodb_8011_install_guide.md` 安装MongoDB和Redis

### 2. 初始化MongoDB
```bash
python scripts/database/setup_mongodb_python.py
```

### 3. 测试连接
```bash
python scripts/database/test_database_connections.py
```

## 📊 数据库信息

### Redis
- 版本: 8.0.3
- 端口: 6379
- 密码: tradingagents123

### MongoDB  
- 版本: 8.1.2
- 端口: 27017
- 数据库: tradingagents
- 用户: admin/tradingagents123

## 🔗 连接字符串

### Redis
```
redis://:tradingagents123@localhost:6379
```

### MongoDB
```
mongodb://admin:tradingagents123@localhost:27017/tradingagents?authSource=admin
```
