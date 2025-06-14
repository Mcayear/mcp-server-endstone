#!/usr/bin/env python3
"""
Endstone MCP Server

A Model Context Protocol server for Endstone Minecraft server development.
Provides code completion, documentation, and development assistance.
"""

import asyncio
import json
import logging
import sys
import ast
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    Resource,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("endstone-mcp")

class EndstoneMCPServer:
    def __init__(self, reference_path=None):
        self.server = Server("endstone-mcp")
        
        # 确定引用路径
        if reference_path:
            self.reference_path = Path(reference_path)
        else:
            # 优先寻找包内的reference目录
            package_ref = Path(__file__).parent / "reference"
            # 然后检查当前工作目录下的引用路径
            cwd_ref = Path.cwd() / "reference"
            
            if package_ref.exists():
                self.reference_path = package_ref
                logger.info(f"使用包内reference路径: {package_ref}")
            elif cwd_ref.exists():
                self.reference_path = cwd_ref
                logger.info(f"使用当前目录reference路径: {cwd_ref}")
            else:
                logger.warning("引用路径未找到，某些功能可能不可用")
                self.reference_path = Path(__file__).parent / "reference"
        
        # 定义引用路径
        self.ENDSTONE_REF_PATH = self.reference_path / "endstone"
        self.ENDSTONE_PYI_PATH = self.reference_path / "endstone/_internal/endstone_python.pyi"
        self.TUTORIALS_PATH = self.reference_path / "tutorials"
        
        # 加载模块和定义
        self.endstone_modules = self._load_endstone_modules()
        self.pyi_definitions = self._load_pyi_definitions(self.ENDSTONE_PYI_PATH)
        self._setup_handlers()
    
    def _load_pyi_definitions(self, file_path: Path) -> Dict[str, Any]:
        """Parse a .pyi file and extract class information using AST."""
        if not file_path.exists():
            logger.warning(f"PYI file not found at {file_path}")
            return {}

        content = file_path.read_text(encoding='utf-8')
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Failed to parse PYI file {file_path}: {e}")
            return {}

        classes = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                class_doc = ast.get_docstring(node)

                properties = []
                methods = []

                for body_item in node.body:
                    if isinstance(body_item, ast.FunctionDef):
                        is_property = any(
                            isinstance(d, ast.Name) and d.id == 'property'
                            for d in body_item.decorator_list
                        )

                        func_name = body_item.name
                        func_doc = ast.get_docstring(body_item)

                        return_type = None
                        if body_item.returns:
                            try:
                                return_type = ast.unparse(body_item.returns)
                            except AttributeError:
                                if isinstance(body_item.returns, ast.Name):
                                    return_type = body_item.returns.id
                                elif isinstance(body_item.returns, ast.Constant):
                                    return_type = str(body_item.returns.value)
                                else:
                                    return_type = "ComplexType"

                        params = []
                        all_args = body_item.args.args + body_item.args.kwonlyargs
                        for arg in all_args:
                            if arg.arg == 'self':
                                continue
                            
                            param_name = arg.arg
                            param_type = "Any"
                            if arg.annotation:
                                try:
                                    param_type = ast.unparse(arg.annotation)
                                except AttributeError: # Fallback for older python
                                    if isinstance(arg.annotation, ast.Name):
                                        param_type = arg.annotation.id
                                    else:
                                        param_type = "ComplexType"
                            
                            params.append({"name": param_name, "type": param_type})

                        item_info = {
                            "name": func_name,
                            "doc": func_doc,
                            "return_type": return_type,
                            "params": params,
                        }

                        if is_property:
                            properties.append(item_info)
                        else:
                            methods.append(item_info)

                classes[class_name] = {
                    "doc": class_doc,
                    "properties": properties,
                    "methods": methods,
                }
        return classes
    
    def _load_endstone_modules(self) -> Dict[str, Any]:
        """Load information about Endstone modules and their exports."""
        modules = {}
        
        # Core modules mapping
        core_modules = {
            "__init__.py": "endstone",
            "actor.py": "endstone.actor",
            "ban.py": "endstone.ban",
            "block.py": "endstone.block",
            "boss.py": "endstone.boss",
            "command.py": "endstone.command",
            "damage.py": "endstone.damage",
            "enchantments.py": "endstone.enchantments",
            "event.py": "endstone.event",
            "form.py": "endstone.form",
            "inventory.py": "endstone.inventory",
            "lang.py": "endstone.lang",
            "level.py": "endstone.level",
            "map.py": "endstone.map",
            "permissions.py": "endstone.permissions",
            "plugin.py": "endstone.plugin",
            "scheduler.py": "endstone.scheduler",
            "scoreboard.py": "endstone.scoreboard",
            "util.py": "endstone.util",
        }
        
        for file_name, module_name in core_modules.items():
            file_path = self.ENDSTONE_REF_PATH / file_name
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    exports = self._extract_exports(content)
                    modules[module_name] = {
                        "file_path": str(file_path),
                        "exports": exports,
                        "content": content
                    }
                except Exception as e:
                    logger.warning(f"Failed to load {file_name}: {e}")
        
        return modules
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract __all__ exports from module content."""
        exports = []
        lines = content.split('\n')
        in_all_block = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('__all__'):
                in_all_block = True
                # Handle single line __all__
                if '[' in line and ']' in line:
                    start = line.find('[')
                    end = line.find(']')
                    if start != -1 and end != -1:
                        items_str = line[start+1:end]
                        exports.extend(self._parse_list_items(items_str))
                        in_all_block = False
            elif in_all_block:
                if ']' in line:
                    # End of __all__ block
                    before_bracket = line[:line.find(']')]
                    exports.extend(self._parse_list_items(before_bracket))
                    in_all_block = False
                else:
                    exports.extend(self._parse_list_items(line))
        
        return exports
    
    def _parse_list_items(self, items_str: str) -> List[str]:
        """Parse items from a string containing list elements."""
        items = []
        for item in items_str.split(','):
            item = item.strip().strip('"').strip("'").strip()
            if item and not item.startswith('#'):
                items.append(item)
        return items
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_module_info",
                    description="Get information about an Endstone module including its exports and documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "Name of the Endstone module (e.g., 'endstone.event', 'endstone.plugin')"
                            }
                        },
                        "required": ["module_name"]
                    }
                ),
                Tool(
                    name="search_exports",
                    description="Search for specific classes, functions, or constants across Endstone modules",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search term (class name, function name, etc.)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_symbol_info",
                    description="Get detailed information about a specific class, function, or constant in Endstone",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol_name": {
                                "type": "string",
                                "description": "Name of the class, function, etc. (e.g., 'PlayerInteractEvent', 'Plugin')"
                            }
                        },
                        "required": ["symbol_name"]
                    }
                ),
                Tool(
                    name="generate_plugin_template",
                    description="Generate a basic Endstone plugin template with specified features",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plugin_name": {
                                "type": "string",
                                "description": "Name of the plugin, which must end with '_plugin' (e.g., 'example_plugin', 'economy_plugin') "
                            },
                            "features": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of features to include (e.g., 'commands', 'events', 'permissions')"
                            }
                        },
                        "required": ["plugin_name"]
                    }
                ),
                Tool(
                    name="get_event_info",
                    description="Get detailed information about Endstone events and event handling",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_type": {
                                "type": "string",
                                "description": "Specific event type to get info about (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="read_tutorials",
                    description="Read Endstone tutorials or list available tutorials",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Tutorial name to read or leave empty to list all tutorials"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_module_info":
                    result = await self._get_module_info(arguments.get("module_name"))
                    return result.content
                elif name == "search_exports":
                    result = await self._search_exports(arguments.get("query"))
                    return result.content
                elif name == "get_symbol_info":
                    result = await self._get_symbol_info(arguments.get("symbol_name"))
                    return result.content
                elif name == "generate_plugin_template":
                    result = await self._generate_plugin_template(
                        arguments.get("plugin_name"),
                        arguments.get("features", [])
                    )
                    return result.content
                elif name == "get_event_info":
                    result = await self._get_event_info(arguments.get("event_type"))
                    return result.content
                elif name == "read_tutorials":
                    result = await self._read_tutorials(arguments.get("query"))
                    return result.content
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts."""
            return []  # No prompts available
    
    async def _get_module_info(self, module_name: str) -> CallToolResult:
        """Get information about a specific module."""
        if not module_name:
            return CallToolResult(
                content=[TextContent(type="text", text="Module name is required")]
            )
        
        if module_name in self.endstone_modules:
            module_info = self.endstone_modules[module_name]
            exports = module_info["exports"]
            
            result = f"# {module_name}\n\n"
            result += f"**File:** {module_info['file_path']}\n\n"
            result += f"**Exports:** {len(exports)} items\n\n"
            
            if exports:
                result += "## Available Exports:\n"
                for export in exports:
                    result += f"- `{export}`\n"
            else:
                result += "No exports found in __all__\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
        else:
            available = ", ".join(self.endstone_modules.keys())
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=f"Module '{module_name}' not found. Available modules: {available}"
                )]
            )
    
    async def _search_exports(self, query: str) -> CallToolResult:
        """Search for exports across all modules."""
        if not query:
            return CallToolResult(
                content=[TextContent(type="text", text="Search query is required")]
            )
        
        results = []
        query_lower = query.lower()
        
        for module_name, module_info in self.endstone_modules.items():
            for export in module_info["exports"]:
                if query_lower in export.lower():
                    results.append(f"- `{export}` from `{module_name}`")
        
        if results:
            result_text = f"# Search Results for '{query}'\n\n" + "\n".join(results)
        else:
            result_text = f"No exports found matching '{query}'"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
    
    async def _generate_plugin_template(self, plugin_name: str, features: List[str]) -> CallToolResult:
        """Generate a plugin template."""
        if not plugin_name:
            return CallToolResult(
                content=[TextContent(type="text", text="Plugin name is required")]
            )
        
        template = self._create_plugin_template(plugin_name, features)
        
        return CallToolResult(
            content=[TextContent(type="text", text=template)]
        )
    
    async def _get_symbol_info(self, symbol_name: str) -> CallToolResult:
        """Get information about a specific symbol."""
        if not symbol_name:
            return CallToolResult(
                content=[TextContent(type="text", text="Symbol name is required")]
            )
        
        result_text = self._format_symbol_info(symbol_name)
        
        return CallToolResult(content=[TextContent(type="text", text=result_text)])

    def _format_symbol_info(self, symbol_name: str) -> str:
        """Formats the detailed information for a symbol into a markdown string."""
        # Find which module it belongs to
        module_name = None
        for mod, info in self.endstone_modules.items():
            if symbol_name in info["exports"]:
                module_name = mod
                break

        result = f"# {symbol_name}\n\n"
        if module_name:
            result += f"Found in module: `{module_name}`\n\n"
        
        if symbol_name not in self.pyi_definitions:
            result += "No detailed definition found for this symbol." if module_name else f"Symbol '{symbol_name}' not found in any loaded Endstone module's exports."
            return result

        class_info = self.pyi_definitions[symbol_name]
        if class_info.get('doc'):
            result += f"{class_info['doc']}\n\n"
        
        if class_info.get('properties'):
            result += "## Properties\n"
            for prop in class_info['properties']:
                prop_name = prop['name']
                prop_type = prop['return_type']
                prop_doc = prop.get('doc') or 'No description available.'
                
                result += f"- **`{prop_name}`**"
                if prop_type:
                    result += f" -> `{prop_type}`"
                result += f"\n  - {prop_doc}\n"
            result += "\n"
        
        if class_info.get('methods'):
            result += "## Methods\n"
            for method in class_info['methods']:
                method_name = method['name']
                # Skip if method name matches a property name (likely a setter/deleter)
                if any(prop['name'] == method_name for prop in class_info.get('properties', [])):
                    continue

                method_type = method['return_type']
                method_doc = method.get('doc') or 'No description available.'
                
                params = method.get('params', [])
                param_str = ', '.join([f"{p['name']}: {p['type']}" for p in params])

                result += f"- **`{method_name}({param_str})`**"
                if method_type:
                    result += f" -> `{method_type}`"
                result += f"\n  - {method_doc}\n"
            result += "\n"

        return result

    async def _get_event_info(self, event_type: Optional[str]) -> CallToolResult:
        """Get information about events."""
        if "endstone.event" in self.endstone_modules:
            events = self.endstone_modules["endstone.event"]["exports"]
            
            if event_type:
                if event_type in events:
                    result = self._format_symbol_info(event_type)
                    result += "## Usage Example:\n\n"
                    result += f"```python\nfrom endstone.event import {event_type}, event_handler\n\n"
                    result += "@event_handler\n"
                    result += f"def on_{event_type.lower().replace('event', '')}(self, event: {event_type}):\n"
                    result += "    # Handle the event\n"
                    result += "    pass\n```"
                else:
                    result = f"Event '{event_type}' not found. Available events: {', '.join([e for e in events if 'Event' in e])}"
            else:
                event_list = [e for e in events if 'Event' in e]
                result = f"# Available Events ({len(event_list)})\n\n"
                for event in event_list:
                    result += f"- `{event}`\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="Event module not found")]
            )

    async def _read_tutorials(self, query: Optional[str]) -> CallToolResult:
        """Read tutorial content or list available tutorials."""
        try:
            if not self.TUTORIALS_PATH.exists():
                return CallToolResult(
                    content=[TextContent(type="text", text="Tutorial directory does not exist")]
                )
            
            # Get all tutorial files
            tutorial_files = list(self.TUTORIALS_PATH.glob('*.md'))
        
        
            # List all available tutorials
            available_tutorials = "## Available Tutorials\n\n"
            for file_path in tutorial_files:
                file_name = file_path.name
                intro = ""
                
                # Read and extract the main title and introduction
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        first_paragraph = re.search(r'^#.*?\n\n(.*?)(\n\n|$)', content, re.DOTALL)
                        if first_paragraph:
                            intro = first_paragraph.group(1).replace('\n', ' ')
                except Exception as e:
                    intro = f"Failed to read introduction: {str(e)}"
                
                available_tutorials += f"{file_name}\n> {intro}\n\n"
            
            if not query:
                return CallToolResult(
                    content=[TextContent(type="text", text=available_tutorials)]
                )
        
            # 查找匹配的教程文件
            query_lower = query.lower()
            best_match = None
            best_score = 0
            
            for file_path in tutorial_files:
                file_name = file_path.name.lower()
                base_name = file_path.stem.lower()
                
                # 计算最佳匹配分数
                if query_lower == base_name:
                    score = 100  # 完全匹配文件名
                elif query_lower in base_name:
                    score = 75   # 部分匹配文件名
                elif query_lower in file_name:
                    score = 50   # 匹配扩展名
                else:
                    score = 0
                    
                if score > best_score:
                    best_score = score
                    best_match = file_path
            
            if best_match:
                try:
                    content = best_match.read_text(encoding='utf-8')
                    return CallToolResult(
                        content=[TextContent(type="text", text=content)]
                    )
                except Exception as e:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Failed to read tutorial file: {str(e)}")]
                    )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"not tutorial found: '{query}'. \n\n{available_tutorials}"
                    )]
                )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error reading tutorials: {str(e)}")]
            )
    
    def _create_plugin_template(self, plugin_name: str, features: List[str]) -> str:
        """Create a plugin template based on requested features."""
        # 1. Validate the plugin name. The convention is snake_case ending with _plugin.
        if not plugin_name or not plugin_name.endswith("_plugin"):
            return "Invalid input. 'plugin_name' must be in snake_case and end with '_plugin' (e.g., 'my_awesome_plugin')."

        # Ensure the name part is not empty
        if plugin_name == "_plugin":
            return "Invalid input. 'plugin_name' cannot be empty."

        snake_case_name = plugin_name[:-len("_plugin")]

        # 2. Derive other name formats from the snake_case name.
        # e.g., from 'my_awesome_plugin'
        
        # kebab-case for project name suffix and entry point: 'my-awesome-plugin'
        kebab_case_name = snake_case_name.replace('_', '-')

        # PascalCase for the main class name: 'MyAwesomePlugin'
        pascal_case_name = "".join(word.capitalize() for word in snake_case_name.split('_'))

        # 3. Construct names for the project structure and configuration.
        
        # Project name for pyproject.toml: 'endstone-my-awesome-plugin'
        project_name = f"endstone-{kebab_case_name}"
        
        # Entry point name for pyproject.toml: 'my-awesome-plugin'
        entry_point_name = kebab_case_name
        
        # Python package name: 'endstone_my_awesome_plugin'
        package_name = f"endstone_{snake_case_name}"
        
        # Main Python file name: 'my_awesome_plugin.py'
        main_py_filename = f"{snake_case_name}_plugin.py"
        
        # Main Python class name: 'MyAwesomePlugin'
        main_class_name = f"{pascal_case_name}Plugin"

        # pyproject.toml content
        pyproject_toml_content = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
