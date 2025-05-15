# Vidnoz 站点自动化工具

这个工具可以自动登录并更新 Vidnoz 管理网站的各种页面样式。

## 安装

```bash
pip install -r requirements.txt
```

## 站点配置

站点配置使用 JSON 格式，支持为每个站点指定标识符：

```json
{
  "urls": {
    "en": "http://manage.vidnoz.com/frontend/login",
    "jp": "http://manage-jp.vidnoz.com/frontend/login"
  }
}
```

## 运行方式

### 基本用法

处理配置文件中的所有站点：

```bash
python vidnoz_automation.py sites.json
```

### 高级选项

#### 仅处理特定站点

使用 `--include` 选项指定需要处理的站点标识符：

```bash
# 仅处理 tw 站点
python vidnoz_automation.py sites.json --include=tw

# 处理 tw 和 en 站点
python vidnoz_automation.py sites.json --include=tw,kr
```

#### 排除特定站点

使用 `--exclude` 选项指定要排除的站点标识符：

```bash
# 排除 en 站点，处理其它所有站点
python vidnoz_automation.py sites.json --exclude=kr

# 排除 tw 和 en 站点，处理其它所有站点
python vidnoz_automation.py sites.json --exclude=tw,kr
```

## 更新模式设置

### 基本更新模式

默认情况下，脚本只更新"公共样式"。

### 全局刷新模式

如需启用全局刷新模式（处理所有页面和所有按钮），请修改脚本中的设置：

```python
# 在 vidnoz_automation.py 文件中修改：
EXECUTE_MULTI_PAGE_UPDATE = True
```

全局刷新模式会依次处理以下页面的所有按钮：

1. aritcle-list 页面
2. faq-list 页面
3. pressroom-list 页面（如果存在）

## 使用批处理文件（更简便的方式）

为了更方便地使用此工具，您可以使用提供的批处理文件：

```
run_vidnoz.bat
```

这个批处理文件提供了一个交互式菜单，让您可以：

1. 选择处理所有站点或指定特定站点
2. 选择包含或排除特定站点
3. 设置更新模式（基本或全局刷新）
4. 查看当前设置
5. 执行命令

### 使用方法

1. 双击运行 `run_vidnoz.bat`
2. 在菜单中进行选择
3. 查看当前设置确认无误
4. 选择"执行命令"开始运行

批处理文件会自动处理参数和设置，无需手动修改代码或记忆复杂的命令参数。
