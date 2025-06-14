<p align="right">
<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="30" height="24">
</p>

# Endstone MCP Server

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/version-0.1.4-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-%3E=3.8-blue?logo=python" alt="Python version">
</p>

A Model Context Protocol (MCP) server designed to support EndstoneMC development.

<p align="center">
<a href="README_CN.md">
<img src="https://flagicons.lipis.dev/flags/4x3/cn.svg" width="30" height="24">
</a>
</p>

## Features

- **Module Information Query**: Retrieve detailed information and exports for Endstone modules.
- **Code Search**: Search for classes, functions, and constants across all Endstone modules.
- **Plugin Template Generation**: Generate basic plugin templates based on specified requirements.
- **Event Handling Guidance**: Provide detailed information and examples for event handling.
- **Development Tutorials**: Built-in guides for plugin development, event handling, and command creation.

## Installation or Startup

### Using uvx

```bash
uvx mcp-server-endstone
```

### From Source

```bash
git clone https://github.com/Mcayear/mcp-server-endstone
cd mcp-server-endstone
pip install -e .

# Start after installation
mcp-server-endstone
```

### Unit Tests
```bash
python -m tests.test_server
```

## Usage

### Start the Server Directly

```bash
mcp-server-endstone [--reference <path_to_reference_files>]
```

### Integrate with an MCP Client

Add the following to your MCP client configuration:

> Example (compatible with clients like cursor, trae):

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

## Available Tools

### 1. get_module_info
Get information about a specific Endstone module.

**Parameters:**
- `module_name`: The name of the module (e.g., 'endstone.event', 'endstone.plugin').

**Example:**
```
Tool: get_module_info
Parameters: {"module_name": "endstone.event"}
```

### 2. search_exports
Search for specific exports across all modules.

**Parameters:**
- `query`: The search term (class name, function name, etc.).

**Example:**
```
Tool: search_exports
Parameters: {"query": "Player"}
```

### 3. get_symbol_info
Get the detailed definition of a specific symbol (like a class or event) in Endstone, including its documentation, attributes, and methods.

**Parameters:**
- `symbol_name`: The name of the symbol (e.g., 'PlayerInteractEvent', 'Plugin').

**Example:**
```
Tool: get_symbol_info
Parameters: {"symbol_name": "PlayerInteractEvent"}
```

### 4. generate_plugin_template
Generate a basic plugin template with specified features.

**Parameters:**
- `plugin_name`: The name of the plugin (must end with '_plugin').
- `features`: A list of features to include (optional: 'commands', 'events', 'permissions').

**Example:**
```
Tool: generate_plugin_template
Parameters: {
  "plugin_name": "example_plugin",
  "features": ["events", "commands"]
}
```

### 5. get_event_info
Get information about events. If `event_type` is provided, it returns the detailed definition (attributes, docs) and usage examples for that event. Otherwise, it lists all available events.

**Parameters:**
- `event_type`: A specific event type (optional).

**Example:**
```
Tool: get_event_info
Parameters: {"event_type": "PlayerJoinEvent"}
```

### 6. read_tutorials
Get content for a tutorial. If no tutorial name is specified, it lists all available tutorials.

**Parameters:**
- `query`: The name of the tutorial (optional).

**Example:**
```
Tool: read_tutorials
Parameters: {"query": "register-commands"}
```

## Supported Endstone Modules

- `endstone` - Core module
- `endstone.actor` - Actor-related
- `endstone.ban` - Ban system
- `endstone.block` - Block operations
- `endstone.boss` - Boss bar
- `endstone.command` - Command system
- `endstone.damage` - Damage system
- `endstone.enchantments` - Enchantments
- `endstone.event` - Event system
- `endstone.form` - Form UI
- `endstone.inventory` - Inventory
- `endstone.lang` - Language localization
- `endstone.level` - World/Dimension
- `endstone.map` - Map
- `endstone.permissions` - Permission system
- `endstone.plugin` - Plugin basics
- `endstone.scheduler` - Task scheduler
- `endstone.scoreboard` - Scoreboard
- `endstone.util` - Utilities

## Development Examples

### Basic Plugin Structure

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

### Event Handling

```python
from endstone.event import event_handler, PlayerJoinEvent

@event_handler
def on_player_join(self, event: PlayerJoinEvent):
    player = event.player
    self.logger.info(f"Welcome {player.name}!")
    player.send_message("Welcome to the server!")
```

## Project Structure

```
mcp-server-endstone/
├── reference/         # Required reference resources
│   ├── endstone/
│   └── tutorials/
├── src/
│   └── mcp_server_endstone/
│       ├── __init__.py
│       ├── server.py  # Core server logic
│       ├── cli.py     # Command-line entry point
│       └── reference/ # Reference files
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── pyproject.toml
└── README.md
```

## Troubleshooting

1.  **Reference File Path Issues**: The server first attempts to load reference files from the `reference` directory within the package, then from the current working directory. If neither exists, some features may be unavailable. Use the `--reference` argument to specify the path.

2.  **Debugging Errors**: The server's log level is set to INFO. Check the logs to diagnose problems.

3.  **Dependency Issues**: Ensure all dependencies are correctly installed: `mcp>=0.1.0`

## Contributing

Contributions are welcome! Please feel free to submit Issues and Pull Requests to improve this MCP server.

## Credits

[EndstoneMC](https://github.com/EndstoneMC/endstone) - The `reference` content is based on `endstone/docs/reference` and `endstone/docs/tutorials`.

## License

MIT License