dependencies = []
authors = [
    {{ name = "Endstone Developers", email = "hello@endstone.dev" }},
]
description = "A new Endstone plugin: {pascal_case_name}"
readme = "README.md"
license = {{ file = "LICENSE" }}
keywords = ["endstone", "plugin"]

[project.urls]
Homepage = "https://github.com/EndstoneMC/python-example-plugin"

[project.entry-points."endstone"]
{entry_point_name} = "{package_name}:{main_class_name}"
"""

        # __init__.py content
        init_py_content = f"""from .{snake_case_name}_plugin import {main_class_name}

__all__ = ["{main_class_name}"]
"""

        # plugin instance file content
        plugin_instance_py_content = """from endstone.plugin import Plugin

_plugin_instance: Plugin

def set_plugin_instance(instance: Plugin):
    \"\"\"setting global plugin instance\"\"\"
    global _plugin_instance
    _plugin_instance = instance

def get_plugin_instance() -> Plugin:
    \"\"\"getting global plugin instance\"\"\"
    return _plugin_instance
"""

        # event listener file content
        event_listener_py_content = f"""
### `src/{package_name}/event_listener.py`

use tool `read_tutorials("event-listener")` to get more information.

Note: This file is a Listener file, which only allows the `__init__` method and methods registered with the `@event_handler` annotation.
"""
        event_listener_py_content += """
