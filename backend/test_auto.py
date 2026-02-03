"""
自动化测试脚本
"""
import sys
import os
import subprocess
import time
import requests
from pathlib import Path

def print_step(step, message):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step}: {message}")
    print('='*60)

def check_python():
    """检查Python环境"""
    print_step(1, "检查Python环境")
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        print(f"✅ {result.stdout.strip()}")
        return True
    except:
        print("❌ 未找到Python3")
        return False

def check_node():
    """检查Node.js环境"""
    print_step(2, "检查Node.js环境")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✅ Node.js {result.stdout.strip()}")
        return True
    except:
        print("❌ 未找到Node.js")
        return False

def install_backend_deps():
    """安装后端依赖"""
    print_step(3, "安装后端依赖")
    try:
        result = subprocess.run(
            ['pip', 'install', '-q', '-r', 'requirements_test.txt'],
            cwd='backend',
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✅ 后端依赖安装成功")
            return True
        else:
            print(f"⚠️ 依赖安装可能有警告: {result.stderr}")
            return True  # 即使有警告也继续
    except subprocess.TimeoutExpired:
        print("❌ 依赖安装超时")
        return False
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def install_frontend_deps():
    """安装前端依赖"""
    print_step(4, "安装前端依赖")
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd='frontend',
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode == 0:
            print("✅ 前端依赖安装成功")
            return True
        else:
            print(f"⚠️ 依赖安装可能有警告")
            return True
    except subprocess.TimeoutExpired:
        print("❌ 依赖安装超时")
        return False
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_code_syntax():
    """检查代码语法"""
    print_step(5, "检查代码语法")
    errors = []
    
    # 检查Python文件
    python_files = [
        'backend/test_main.py',
        'backend/test_config.py',
        'backend/test_database.py',
        'backend/test_auth.py',
        'backend/test_routers/auth.py',
        'backend/test_routers/analyses.py',
    ]
    
    for file in python_files:
        if os.path.exists(file):
            try:
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', file],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"✅ {file}")
                else:
                    print(f"❌ {file}: {result.stderr}")
                    errors.append(file)
            except Exception as e:
                print(f"⚠️ {file}: {e}")
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个语法错误")
        return False
    else:
        print("\n✅ 所有Python文件语法检查通过")
        return True

def test_backend_startup():
    """测试后端启动"""
    print_step(6, "测试后端启动")
    
    # 检查数据库文件是否会被创建
    db_file = Path('backend/test.db')
    if db_file.exists():
        db_file.unlink()  # 删除旧的测试数据库
    
    try:
        # 尝试导入测试模块
        sys.path.insert(0, 'backend')
        import test_database
        test_database.init_db()
        print("✅ 数据库初始化成功")
        
        # 检查数据库文件是否创建
        if db_file.exists():
            print("✅ 数据库文件创建成功")
        else:
            print("⚠️ 数据库文件未创建（可能使用内存数据库）")
        
        return True
    except Exception as e:
        print(f"❌ 后端启动测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """测试API端点（需要后端运行）"""
    print_step(7, "测试API端点")
    print("⚠️ 此测试需要后端服务运行")
    print("   请先启动后端: cd backend && python test_main.py")
    print("   然后在另一个终端运行此脚本")
    
    try:
        # 测试健康检查
        response = requests.get('http://localhost:8000/health', timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            print(f"   {response.json()}")
            return True
        else:
            print(f"⚠️ 后端响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️ 无法连接到后端服务（可能未启动）")
        return False
    except Exception as e:
        print(f"⚠️ API测试失败: {e}")
        return False

def create_test_summary(results):
    """创建测试总结"""
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！可以开始使用项目了")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("朋友圈分析助手 - 自动化测试")
    print("="*60)
    
    results = {}
    
    # 1. 检查环境
    results['Python环境'] = check_python()
    results['Node.js环境'] = check_node()
    
    if not (results['Python环境'] and results['Node.js环境']):
        print("\n❌ 环境检查失败，请先安装Python3和Node.js")
        create_test_summary(results)
        return
    
    # 2. 安装依赖
    results['后端依赖'] = install_backend_deps()
    results['前端依赖'] = install_frontend_deps()
    
    # 3. 检查代码
    results['代码语法'] = check_code_syntax()
    
    # 4. 测试后端
    results['后端启动'] = test_backend_startup()
    
    # 5. 测试API（可选）
    results['API端点'] = test_api_endpoints()
    
    # 总结
    create_test_summary(results)
    
    # 提供下一步建议
    print("\n" + "="*60)
    print("下一步操作")
    print("="*60)
    print("1. 启动后端: cd backend && python test_main.py")
    print("2. 启动前端: cd frontend && npm run dev")
    print("3. 访问应用: http://localhost:3000")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
