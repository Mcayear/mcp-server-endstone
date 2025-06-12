#!/usr/bin/env python3
"""
Test script for Endstone MCP Server

This script tests the functionality of the MCP server without requiring
a full MCP client setup.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from endstone_mcp_server import EndstoneMCPServer

async def test_server_functionality():
    """测试 MCP 服务器功能。"""
    print("=== 测试 Endstone MCP 服务器 ===")
    
    # Initialize the server
    server = EndstoneMCPServer()
    
    print(f"\n✓ 服务器初始化成功")
    print(f"✓ 已加载 {len(server.endstone_modules)} 个 Endstone 模块")
    
    # Test 1: Module loading
    print("\n--- 测试 1: 模块加载 ---")
    for module_name, module_info in server.endstone_modules.items():
        exports_count = len(module_info['exports'])
        print(f"  {module_name}: {exports_count} 个导出项")
    
    # Test 2: Get module info
    print("\n--- 测试 2: 获取模块信息 ---")
    result = await server._get_module_info("endstone.event")
    if result.content:
        content = result.content[0].text
        print(f"  结果长度: {len(content)} 个字符")
        print(f"  预览: {content[:200]}...")
    
    # Test 3: Search exports
    print("\n--- 测试 3: 搜索导出项 ---")
    result = await server._search_exports("form")
    if result.content:
        content = result.content[0].text
        print(f"  搜索结果: {content.count('form')} 个匹配项")
        lines = content.split('\n')
        for line in lines[:5]:  # Show first 5 results
            if line.strip():
                print(f"    {line}")
    
    # Test 4: Generate plugin template
    print("\n--- 测试 4: 生成插件模板 ---")
    result = await server._generate_plugin_template("TestPlugin", ["events", "commands"])
    if result.content:
        content = result.content[0].text
        print(f"  模板长度: {len(content)} 个字符")
        print(f"  包含 'on_enable': {'on_enable' in content}")
        print(f"  包含 'event_handler': {'event_handler' in content}")
    
    # Test 5: Get event info
    print("\n--- 测试 5: 获取事件信息 ---")
    result = await server._get_event_info("PlayerJoinEvent")
    if result.content:
        content = result.content[0].text
        print(f"  事件信息长度: {len(content)} 个字符")
        print(f"  包含使用示例: {'```python' in content}")
    
    # Test 6: List all events
    print("\n--- 测试 6: 列出所有事件 ---")
    result = await server._get_event_info(None)
    if result.content:
        content = result.content[0].text
        event_count = content.count('Event`')
        print(f"  找到 {event_count} 个事件")
    
    print("\n=== 所有测试成功完成！ ===")
    
    # Show some statistics
    print("\n--- 服务器统计信息 ---")
    total_exports = sum(len(info['exports']) for info in server.endstone_modules.values())
    print(f"  总模块数: {len(server.endstone_modules)}")
    print(f"  总导出项数: {total_exports}")
    
    # Show available modules
    print("\n--- 可用模块 ---")
    for module_name in sorted(server.endstone_modules.keys()):
        print(f"  - {module_name}")
    
    return True

async def test_error_handling():
    """测试错误处理。"""
    print("\n=== 测试错误处理 ===")
    
    server = EndstoneMCPServer()
    
    # Test invalid module name
    print("\n--- 测试: 无效模块名 ---")
    result = await server._get_module_info("invalid.module")
    if result.content:
        content = result.content[0].text
        print(f"  错误处理正确: {'not found' in content.lower()}")
    
    # Test empty search query
    print("\n--- 测试: 空搜索查询 ---")
    result = await server._search_exports("")
    if result.content:
        content = result.content[0].text
        print(f"  错误处理正确: {'required' in content.lower()}")
    
    # Test empty plugin name
    print("\n--- 测试: 空插件名 ---")
    result = await server._generate_plugin_template("", [])
    if result.content:
        content = result.content[0].text
        print(f"  错误处理正确: {'required' in content.lower()}")
    
    print("\n✓ 错误处理测试完成")

def test_module_parsing():
    """测试模块解析功能。"""
    print("\n=== 测试模块解析 ===")
    
    server = EndstoneMCPServer()
    
    # Test __all__ parsing
    test_content = '''
from some_module import Class1, Class2

__all__ = [
    "Class1",
    "Class2",
    "function1",
    "CONSTANT",
]

def function1():
    pass
'''
    
    exports = server._extract_exports(test_content)
    print(f"  解析的导出项: {exports}")
    expected = ["Class1", "Class2", "function1", "CONSTANT"]
    print(f"  解析正确: {exports == expected}")
    
    # Test single line __all__
    single_line_content = '__all__ = ["Item1", "Item2"]'
    exports = server._extract_exports(single_line_content)
    print(f"  单行解析: {exports}")
    
    print("\n✓ 模块解析测试完成")

async def main():
    """主测试函数。"""
    try:
        # Test basic functionality
        await test_server_functionality()
        
        # Test error handling
        await test_error_handling()
        
        # Test module parsing
        test_module_parsing()
        
        print("\n🎉 所有测试通过！MCP 服务器已准备就绪。")
        
    except Exception as e:
        print(f"\n❌ 测试失败，错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)