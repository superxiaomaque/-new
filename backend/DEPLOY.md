# 后端部署指南

## 使用 Railway 部署（推荐）

### 步骤 1：准备 Railway 账号
1. 访问 https://railway.app
2. 使用 GitHub 账号登录
3. 点击 "New Project"

### 步骤 2：连接 GitHub 仓库
1. 选择 "Deploy from GitHub repo"
2. 选择你的仓库 `superxiaomaque/-new`
3. Railway 会自动检测到 `backend` 目录

### 步骤 3：配置项目
1. 在 Railway 项目设置中，找到 "Settings"
2. 设置 **Root Directory** 为 `backend`
3. 设置 **Start Command** 为：`uvicorn main:app --host 0.0.0.0 --port $PORT`

### 步骤 4：配置环境变量
在 Railway 项目的 "Variables" 标签中，添加以下环境变量：

```
DATABASE_URL=sqlite:///./data.db
SECRET_KEY=你的随机密钥（至少32个字符）
DOUBAO_API_KEY=你的豆包API密钥
DOUBAO_API_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-1-6-flash-250828
STORAGE_BACKEND=local
```

**重要：**
- `SECRET_KEY` 需要生成一个随机字符串（可以使用：`openssl rand -hex 32`）
- `DOUBAO_API_KEY` 从火山引擎控制台获取
- `DATABASE_URL` 使用 SQLite（Railway 会自动创建持久化存储）

### 步骤 5：部署
1. Railway 会自动开始构建和部署
2. 等待部署完成（通常 2-3 分钟）
3. 部署完成后，Railway 会提供一个 URL（例如：`https://your-app.railway.app`）

### 步骤 6：配置前端
1. 复制 Railway 提供的后端 URL
2. 在 Vercel 项目设置中，添加环境变量：
   - 名称：`VITE_API_BASE_URL`
   - 值：你的 Railway URL（例如：`https://your-app.railway.app`）
3. 重新部署前端

## 使用 Render 部署（备选）

### 步骤 1：准备 Render 账号
1. 访问 https://render.com
2. 使用 GitHub 账号登录

### 步骤 2：创建 Web Service
1. 点击 "New" → "Web Service"
2. 连接你的 GitHub 仓库
3. 设置：
   - **Name**: `friend-circle-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 步骤 3：配置环境变量
在 Render 的 "Environment" 标签中添加环境变量（同 Railway）

### 步骤 4：部署
Render 会自动部署，完成后会提供 URL

## 注意事项

1. **数据库持久化**：
   - SQLite 文件需要持久化存储
   - Railway 会自动处理
   - Render 需要使用 PostgreSQL（需要修改 `DATABASE_URL`）

2. **文件上传**：
   - 上传的文件会保存在 `uploads/` 目录
   - 需要配置持久化存储或使用云存储（TOS）

3. **CORS 配置**：
   - 后端已配置允许所有来源（`allow_origins=["*"]`）
   - 生产环境建议限制为前端域名

4. **端口配置**：
   - Railway/Render 会自动设置 `PORT` 环境变量
   - 代码已配置使用 `$PORT`
