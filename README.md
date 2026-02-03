# 朋友圈截图分析交友助手

基于豆包大模型（doubao-seed-1.6-thinking）的智能分析工具，通过分析目标对象的朋友圈截图，为用户提供个性化的交友建议和沟通策略。

## 项目结构

```
朋友圈分析/
├── frontend/          # 前端项目（Vue.js 3）
├── backend/           # 后端项目（Python FastAPI）
├── PRD.md            # 产品需求文档
└── README.md         # 项目说明文档
```

## 技术栈

### 前端
- Vue.js 3
- Vant（移动端UI组件库）
- Axios
- Pinia
- Vue Router

### 后端
- Python 3.9+
- FastAPI
- MySQL
- Redis（可选）
- 火山引擎TOS（云存储）
- 豆包大模型API

## 快速开始

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 后端开发
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 一键运行（推荐）

如果你不想手动折腾环境/数据库，直接看 `一键运行.md`，推荐使用测试模式（SQLite）一键启动。

## 功能特性

- ✅ 用户登录注册（手机号+密码）
- ✅ 图片上传（5-20张，单张10MB）
- ✅ AI智能分析（豆包大模型）
- ✅ 完整版分析结果（匹配度评分、详细攻略等）
- ✅ 历史记录管理（标签分类、批量导出）
- ✅ 分享导出功能（分享链接、图片导出）
- ✅ 多轮对话（基于分析结果追问）

## 开发计划

- Week 1: 需求确认、设计完成
- Week 2: 前端开发完成
- Week 3: 后端开发完成
- Week 4: 测试、优化、上线

## 许可证

MIT License