from endstone import ColorFormat
from endstone.event import event_handler, EventPriority, PlayerJoinEvent, PlayerQuitEvent
from endstone.plugin import Plugin

class ExampleListener:
    def __init__(self, plugin: Plugin):
        self._plugin = plugin

    @event_handler(priority=EventPriority.NORMAL)
    def on_player_join(self, event: PlayerJoinEvent):
        player = event.player
        self._plugin.logger.info(
            ColorFormat.YELLOW + f"{player.name}[/{player.address}] joined the game with UUID {player.unique_id}"
        )

        # example of explicitly removing one's permission of using /me command
        player.add_attachment(self._plugin, "minecraft.command.me", False)
        player.update_commands()  # don't forget to resend the commands

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        player = event.player
        self._plugin.logger.info(ColorFormat.YELLOW + f"{player.name}[/{player.address}] left the game.")

"""

        # food command file content
        food_command_py_content = f"""
### `src/{package_name}/food_command.py`

use tool `read_tutorials("command")` to get more information.

Key points:
1. Subclass CommandExecutor and implement only on_command (do not use __init__; it won’t be called).
2. Call get_plugin_instance() to access the global plugin.
3. For temporary data, attach attributes to the plugin (e.g. plugin.temp = {{}}); for persistent data, use the plugin.config API.
4. muiltple commands example file: `food_command.py` -> `/food`, `example_command.py` -> `/example`

