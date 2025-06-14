#!/usr/bin/env python3
"""
命令行工具入口点
"""

import asyncio
import argparse
import sys
from pathlib import Path

from .server import EndstoneMCPServer

def main():
    """主入口点函数"""
    parser = argparse.ArgumentParser(description="Endstone MCP 服务器")
    parser.add_argument(
        "--reference", 
        type=str, 
        help="Endstone 引用文件的路径",
        default=None
    )
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建并运行服务器
    server = EndstoneMCPServer(reference_path=args.reference)
    asyncio.run(server.run())

if __name__ == "__main__":
    sys.exit(main()) 