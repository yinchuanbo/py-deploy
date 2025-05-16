import os
import sys
import subprocess
import shutil
from pathlib import Path

# 确保工作目录是脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 确保已安装所需的库
def install_if_missing(package):
    try:
        __import__(package)
        print(f"{package} 已安装")
    except ImportError:
        print(f"正在安装 {package}...")
        subprocess.call([sys.executable, "-m", "pip", "install", package])

install_if_missing("PyInstaller")
install_if_missing("selenium")

# 准备PyInstaller参数
pyinstaller_args = [
    'pyinstaller',
    '--name=VidnozAutomation',
    '--onefile',  # 打包成单个文件
    '--windowed',  # 无控制台窗口
    '--clean',
    '--noconfirm',
    'vidnoz_app.py'  # 主脚本
]

print("开始打包 Vidnoz 自动化工具...")
print(f"使用命令: {' '.join(pyinstaller_args)}")

# 运行PyInstaller
subprocess.call(pyinstaller_args)

# 确保dist目录存在
dist_dir = os.path.join(os.getcwd(), 'dist')
if not os.path.exists(dist_dir):
    print("警告: 打包可能失败，没有生成dist目录")
    sys.exit(1)

# 创建批处理文件
batch_file_path = os.path.join(dist_dir, '启动Vidnoz自动化工具.bat')
with open(batch_file_path, 'w', encoding='utf-8') as f:
    f.write('@echo off\n')
    f.write('echo 正在启动 Vidnoz 自动化工具...\n')
    f.write('start "" "VidnozAutomation.exe"\n')
    f.write('exit\n')

# 创建使用说明
help_file_path = os.path.join(dist_dir, '使用说明.txt')
with open(help_file_path, 'w', encoding='utf-8') as f:
    f.write('Vidnoz 自动化工具使用说明\n')
    f.write('====================\n\n')
    f.write('本工具支持自动登录各个区域的 Vidnoz 管理网站并执行更新操作。\n\n')
    f.write('一、使用方法\n')
    f.write('----------\n\n')
    f.write('1. 双击"启动Vidnoz自动化工具.bat"或直接双击"VidnozAutomation.exe"启动程序\n\n')
    f.write('2. 在控制面板中选择需要处理的站点:\n')
    f.write('   - 所有站点: 处理配置文件中的所有站点\n')
    f.write('   - 包含特定站点: 仅处理选中的站点\n')
    f.write('   - 排除特定站点: 处理除选中站点外的所有站点\n\n')
    f.write('3. 选择更新模式:\n')
    f.write('   - 基本更新: 仅更新公共样式\n')
    f.write('   - 多页面更新: 更新所有页面的样式和列表\n\n')
    f.write('4. 点击"开始执行"按钮启动自动化过程\n\n')
    f.write('5. 执行过程中可以在日志区域查看进度和状态\n\n')
    f.write('6. 完成后可以查看详细的执行结果\n\n')
    f.write('二、注意事项\n')
    f.write('----------\n\n')
    f.write('1. 确保计算机已安装Chrome浏览器\n\n')
    f.write('2. 首次运行可能会出现Windows安全提示，选择"仍然运行"即可\n\n')
    f.write('3. 程序首次运行会自动创建sites.json配置文件，如需修改站点配置，可编辑此文件\n\n')
    f.write('4. 执行过程中请勿关闭程序窗口\n\n')
    f.write('5. 多页面更新模式下，程序会依次访问多个页面并执行更新操作，耗时较长\n\n')
    f.write('6. 如遇到问题，可查看日志区域的具体错误信息\n\n')
    f.write('三、联系支持\n')
    f.write('----------\n\n')
    f.write('如有任何问题或需要帮助，请联系管理员。\n')

print("\n打包完成!")
print(f"可执行文件位于: {os.path.join(dist_dir, 'VidnozAutomation.exe')}")
print("已创建启动批处理文件")
print("已创建使用说明文档")

print("\n注意:")
print("1. 确保已安装 Chrome 浏览器")
print("2. 首次运行时，Windows 安全提示可能会出现，请选择'仍然运行'")
print("3. 程序会在首次运行时自动生成配置文件") 