```python
from endstone.command import Command, CommandSender, CommandExecutor
from endstone import Player, ColorFormat
from endstone.inventory import ItemStack

from {package_name}.plugin_instance import get_plugin_instance

class FoodCommandExecutor(CommandExecutor):
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_error_message("此命令只能由玩家执行。")
            return False
        self.give_food(sender)
        return True
    
    def give_food(self, player: Player):
        plugin = get_plugin_instance()
        plugin.logger.info("give food to "+player.name)
        player.inventory.add_item(ItemStack('minecraft:apple', 1))
        player.send_message(ColorFormat.GREEN + "You received an apple!")
```
"""

        # main plugin file content
        main_plugin_py_content = f"from endstone.plugin import Plugin\n"
        main_plugin_py_content += f"from {package_name}.plugin_instance import set_plugin_instance\n"

        if "commands" in features:
            main_plugin_py_content += f"""from endstone.command import Command, CommandSender
from {package_name}.food_command import FoodCommandExecutor
"""

        if "events" in features:
            main_plugin_py_content += f"""from {package_name}.example_listener import ExampleListener
"""

        main_plugin_py_content += f"""
class {main_class_name}(Plugin):
    name = "{snake_case_name}"
    version = "0.1.0"
    api_version = "0.5"
    load = "POSTWORLD"
