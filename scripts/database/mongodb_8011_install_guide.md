# MongoDB 8.0.11 安装配置指南 - TradingAgents

## 🎯 版本说明
MongoDB 8.0.11 是最新的稳定版本，具有以下优势：
- ✅ 更好的性能和稳定性
- ✅ 增强的安全特性
- ✅ 改进的查询优化器
- ✅ 完全向后兼容

## 📥 下载和安装

### 1. 下载 MongoDB 8.0.11
- 访问: https://www.mongodb.com/try/download/community
- 版本: **8.0.11 (Current)**
- 平台: **Windows x64**
- 包格式: **msi**

### 2. 安装步骤
1. **运行安装程序**
   - 双击下载的 `.msi` 文件
   - 选择 "Complete" 完整安装

2. **服务配置**
   - ✅ 勾选 "Install MongoDB as a Service"
   - 服务名称: `MongoDB`
   - 服务用户: **Run service as Network Service user** (推荐)
   - 数据目录: `D:\MongoDB\data`
   - 日志目录: `D:\MongoDB\logs`

3. **MongoDB Compass (可选)**
   - ✅ 勾选安装 MongoDB Compass (图形化管理工具)

## 🔧 配置 MongoDB

### 1. 验证安装
```cmd
# 检查MongoDB版本
mongod --version

# 检查MongoDB Shell版本
mongosh --version
```

### 2. 启动MongoDB服务
```cmd
# 启动服务
net start MongoDB

# 检查服务状态
sc query MongoDB
```

### 3. 连接到MongoDB
```cmd
# 使用MongoDB Shell连接
mongosh
```

### 4. 创建管理员用户
在 `mongosh` 中执行：
```javascript
// 切换到admin数据库
use admin

// 创建超级管理员用户
db.createUser({
  user: "admin",
  pwd: "tradingagents123",
  roles: [
    "userAdminAnyDatabase",
    "readWriteAnyDatabase", 
    "dbAdminAnyDatabase",
    "clusterAdmin"
  ]
})

// 验证用户创建
db.getUsers()
```

### 5. 启用认证
编辑MongoDB配置文件 `C:\Program Files\MongoDB\Server\8.0\bin\mongod.cfg`：
```yaml
# MongoDB 8.0.11 配置文件
systemLog:
  destination: file
  path: C:\data\log\mongod.log
  logAppend: true

storage:
  dbPath: C:\data\db
  journal:
    enabled: true

net:
  port: 27017
  bindIp: 127.0.0.1

security:
  authorization: enabled

setParameter:
  enableLocalhostAuthBypass: false
```

### 6. 重启MongoDB服务
```cmd
# 重启服务以应用配置
net stop MongoDB
net start MongoDB
```

### 7. 创建应用数据库和用户
```cmd
# 使用管理员身份连接
mongosh -u admin -p tradingagents123 --authenticationDatabase admin
```

在 `mongosh` 中执行：
```javascript
// 切换到应用数据库
use tradingagents

// 创建应用用户
db.createUser({
  user: "tradingagents",
  pwd: "tradingagents123",
  roles: [
    { role: "readWrite", db: "tradingagents" },
    { role: "dbAdmin", db: "tradingagents" }
  ]
})

// 验证用户
db.getUsers()
```

## 🗄️ 初始化数据库结构

### 运行初始化脚本
```cmd
# 在项目根目录执行
mongosh -u admin -p tradingagents123 --authenticationDatabase admin < scripts\setup_mongodb_users.js
```

## ✅ 验证配置

### 1. 测试连接
```javascript
// 测试管理员连接
mongosh "mongodb://admin:tradingagents123@localhost:27017/?authSource=admin"

// 测试应用用户连接
mongosh "mongodb://tradingagents:tradingagents123@localhost:27017/tradingagents?authSource=tradingagents"
```

### 2. 检查数据库
```javascript
// 显示所有数据库
show dbs

// 切换到应用数据库
use tradingagents

// 显示集合
show collections

// 检查索引
db.stock_data.getIndexes()
```

## 🔗 连接信息

### 管理员连接
```
mongodb://admin:tradingagents123@localhost:27017/?authSource=admin
```

### 应用连接 (推荐)
```
mongodb://tradingagents:tradingagents123@localhost:27017/tradingagents?authSource=tradingagents
```

## 🛠️ 故障排除

### 常见问题

1. **服务启动失败**
   ```cmd
   # 检查日志
   type "C:\data\log\mongod.log"
   ```

2. **认证失败**
   - 确保用户名密码正确
   - 检查 `authSource` 参数

3. **连接超时**
   - 确保防火墙允许27017端口
   - 检查服务是否运行

### 性能优化 (MongoDB 8.0.11)
```javascript
// 启用查询计划缓存
db.adminCommand({setParameter: 1, planCacheSizeGB: 1})

// 设置连接池大小
db.adminCommand({setParameter: 1, maxIncomingConnections: 1000})
```

## 🎉 完成
MongoDB 8.0.11 配置完成！您现在可以：
- 使用图形化工具 MongoDB Compass 管理数据库
- 运行 TradingAgents 项目的数据库测试
- 开始使用高性能的数据存储功能
