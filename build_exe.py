import os
import sys
import subprocess
import base64
from pathlib import Path

# 确保工作目录是脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 确保已安装所需的库
try:
    import PyInstaller
except ImportError:
    print("正在安装 PyInstaller...")
    subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"])

# 确保已安装 selenium
try:
    import selenium
except ImportError:
    print("正在安装 selenium...")
    subprocess.call([sys.executable, "-m", "pip", "install", "selenium"])

# 准备 PyInstaller 参数
pyinstaller_args = [
    'pyinstaller',
    '--name=VidnozAutomation',
    '--onefile',  # 打包成单个文件
    '--windowed',  # 无控制台窗口
    '--noupx',
    '--clean',
    '--log-level=INFO',
    # 确保添加所需文件
    '--add-data=sites.json;.',
    # 在这里添加其他资源文件，如果有的话
    'vidnoz_gui.py'  # 主脚本
]

# 确保 sites.json 存在
if not os.path.exists('sites.json'):
    print("错误: sites.json 文件不存在!")
    sys.exit(1)

# 确保 vidnoz_automation.py 存在
if not os.path.exists('vidnoz_automation.py'):
    print("错误: vidnoz_automation.py 文件不存在!")
    sys.exit(1)

print("开始打包 Vidnoz 自动化工具...")
print(f"使用命令: {' '.join(pyinstaller_args)}")

# 运行 PyInstaller
subprocess.call(pyinstaller_args)

print("\n打包完成!")
print("可执行文件位于: dist/VidnozAutomation.exe")
print("\n注意:")
print("1. 确保已安装 Chrome 浏览器")
print("2. 首次运行时，Windows 安全提示可能会出现，请选择'仍然运行'")
print("3. 若需修改站点配置，请编辑 dist/sites.json 文件") 