"""

        if "commands" in features:
            main_plugin_py_content += """
    commands = {
        "food": {
            "description": "Give a apple to yourself",
            "usages": ["/food"],
            "aliases": ["eattt"],
            "permissions": ["{snake_case_name}.command.food"]
        }
    }

    permissions = {
        "{snake_case_name}.command": {
            "description": "Allow users to use all commands provided by this plugin.",
            "default": True,
            "children": {
                "{snake_case_name}.command.food": True
            }
        },
        "{snake_case_name}.command.food": {
            "description": "Allow users to use the /food command.",
            "default": True  # values: "op" | True
        }
    }
""".replace("{snake_case_name}", snake_case_name)
        
        main_plugin_py_content += f"""
    def on_enable(self) -> None:
        \"\"\"Called when the plugin is enabled.\"\"\"
        self.logger.info(f"{{self.name}} v{{self.version}} has been enabled!")
        # setting global plugin instance
        set_plugin_instance(self)
"""

        if "commands" in features:
            main_plugin_py_content += '''
        # Register commands
        self.get_command("food").executor = FoodCommandExecutor()
'''

        if "events" in features:
            main_plugin_py_content += '''
        # Register event listeners
        self.register_events(ExampleListener(self))
'''
        

        main_plugin_py_content += '''

    def on_disable(self) -> None:
        \"\"\"Called when the plugin is disabled.\"\"\"
        self.logger.info(f"{{self.name}} has been disabled!")
'''

        # Assemble the final markdown output
        markdown_output = f"""# Plugin Template for '{pascal_case_name}'

