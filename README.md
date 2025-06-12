# Endstone MCP Server

一个为 EndstoneMC 开发提供支持的 Model Context Protocol (MCP) 服务器。

## 功能特性

- **模块信息查询**: 获取 Endstone 模块的详细信息和导出内容
- **代码搜索**: 在所有 Endstone 模块中搜索类、函数和常量
- **插件模板生成**: 根据需求生成基础插件模板
- **事件处理指导**: 提供事件处理的详细信息和示例
- **开发指南**: 内置插件开发、事件处理和命令创建指南

## 安装

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 确保 Endstone 参考文件位于正确路径:
```
path/to/reference/endstone/
```

## 使用方法

### 作为独立服务器运行

```bash
python endstone_mcp_server.py
```

### 与 MCP 客户端集成

在你的 MCP 客户端配置中添加:

```json
{
  "mcpServers": {
    "endstone": {
      "command": "python",
      "args": ["path/to/endstone_mcp_server.py"]
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

### 3. generate_plugin_template
生成基础插件模板

**参数:**
- `plugin_name`: 插件名称
- `features`: 功能列表 (可选: 'commands', 'events', 'permissions')

**示例:**
```
工具: generate_plugin_template
参数: {
  "plugin_name": "MyAwesome",
  "features": ["events", "commands"]
}
```

### 4. get_event_info
获取事件相关信息

**参数:**
- `event_type`: 特定事件类型 (可选)

**示例:**
```
工具: get_event_info
参数: {"event_type": "PlayerJoinEvent"}
```

## 可用提示

### 1. plugin_development
获取插件开发指南

### 2. event_handling
学习事件处理机制

### 3. command_creation
了解自定义命令创建

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
    
    def __init__(self):
        super().__init__()
        self.logger: Logger = self.get_logger()
    
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

## 故障排除

1. **模块未找到**: 确保 Endstone 参考文件路径正确
2. **权限错误**: 检查文件读取权限
3. **依赖问题**: 确保所有依赖已正确安装

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个 MCP 服务器。

## 许可证

MIT License