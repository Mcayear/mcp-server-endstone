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

# Endstone reference path
ENDSTONE_REF_PATH = Path(__file__).parent / "./reference/endstone"

class EndstoneMCPServer:
    def __init__(self):
        self.server = Server("endstone-mcp")
        self.endstone_modules = self._load_endstone_modules()
        self._setup_handlers()
    
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
            file_path = ENDSTONE_REF_PATH / file_name
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
                    name="generate_plugin_template",
                    description="Generate a basic Endstone plugin template with specified features",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plugin_name": {
                                "type": "string",
                                "description": "Name of the plugin"
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
                elif name == "generate_plugin_template":
                    result = await self._generate_plugin_template(
                        arguments.get("plugin_name"),
                        arguments.get("features", [])
                    )
                    return result.content
                elif name == "get_event_info":
                    result = await self._get_event_info(arguments.get("event_type"))
                    return result.content
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts."""
            return [
                Prompt(
                    name="plugin_development",
                    description="Get guidance on developing Endstone plugins"
                ),
                Prompt(
                    name="event_handling",
                    description="Learn about event handling in Endstone"
                ),
                Prompt(
                    name="command_creation",
                    description="Guide for creating custom commands"
                )
            ]
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict) -> GetPromptResult:
            """Handle prompt requests."""
            if name == "plugin_development":
                content = self._get_plugin_development_guide()
            elif name == "event_handling":
                content = self._get_event_handling_guide()
            elif name == "command_creation":
                content = self._get_command_creation_guide()
            else:
                content = f"Unknown prompt: {name}"
            
            return GetPromptResult(
                description=f"Endstone {name} guide",
                messages=[
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": content
                        }
                    }
                ]
            )
    
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
    
    async def _get_event_info(self, event_type: Optional[str]) -> CallToolResult:
        """Get information about events."""
        if "endstone.event" in self.endstone_modules:
            events = self.endstone_modules["endstone.event"]["exports"]
            
            if event_type:
                if event_type in events:
                    result = f"# {event_type}\n\nThis event is available in endstone.event module.\n\n"
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
    
    def _create_plugin_template(self, plugin_name: str, features: List[str]) -> str:
        """Create a plugin template based on requested features."""
        template = f'''from endstone.plugin import Plugin
from endstone import Logger

class {plugin_name}Plugin(Plugin):
    
    def __init__(self):
        super().__init__()
        self.logger: Logger = self.get_logger()
    
    def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        self.logger.info(f"{{self.name}} v{{self.version}} has been enabled!")
'''
        
        if "events" in features:
            template += '''
        # Register event handlers
        self.register_events()
    
    def register_events(self):
        """Register event handlers."""
        from endstone.event import event_handler, PlayerJoinEvent
        
        @event_handler
        def on_player_join(self, event: PlayerJoinEvent):
            player = event.player
            self.logger.info(f"Player {{player.name}} joined the server!")
'''
        
        if "commands" in features:
            template += '''
        # Register commands
        self.register_commands()
    
    def register_commands(self):
        """Register custom commands."""
        from endstone.command import Command, CommandExecutor
        
        # Example command implementation
        pass
'''
        
        template += '''
    
    def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        self.logger.info(f"{{self.name}} has been disabled!")
'''
        
        return template
    
    def _get_plugin_development_guide(self) -> str:
        """Get plugin development guide."""
        return """
# Endstone Plugin Development Guide

## Basic Plugin Structure

1. **Inherit from Plugin class**
   ```python
   from endstone.plugin import Plugin
   
   class MyPlugin(Plugin):
       pass
   ```

2. **Implement lifecycle methods**
   - `on_enable()`: Called when plugin is enabled
   - `on_disable()`: Called when plugin is disabled

3. **Plugin metadata**
   - Set class attributes: name, version, api_version
   - Or use plugin.toml configuration file

## Key Components

- **Events**: Handle server events (player join, block break, etc.)
- **Commands**: Create custom commands
- **Permissions**: Manage player permissions
- **Scheduler**: Schedule tasks
- **Configuration**: Store plugin settings
"""
    
    def _get_event_handling_guide(self) -> str:
        """Get event handling guide."""
        return """
# Event Handling in Endstone

## Basic Event Handler

```python
from endstone.event import event_handler, PlayerJoinEvent

@event_handler
def on_player_join(self, event: PlayerJoinEvent):
    player = event.player
    self.logger.info(f"Welcome {player.name}!")
```

## Event Priorities

- `EventPriority.LOWEST`
- `EventPriority.LOW`
- `EventPriority.NORMAL` (default)
- `EventPriority.HIGH`
- `EventPriority.HIGHEST`

## Cancellable Events

Some events can be cancelled:

```python
@event_handler
def on_block_break(self, event: BlockBreakEvent):
    if some_condition:
        event.cancelled = True
```
"""
    
    def _get_command_creation_guide(self) -> str:
        """Get command creation guide."""
        return """
# Creating Commands in Endstone

## Basic Command

```python
from endstone.command import Command, CommandExecutor

class MyCommandExecutor(CommandExecutor):
    def on_command(self, sender, command, args):
        sender.send_message("Hello from custom command!")
        return True

# Register the command
command = Command("mycommand")
command.executor = MyCommandExecutor()
self.server.command_map.register(command)
```

## Command with Arguments

```python
def on_command(self, sender, command, args):
    if len(args) == 0:
        sender.send_message("Usage: /mycommand <argument>")
        return False
    
    arg = args[0]
    sender.send_message(f"You said: {arg}")
    return True
```
"""
    
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

def main():
    """Main entry point."""
    server = EndstoneMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()