Based on your request, here is a complete guide to create the '{pascal_case_name}' plugin project, following Endstone's conventions.

## 1. Project Structure

Your project should have the following file structure. The project name `{project_name}` uses dashes, while the Python package name `{package_name}` uses underscores.

creating these files, use MIT LICENSE.

```
src/{package_name}/{main_py_filename}
src/{package_name}/plugin_instance.py
src/{package_name}/__init__.py{"\nsrc/"+package_name+"/event_listener.py" if "events" in features else ""}{"\nsrc/"+package_name+"/python_command.py" if "commands" in features else ""}
pyproject.toml
README.md
LICENSE
```

## 2. File Contents

Here are the contents for each file. Create these files with the content below.

### `pyproject.toml`

This file configures your project, its dependencies, and the entry point for Endstone to discover your plugin.

```toml
{pyproject_toml_content}
```

### `src/{package_name}/__init__.py`

This file makes your plugin class available when the package is imported and defines the public API of the package.

```python
{init_py_content}
```

### `src/{package_name}/{main_py_filename}`

This is the core of your plugin, containing the main `Plugin` class and its logic.

```python
{main_plugin_py_content}
```

### `src/{package_name}/plugin_instance.py`

This file is used to set and get the global plugin instance.
```python
{plugin_instance_py_content}
```
{event_listener_py_content if "events" in features else ""}{food_command_py_content if "commands" in features else ""}
"""

        return markdown_output
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="endstone-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    """Main entry point."""
    server = EndstoneMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 