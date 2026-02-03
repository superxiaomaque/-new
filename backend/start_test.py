"""
测试启动脚本（使用SQLite，无需MySQL）
"""
import sys
import os

# 使用测试配置
sys.path.insert(0, os.path.dirname(__file__))

# 替换config和database模块
import test_config as config_module
import test_database as database_module

# 将测试模块注入到sys.modules（必须在导入main之前）
sys.modules['config'] = config_module
sys.modules['database'] = database_module

# 替换routers中的导入
import importlib

# 修改auth.py中的导入
import routers.auth as auth_module
auth_module.config = config_module
auth_module.database = database_module

# 修改analyses.py中的导入
import routers.analyses as analyses_module
analyses_module.config = config_module
analyses_module.database = database_module

# 修改main.py中的导入
import main
main.database = database_module

# 初始化数据库
print("正在初始化数据库...")
database_module.init_db()
print("数据库初始化完成！")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("后端服务启动中...")
    print("访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("="*50 + "\n")
    uvicorn.run(main.app, host="0.0.0.0", port=8000, reload=True)
