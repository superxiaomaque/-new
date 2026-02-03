# 测试运行指南

## 🚀 快速启动（推荐）

### 方式一：使用测试模式（SQLite，无需MySQL）

#### 1. 启动后端

```bash
cd backend

# 安装依赖（首次运行）
pip install -r requirements_test.txt

# 启动测试服务器
python test_main.py
```

✅ 后端启动成功后会显示：
- 访问地址: http://localhost:8000
- API文档: http://localhost:8000/docs

#### 2. 启动前端

打开**新的终端窗口**：

```bash
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

✅ 前端启动成功后会显示：
- 访问地址: http://localhost:3000

## 📝 测试流程

1. **访问前端**
   - 打开浏览器访问：http://localhost:3000

2. **注册账号**
   - 点击"立即注册"
   - 输入手机号（任意11位数字，如：13800138000）
   - 输入密码（至少6位，如：123456）
   - 确认密码
   - 完成注册

3. **登录**
   - 使用刚才注册的账号登录

4. **上传图片分析**
   - 点击"开始分析"
   - 上传至少5张朋友圈截图（最多20张）
   - （可选）填写补充信息（性别、年龄等）
   - 点击"开始分析"

   ⚠️ **注意**：如果没有配置豆包API密钥，分析功能会失败

5. **查看结果**
   - 分析完成后会自动跳转到结果页面
   - 可以查看各个维度的分析结果
   - 可以尝试多轮对话功能

6. **查看历史记录**
   - 点击底部导航栏的"历史"
   - 查看之前的分析记录

## ⚙️ 配置豆包API密钥

如果需要测试完整的分析功能，需要配置豆包API密钥：

### 方法1：环境变量（推荐）

```bash
export DOUBAO_API_KEY=your-api-key-here
python test_main.py
```

### 方法2：修改配置文件

编辑 `backend/test_config.py`：

```python
DOUBAO_API_KEY: str = "your-api-key-here"
```

## 📋 功能测试清单

- [x] 用户注册
- [x] 用户登录
- [x] 图片上传（5-20张）
- [ ] AI分析（需要API密钥）
- [x] 查看分析结果
- [x] 多轮对话
- [x] 历史记录
- [x] 分享链接
- [x] 修改密码

## 🔧 常见问题

### Q1: 端口被占用？

**后端**：修改 `test_main.py` 中的端口号
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为8001
```

**前端**：修改 `vite.config.js` 中的端口号
```javascript
server: {
  port: 3001,  // 改为3001
}
```

### Q2: 依赖安装失败？

**Python依赖**：
- 确保Python版本 >= 3.9
- 使用虚拟环境：`python -m venv venv && source venv/bin/activate`

**Node.js依赖**：
- 确保Node.js版本 >= 16
- 清除缓存：`rm -rf node_modules package-lock.json && npm install`

### Q3: 数据库错误？

- 测试模式使用SQLite，无需MySQL
- 确保 `backend` 目录有写入权限
- 数据库文件：`backend/test.db`

### Q4: API调用失败？

- 检查 `DOUBAO_API_KEY` 是否配置
- 检查网络连接
- 查看后端终端错误信息

### Q5: 前端无法连接后端？

- 检查后端是否启动（访问 http://localhost:8000/docs）
- 检查 `vite.config.js` 中的 proxy 配置
- 检查浏览器控制台错误信息

## 📁 项目结构

```
朋友圈分析/
├── backend/
│   ├── test_main.py          # 测试启动文件（使用SQLite）
│   ├── test_config.py        # 测试配置
│   ├── test_database.py      # 测试数据库（SQLite）
│   ├── test_auth.py          # 测试认证
│   ├── test_routers/         # 测试路由
│   ├── services/             # 服务层
│   └── requirements_test.txt # 测试依赖
├── frontend/
│   ├── src/
│   └── package.json
└── README_测试.md           # 本文档
```

## 🎯 下一步

1. ✅ 配置真实的豆包API密钥
2. ✅ 测试完整功能流程
3. ⏳ 配置云存储（可选）
4. ⏳ 部署到生产环境

## 💡 提示

- 测试模式使用SQLite，数据保存在 `backend/test.db`
- 生产环境建议使用MySQL
- 图片当前保存在 `backend/uploads/` 目录
- 生产环境建议使用云存储（火山引擎TOS）
