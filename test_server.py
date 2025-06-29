#!/usr/bin/env python3
"""
Test script for FastMail MCP Server

This script demonstrates how to test the FastMail MCP server locally.
Make sure to set your FASTMAIL_API_TOKEN environment variable first.
"""

import asyncio
import json
import os
import subprocess
import sys
from typing import Any, Dict

async def test_mcp_tool(tool_name: str, arguments: Dict[str, Any]):
    """Test a single MCP tool by running the server and sending a command."""
    
    # Create the MCP request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    # Run the server process
    server_path = os.path.join(os.path.dirname(__file__), "..", "fastmail_mcp_server.py")
    
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send the request
    request_json = json.dumps(request) + "\n"
    stdout, stderr = process.communicate(input=request_json)
    
    print(f"🔧 Testing tool: {tool_name}")
    print(f"📤 Request: {arguments}")
    
    if stderr:
        print(f"❌ Error: {stderr}")
    
    if stdout:
        try:
            response = json.loads(stdout.strip())
            print(f"✅ Response: {json.dumps(response, indent=2)}")
        except json.JSONDecodeError:
            print(f"📄 Raw output: {stdout}")
    
    print("-" * 50)

async def main():
    """Run tests for the FastMail MCP server."""
    
    api_token = os.getenv("FASTMAIL_API_TOKEN")
    if not api_token:
        print("❌ Please set FASTMAIL_API_TOKEN environment variable")
        print("💡 Get your token from: FastMail Settings → Privacy & Security → Integrations")
        return
    
    print("🚀 Testing FastMail MCP Server\n")
    
    # Test 1: Configure FastMail
    await test_mcp_tool("configure_fastmail", {
        "apiToken": api_token
    })
    
    # Test 2: List mailboxes
    await test_mcp_tool("list_mailboxes", {})
    
    # Test 3: Find inbox
    await test_mcp_tool("find_mailbox", {
        "role": "inbox"
    })
    
    # Test 4: Get recent emails from inbox
    await test_mcp_tool("get_emails", {
        "mailboxName": "Inbox",
        "limit": 5
    })
    
    # Test 5: Search for emails
    await test_mcp_tool("search_emails", {
        "keyword": "fastmail",
        "limit": 3
    })
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
