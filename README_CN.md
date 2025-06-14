<p align="right">
<img src="https://flagicons.lipis.dev/flags/4x3/cn.svg" width="30" height="24">
</p>

# Endstone MCP Server

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/version-0.1.2-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-%3E=3.8-blue?logo=python" alt="Python version">
</p>

一个为 EndstoneMC 开发提供支持的 Model Context Protocol (MCP) 服务器。

<p align="center">
<a href="README.md">
<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="30" height="24">
</a>
</p>

## 功能特性

- **模块信息查询**: 获取 Endstone 模块的详细信息和导出内容
- **代码搜索**: 在所有 Endstone 模块中搜索类、函数和常量
- **插件模板生成**: 根据需求生成基础插件模板
- **事件处理指导**: 提供事件处理的详细信息和示例
- **开发教程**: 内置插件开发、事件处理和命令创建指南

## 安装或启动

### 用 uvx

```bash
uvx mcp-server-endstone
```

### 用源码

```bash
git clone https://github.com/Mcayear/mcp-server-endstone
cd mcp-server-endstone
pip install -e .

# 安装后启动
mcp-server-endstone
```

### 单元测试
```bash
python -m tests.test_server
```

## 使用方法

### 直接启动服务器

```bash
mcp-server-endstone [--reference 引用文件路径]
```

### 与 MCP 客户端集成

在你的 MCP 客户端配置中添加:

> 示例可直接用于：cursor、trae

```json
{
  "mcpServers": {
    "endstone": {
      "command": "uvx",
      "args": [
        "mcp-server-endstone"
      ]
    }
  }
}
```

## 可用工具

### 1. get_module_info
获取特定 Endstone 模块的信息

**参数:**
- `module_name`: 模块名称 (例如: 'endstone.event', 'endstone.plugin')

**示例:**
```
工具: get_module_info
参数: {"module_name": "endstone.event"}
```

### 2. search_exports
在所有模块中搜索特定的导出项

**参数:**
- `query`: 搜索词 (类名、函数名等)

**示例:**
```
工具: search_exports
参数: {"query": "Player"}
```

### 3. get_symbol_info
获取 Endstone 中特定符号（如类、事件）的详细定义，包括其文档、属性和方法。

**参数:**
- `symbol_name`: 符号名称 (例如: 'PlayerInteractEvent', 'Plugin')

**示例:**
```
工具: get_symbol_info
参数: {"symbol_name": "PlayerInteractEvent"}
```

### 4. generate_plugin_template
生成基础插件模板，包含指定功能

**参数:**
- `plugin_name`: 插件名称 (必须以 '_plugin' 结尾)
- `features`: 功能列表 (可选: 'commands', 'events', 'permissions')

**示例:**
```
工具: generate_plugin_template
参数: {
  "plugin_name": "example_plugin",
  "features": ["events", "commands"]
}
```

### 5. get_event_info
获取事件相关信息。如果提供了 `event_type`，则返回该事件的详细定义（属性、文档）和用法示例。否则，列出所有可用事件。

**参数:**
- `event_type`: 特定事件类型 (可选)

**示例:**
```
工具: get_event_info
参数: {"event_type": "PlayerJoinEvent"}
```

### 6. read_tutorials
获取教程内容。如未指定教程名称，则列出所有可用教程。

**参数:**
- `query`: 教程名称 (可选)

**示例:**
```
工具: read_tutorials
参数: {"query": "register-commands"}
```

## 支持的 Endstone 模块

- `endstone` - 核心模块
- `endstone.actor` - 实体相关
- `endstone.ban` - 封禁系统
- `endstone.block` - 方块操作
- `endstone.boss` - Boss栏
- `endstone.command` - 命令系统
- `endstone.damage` - 伤害系统
- `endstone.enchantments` - 附魔
- `endstone.event` - 事件系统
- `endstone.form` - 表单UI
- `endstone.inventory` - 物品栏
- `endstone.lang` - 语言本地化
- `endstone.level` - 世界/维度
- `endstone.map` - 地图
- `endstone.permissions` - 权限系统
- `endstone.plugin` - 插件基础
- `endstone.scheduler` - 任务调度
- `endstone.scoreboard` - 计分板
- `endstone.util` - 工具类

## 开发示例

### 基础插件结构

```python
from endstone.plugin import Plugin
from endstone import Logger

class MyPlugin(Plugin):
    name = "MyPlugin"
    version = "1.0.0"
    api_version = "0.5"
    
    def on_enable(self) -> None:
        self.logger.info(f"{self.name} v{self.version} enabled!")
    
    def on_disable(self) -> None:
        self.logger.info(f"{self.name} disabled!")
```

### 事件处理

```python
from endstone.event import event_handler, PlayerJoinEvent

@event_handler
def on_player_join(self, event: PlayerJoinEvent):
    player = event.player
    self.logger.info(f"Welcome {player.name}!")
    player.send_message("Welcome to the server!")
```

## 项目结构

```
mcp-server-endstone/
├── reference/         # 引用所需资源
│   ├── endstone/
│   └── tutorials/
├── src/
│   └── mcp_server_endstone/
│       ├── __init__.py
│       ├── server.py  # 核心服务器逻辑
│       ├── cli.py     # 命令行入口
│       └── reference/ # 引用文件
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── pyproject.toml
└── README.md
```

## 故障排除

1. **引用文件路径问题**: 服务器首先尝试从包内的reference目录加载引用文件，然后尝试从当前工作目录加载。如果两者都不存在，某些功能可能不可用。使用`--reference`参数指定引用文件路径。

2. **错误调试**: 服务器的日志级别为INFO，可以查看日志来诊断问题。

3. **依赖问题**: 确保所有依赖已正确安装: `mcp>=0.1.0`

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个 MCP 服务器。

## 致谢

[EndstoneMC](https://github.com/EndstoneMC/endstone) - 本项目的 `reference` 内容源于 `endstone/docs/reference` 与 `endstone/docs/tutorials`

## 许可证

MIT License