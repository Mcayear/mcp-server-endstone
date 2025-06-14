#!/usr/bin/env python3
"""
Test script for Endstone MCP Server.

This script tests the functionality of the MCP server without requiring
a full MCP client setup. It is organized into a TestRunner class
for better structure and state management.
"""

import asyncio
import sys
import traceback
from pathlib import Path

# 添加包导入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_server_endstone.server import EndstoneMCPServer

class TestRunner:
    """
    A test runner to organize and execute tests for the EndstoneMCPServer.
    """

    def __init__(self):
        """Initializes the test runner and the server instance."""
        self._print_header("初始化 Endstone MCP 服务器")
        self.server = EndstoneMCPServer()
        self._print_initial_stats()

    def _print_header(self, title: str):
        """Prints a formatted header for a test section."""
        print(f"\n{'=' * 10} {title} {'=' * 10}")

    def _print_initial_stats(self):
        """Prints the initial statistics of the loaded server."""
        print(f"✓ 服务器初始化成功")
        print(f"✓ 已加载 {len(self.server.endstone_modules)} 个 Endstone 模块")
        if hasattr(self.server, 'pyi_definitions'):
            print(f"✓ 已从 PYI 文件加载 {len(self.server.pyi_definitions)} 个类定义")

    async def run_all(self) -> bool:
        """
        Runs all test suites sequentially.

        Returns:
            True if all tests pass, False otherwise.
        """
        try:
            # --- Functional Tests ---
            await self.test_core_features()
            await self.test_documentation_features()
            await self.test_generation_features()

            # --- Edge Case and Error Handling Tests ---
            await self.test_error_handling()

            # --- Internal Utility Tests ---
            self.test_internal_utils()

            # --- Final Summary ---
            self.print_summary()

            print("\n🎉 所有测试通过！MCP 服务器已准备就绪。")
            return True
        except Exception as e:
            print(f"\n❌ 测试执行过程中发生意外错误: {e}")
            traceback.print_exc()
            return False

    async def test_core_features(self):
        """Tests core functionalities like module info, search, and symbol lookup."""
        self._print_header("测试核心查询功能 (模块、符号、搜索)")

        # Test 1: Get module info
        print("\n--- 测试: 获取模块信息 (endstone.event) ---")
        result = await self.server._get_module_info("endstone.event")
        assert result.content, "获取模块信息失败"
        content = result.content[0].text
        print(f"  结果长度: {len(content)} 字符")
        print(f"  预览: {content[:200]}...")
        assert "Event" in content

        # Test 2: Search exports
        print("\n--- 测试: 搜索导出项 (form) ---")
        result = await self.server._search_exports("form")
        assert result.content, "搜索导出项失败"
        content = result.content[0].text
        print(f"  搜索结果: {content.count('form')} 个匹配项")
        for line in content.split('\n')[:5]:
            if line.strip():
                print(f"    {line}")
        assert "ActionForm" in content

        # Test 3: Get symbol info
        print("\n--- 测试: 获取符号信息 (ActionForm) ---")
        result = await self.server._get_symbol_info("ActionForm")
        assert result.content, "获取符号信息失败"
        content = result.content[0].text
        print(f"  内容文本:\n{content}")
        assert "# ActionForm" in content

    async def test_documentation_features(self):
        """Tests documentation-related features like tutorials and event info."""
        self._print_header("测试文档功能 (教程、事件)")

        # Test 1: List all tutorials
        print("\n--- 测试: 列出所有教程 ---")
        result = await self.server._read_tutorials(None)
        assert result.content, "列出教程失败"
        content = result.content[0].text
        print(f"  教程列表:\n{content}")
        assert "## Available Tutorials" in content

        # Test 2: Read a specific tutorial
        print("\n--- 测试: 读取特定教程 (register-commands) ---")
        result = await self.server._read_tutorials("register-commands")
        assert result.content, "读取特定教程失败"
        content = result.content[0].text
        print(f"  教程长度: {len(content)} 字符")
        print(f"  预览: {content[:200]}...")

        # Test 3: List all events
        print("\n--- 测试: 列出所有事件 ---")
        result = await self.server._get_event_info(None)
        assert result.content, "列出事件失败"
        content = result.content[0].text
        event_count = content.count('Event`')
        print(f"  找到 {event_count} 个事件")
        if "endstone.event" in self.server.endstone_modules:
            assert event_count > 0  # Sanity check

        # Test 4: Get info for a specific event
        print("\n--- 测试: 获取特定事件信息 (PlayerInteractEvent) ---")
        result = await self.server._get_event_info("PlayerInteractEvent")
        assert result.content, "获取特定事件信息失败"
        content = result.content[0].text
        print(f"  事件信息长度: {len(content)} 字符")

    async def test_generation_features(self):
        """Tests code generation features."""
        self._print_header("测试代码生成功能")

        # Test 1: Generate plugin template
        print("\n--- 测试: 生成插件模板 ---")
        result = await self.server._generate_plugin_template("test_plugin", ["events", "commands"])
        assert result.content, "生成插件模板失败"
        content = result.content[0].text
        print(f"  模板长度: {len(content)} 字符")
        print(f"  包含 'on_enable': {'on_enable' in content}")
        print(f"  包含 'event_handler': {'event_handler' in content}")
        assert "on_enable" in content and "event_handler" in content

    async def test_error_handling(self):
        """Tests edge cases and error handling for invalid inputs."""
        self._print_header("测试错误处理和边界情况")

        # Test 1: Invalid module name
        print("\n--- 测试: 无效模块名 ---")
        result = await self.server._get_module_info("invalid.module")
        content = result.content[0].text
        print(f"  响应: {content}")
        assert "not found" in content.lower()

        # Test 2: Invalid symbol name
        print("\n--- 测试: 无效符号名 ---")
        result = await self.server._get_symbol_info("InvalidSymbol")
        content = result.content[0].text
        print(f"  响应: {content}")
        assert "not found" in content.lower()

        # Test 3: Empty search query
        print("\n--- 测试: 空搜索查询 ---")
        result = await self.server._search_exports("")
        content = result.content[0].text
        print(f"  响应: {content}")
        assert "required" in content.lower()

        # Test 4: Empty plugin name
        print("\n--- 测试: 空插件名 ---")
        result = await self.server._generate_plugin_template("", [])
        content = result.content[0].text
        print(f"  响应: {content}")
        assert "required" in content.lower()

        # Test 5: Non-existent tutorial
        print("\n--- 测试: 不存在的教程 ---")
        result = await self.server._read_tutorials("non-existent-tutorial")
        content = result.content[0].text
        assert "Available Tutorials" in content

    def test_internal_utils(self):
        """Tests internal synchronous utility functions like __all__ parsing."""
        self._print_header("测试内部工具函数 (模块解析)")

        # Test __all__ parsing
        test_content = '''
from some_module import Class1, Class2
__all__ = [
    "Class1", "Class2",
    "function1", "CONSTANT",
]
def function1(): pass
'''
        exports = self.server._extract_exports(test_content)
        expected = ["Class1", "Class2", "function1", "CONSTANT"]
        print(f"  解析的导出项: {exports}")
        print(f"  期望的导出项: {expected}")
        assert exports == expected, "多行 __all__ 解析失败"

        # Test single line __all__
        single_line_content = '__all__= ["Item1", "Item2"]'
        exports = self.server._extract_exports(single_line_content)
        expected_single = ["Item1", "Item2"]
        print(f"  单行解析结果: {exports}")
        assert exports == expected_single, "单行 __all__ 解析失败"
        print("✓ 模块解析测试完成")

    def print_summary(self):
        """Prints a final summary of server statistics."""
        self._print_header("服务器最终统计信息")
        total_exports = sum(len(info['exports']) for info in self.server.endstone_modules.values())
        print(f"  总模块数: {len(self.server.endstone_modules)}")
        print(f"  总导出项数: {total_exports}")
        if hasattr(self.server, 'pyi_definitions'):
            print(f"  总 PYI 定义数: {len(self.server.pyi_definitions)}")

        print("\n--- 可用模块 ---")
        for module_name in sorted(self.server.endstone_modules.keys()):
            print(f"  - {module_name}")

async def main():
    """Main entry point for the test script."""
    runner = TestRunner()
    return await runner.run_all()

if __name__ == "__main__":
    # The `assert` statements will raise an AssertionError on failure,
    # which will be caught in `run_all`, causing the script to exit with 1.
    # A successful run will exit with 0.
    is_success = asyncio.run(main())
    sys.exit(0 if is_success else 1) 