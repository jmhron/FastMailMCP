#!/usr/bin/env python3

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Union
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# FastMail JMAP API configuration
FASTMAIL_API_URL = "https://api.fastmail.com/jmap/api/"
FASTMAIL_SESSION_URL = "https://api.fastmail.com/jmap/session"

class FastMailMCPServer:
    def __init__(self):
        self.server = Server("fastmail-mcp-server")
        self.api_token: Optional[str] = None
        self.account_id: Optional[str] = None
        self.session_data: Optional[Dict[str, Any]] = None
        
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="configure_fastmail",
                    description="Configure FastMail API credentials",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "apiToken": {
                                "type": "string",
                                "description": "FastMail API token from Settings > Privacy & Security > Integrations"
                            },
                            "accountId": {
                                "type": "string", 
                                "description": "Optional: FastMail account ID (will be auto-detected if not provided)"
                            }
                        },
                        "required": ["apiToken"]
                    }
                ),
                types.Tool(
                    name="list_mailboxes",
                    description="List all mailboxes/folders in the FastMail account with names, roles, and counts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "description": "Filter by mailbox role: inbox, drafts, sent, trash, archive, junk"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="find_mailbox",
                    description="Find a specific mailbox by name or role",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the mailbox to find (supports partial matching)"
                            },
                            "role": {
                                "type": "string", 
                                "description": "Mailbox role: inbox, drafts, sent, trash, archive, junk"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_emails",
                    description="Get emails from a specific mailbox or folder",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mailboxId": {
                                "type": "string",
                                "description": "ID of the mailbox (use find_mailbox or list_mailboxes to get ID)"
                            },
                            "mailboxName": {
                                "type": "string",
                                "description": "Name of the mailbox (alternative to mailboxId)"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of emails to retrieve",
                                "default": 20
                            },
                            "includeBody": {
                                "type": "boolean",
                                "description": "Include email body content",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="search_emails",
                    description="Search emails by keyword, sender, subject, or other criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "Text to search for in email content, subject, from/to fields"
                            },
                            "from_email": {
                                "type": "string",
                                "description": "Search emails from specific sender"
                            },
                            "to_email": {
                                "type": "string", 
                                "description": "Search emails sent to specific recipient"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Search emails by subject"
                            },
                            "mailboxId": {
                                "type": "string",
                                "description": "Limit search to specific mailbox"
                            },
                            "hasAttachment": {
                                "type": "boolean",
                                "description": "Filter emails with/without attachments"
                            },
                            "before": {
                                "type": "string",
                                "description": "Find emails before this date (YYYY-MM-DD format)"
                            },
                            "after": {
                                "type": "string",
                                "description": "Find emails after this date (YYYY-MM-DD format)"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results",
                                "default": 20
                            },
                            "includeBody": {
                                "type": "boolean", 
                                "description": "Include email body content",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_email_body",
                    description="Get the full body content of a specific email",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "emailId": {
                                "type": "string",
                                "description": "ID of the email to retrieve body for"
                            },
                            "format": {
                                "type": "string",
                                "description": "Body format: text, html, or both",
                                "default": "text"
                            }
                        },
                        "required": ["emailId"]
                    }
                ),
                types.Tool(
                    name="send_email",
                    description="Send an email through FastMail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Recipient email addresses"
                            },
                            "cc": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "CC email addresses"
                            },
                            "bcc": {
                                "type": "array",
                                "items": {"type": "string"}, 
                                "description": "BCC email addresses"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content"
                            },
                            "isHtml": {
                                "type": "boolean",
                                "description": "Whether the body is HTML format",
                                "default": False
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "configure_fastmail":
                    return await self.configure_fastmail(arguments)
                elif name == "list_mailboxes":
                    return await self.list_mailboxes(arguments)
                elif name == "find_mailbox":
                    return await self.find_mailbox(arguments)
                elif name == "get_emails":
                    return await self.get_emails(arguments)
                elif name == "search_emails":
                    return await self.search_emails(arguments)
                elif name == "get_email_body":
                    return await self.get_email_body(arguments)
                elif name == "send_email":
                    return await self.send_email(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def configure_fastmail(self, args: Dict[str, Any]) -> List[types.TextContent]:
        self.api_token = args["apiToken"]
        
        # Get session info and account ID
        async with httpx.AsyncClient() as client:
            response = await client.get(
                FASTMAIL_SESSION_URL,
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to authenticate: {response.text}")
                
            self.session_data = response.json()
            
            # Use provided account ID or get primary account
            if args.get("accountId"):
                self.account_id = args["accountId"]
            else:
                self.account_id = self.session_data["primaryAccounts"]["urn:ietf:params:jmap:mail"]
        
        return [types.TextContent(
            type="text", 
            text=f"✅ FastMail configured successfully!\nAccount ID: {self.account_id}\nUsername: {self.session_data.get('username', 'N/A')}"
        )]

    async def make_jmap_request(self, method_calls: List[List[Any]]) -> Dict[str, Any]:
        if not self.api_token or not self.account_id:
            raise Exception("FastMail not configured. Use configure_fastmail first.")
        
        request_data = {
            "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
            "methodCalls": method_calls
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FASTMAIL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            if response.status_code != 200:
                raise Exception(f"JMAP API error: {response.text}")
            
            return response.json()

    async def list_mailboxes(self, args: Dict[str, Any]) -> List[types.TextContent]:
        method_calls = [["Mailbox/get", {"accountId": self.account_id}, "a"]]
        result = await self.make_jmap_request(method_calls)
        
        mailboxes = result["methodResponses"][0][1]["list"]
        
        # Filter by role if specified
        if role_filter := args.get("role"):
            mailboxes = [mb for mb in mailboxes if mb.get("role") == role_filter]
        
        # Format output nicely
        output_lines = ["📁 **FastMail Mailboxes**\n"]
        for mb in mailboxes:
            role = mb.get("role", "folder")
            name = mb["name"]
            total_emails = mb.get("totalEmails", 0)
            unread_emails = mb.get("unreadEmails", 0)
            
            emoji = {
                "inbox": "📥",
                "drafts": "📝", 
                "sent": "📤",
                "trash": "🗑️",
                "archive": "📦",
                "junk": "🚫"
            }.get(role, "📁")
            
            output_lines.append(f"{emoji} **{name}** ({role})")
            output_lines.append(f"   ID: `{mb['id']}`")
            output_lines.append(f"   Emails: {total_emails} total, {unread_emails} unread\n")
        
        return [types.TextContent(type="text", text="\n".join(output_lines))]

    async def find_mailbox(self, args: Dict[str, Any]) -> List[types.TextContent]:
        method_calls = [["Mailbox/get", {"accountId": self.account_id}, "a"]]
        result = await self.make_jmap_request(method_calls)
        
        mailboxes = result["methodResponses"][0][1]["list"]
        found_mailboxes = []
        
        name_search = args.get("name", "").lower()
        role_search = args.get("role")
        
        for mb in mailboxes:
            if role_search and mb.get("role") == role_search:
                found_mailboxes.append(mb)
            elif name_search and name_search in mb["name"].lower():
                found_mailboxes.append(mb)
        
        if not found_mailboxes:
            return [types.TextContent(type="text", text="❌ No mailboxes found matching your criteria.")]
        
        output_lines = [f"🔍 **Found {len(found_mailboxes)} mailbox(es)**\n"]
        for mb in found_mailboxes:
            role = mb.get("role", "folder")
            emoji = {
                "inbox": "📥", "drafts": "📝", "sent": "📤", 
                "trash": "🗑️", "archive": "📦", "junk": "🚫"
            }.get(role, "📁")
            
            output_lines.append(f"{emoji} **{mb['name']}** ({role})")
            output_lines.append(f"   ID: `{mb['id']}`")
            output_lines.append(f"   Emails: {mb.get('totalEmails', 0)} total, {mb.get('unreadEmails', 0)} unread\n")
        
        return [types.TextContent(type="text", text="\n".join(output_lines))]

    async def resolve_mailbox_id(self, mailbox_id: Optional[str], mailbox_name: Optional[str]) -> str:
        """Helper to resolve mailbox ID from either ID or name"""
        if mailbox_id:
            return mailbox_id
            
        if not mailbox_name:
            raise Exception("Either mailboxId or mailboxName must be provided")
            
        # Find mailbox by name
        method_calls = [["Mailbox/get", {"accountId": self.account_id}, "a"]]
        result = await self.make_jmap_request(method_calls)
        mailboxes = result["methodResponses"][0][1]["list"]
        
        for mb in mailboxes:
            if mb["name"].lower() == mailbox_name.lower():
                return mb["id"]
                
        raise Exception(f"Mailbox '{mailbox_name}' not found")

    async def get_emails(self, args: Dict[str, Any]) -> List[types.TextContent]:
        mailbox_id = await self.resolve_mailbox_id(
            args.get("mailboxId"), 
            args.get("mailboxName")
        )
        
        limit = args.get("limit", 20)
        include_body = args.get("includeBody", False)
        
        # Properties to fetch
        properties = ["id", "subject", "from", "to", "receivedAt", "preview", "hasAttachment", "keywords"]
        if include_body:
            properties.extend(["bodyValues", "textBody", "htmlBody"])
        
        method_calls = [
            ["Email/query", {
                "accountId": self.account_id,
                "filter": {"inMailbox": mailbox_id},
                "sort": [{"property": "receivedAt", "isAscending": False}],
                "limit": limit
            }, "q"],
            ["Email/get", {
                "accountId": self.account_id,
                "#ids": {"resultOf": "q", "name": "Email/query", "path": "/ids"},
                "properties": properties
            }, "g"]
        ]
        
        result = await self.make_jmap_request(method_calls)
        emails = result["methodResponses"][1][1]["list"]
        
        if not emails:
            return [types.TextContent(type="text", text="📭 No emails found in this mailbox.")]
        
        output_lines = [f"📧 **Found {len(emails)} email(s)**\n"]
        
        for email in emails:
            # Extract sender info
            from_addr = email.get("from", [{}])[0]
            sender = from_addr.get("name", from_addr.get("email", "Unknown"))
            
            # Format received date
            received = email.get("receivedAt", "").split("T")[0] if email.get("receivedAt") else "Unknown"
            
            # Status indicators
            is_unread = "$seen" not in email.get("keywords", {})
            has_attachment = email.get("hasAttachment", False)
            
            status = "🔵" if is_unread else "⚪"
            attachment_icon = "📎" if has_attachment else ""
            
            output_lines.append(f"{status} **{email.get('subject', '(No subject)')}** {attachment_icon}")
            output_lines.append(f"   From: {sender}")
            output_lines.append(f"   Date: {received}")
            output_lines.append(f"   ID: `{email['id']}`")
            
            if email.get("preview"):
                preview = email["preview"][:100] + "..." if len(email["preview"]) > 100 else email["preview"]
                output_lines.append(f"   Preview: _{preview}_")
            
            if include_body and email.get("bodyValues"):
                # Get text body if available
                for body_part in email.get("textBody", []):
                    if body_part["partId"] in email["bodyValues"]:
                        body_text = email["bodyValues"][body_part["partId"]]["value"]
                        body_preview = body_text[:300] + "..." if len(body_text) > 300 else body_text
                        output_lines.append(f"   Body: {body_preview}")
                        break
            
            output_lines.append("")
        
        return [types.TextContent(type="text", text="\n".join(output_lines))]

    async def search_emails(self, args: Dict[str, Any]) -> List[types.TextContent]:
        # Build JMAP filter from search criteria
        email_filter = {}
        
        if mailbox_id := args.get("mailboxId"):
            email_filter["inMailbox"] = mailbox_id
            
        if keyword := args.get("keyword"):
            email_filter["text"] = keyword
            
        if from_email := args.get("from_email"):
            email_filter["from"] = from_email
            
        if to_email := args.get("to_email"):
            email_filter["to"] = to_email
            
        if subject := args.get("subject"):
            email_filter["subject"] = subject
            
        if "hasAttachment" in args:
            email_filter["hasAttachment"] = args["hasAttachment"]
            
        if before := args.get("before"):
            email_filter["before"] = f"{before}T23:59:59Z"
            
        if after := args.get("after"):
            email_filter["after"] = f"{after}T00:00:00Z"
        
        if not email_filter:
            return [types.TextContent(type="text", text="❌ Please provide at least one search criterion.")]
        
        limit = args.get("limit", 20)
        include_body = args.get("includeBody", False)
        
        properties = ["id", "subject", "from", "to", "receivedAt", "preview", "hasAttachment", "keywords"]
        if include_body:
            properties.extend(["bodyValues", "textBody", "htmlBody"])
        
        method_calls = [
            ["Email/query", {
                "accountId": self.account_id,
                "filter": email_filter,
                "sort": [{"property": "receivedAt", "isAscending": False}],
                "limit": limit
            }, "q"],
            ["Email/get", {
                "accountId": self.account_id,
                "#ids": {"resultOf": "q", "name": "Email/query", "path": "/ids"},
                "properties": properties
            }, "g"]
        ]
        
        result = await self.make_jmap_request(method_calls)
        emails = result["methodResponses"][1][1]["list"]
        
        if not emails:
            return [types.TextContent(type="text", text="🔍 No emails found matching your search criteria.")]
        
        # Build search summary
        search_terms = []
        if args.get("keyword"):
            search_terms.append(f"keyword: '{args['keyword']}'")
        if args.get("from_email"):
            search_terms.append(f"from: '{args['from_email']}'")
        if args.get("subject"):
            search_terms.append(f"subject: '{args['subject']}'")
        
        output_lines = [f"🔍 **Search Results** ({', '.join(search_terms)})", f"Found {len(emails)} email(s)\n"]
        
        for email in emails:
            from_addr = email.get("from", [{}])[0]
            sender = from_addr.get("name", from_addr.get("email", "Unknown"))
            received = email.get("receivedAt", "").split("T")[0] if email.get("receivedAt") else "Unknown"
            
            is_unread = "$seen" not in email.get("keywords", {})
            has_attachment = email.get("hasAttachment", False)
            
            status = "🔵" if is_unread else "⚪"
            attachment_icon = "📎" if has_attachment else ""
            
            output_lines.append(f"{status} **{email.get('subject', '(No subject)')}** {attachment_icon}")
            output_lines.append(f"   From: {sender} | Date: {received}")
            output_lines.append(f"   ID: `{email['id']}`")
            
            if email.get("preview"):
                preview = email["preview"][:100] + "..." if len(email["preview"]) > 100 else email["preview"]
                output_lines.append(f"   _{preview}_")
            
            output_lines.append("")
        
        return [types.TextContent(type="text", text="\n".join(output_lines))]

    async def get_email_body(self, args: Dict[str, Any]) -> List[types.TextContent]:
        email_id = args["emailId"]
        format_type = args.get("format", "text")
        
        properties = ["id", "subject", "from", "to", "receivedAt", "bodyValues", "textBody", "htmlBody"]
        
        method_calls = [
            ["Email/get", {
                "accountId": self.account_id,
                "ids": [email_id],
                "properties": properties
            }, "g"]
        ]
        
        result = await self.make_jmap_request(method_calls)
        emails = result["methodResponses"][0][1]["list"]
        
        if not emails:
            return [types.TextContent(type="text", text="❌ Email not found.")]
        
        email = emails[0]
        output_lines = [f"📧 **Email Body: {email.get('subject', '(No subject)')}**\n"]
        
        # Get text body
        if format_type in ["text", "both"] and email.get("textBody"):
            for body_part in email["textBody"]:
                if body_part["partId"] in email.get("bodyValues", {}):
                    body_text = email["bodyValues"][body_part["partId"]]["value"]
                    output_lines.append("**Text Body:**")
                    output_lines.append(body_text)
                    output_lines.append("")
                    break
        
        # Get HTML body  
        if format_type in ["html", "both"] and email.get("htmlBody"):
            for body_part in email["htmlBody"]:
                if body_part["partId"] in email.get("bodyValues", {}):
                    body_html = email["bodyValues"][body_part["partId"]]["value"]
                    output_lines.append("**HTML Body:**")
                    output_lines.append(f"```html\n{body_html}\n```")
                    break
        
        return [types.TextContent(type="text", text="\n".join(output_lines))]

    async def send_email(self, args: Dict[str, Any]) -> List[types.TextContent]:
        to_emails = [{"email": addr} for addr in args["to"]]
        cc_emails = [{"email": addr} for addr in args.get("cc", [])]
        bcc_emails = [{"email": addr} for addr in args.get("bcc", [])]
        
        subject = args["subject"]
        body = args["body"]
        is_html = args.get("isHtml", False)
        
        # Create email draft
        email_data = {
            "to": to_emails,
            "subject": subject,
            "bodyValues": {
                "body1": {
                    "value": body,
                    "type": "text/html" if is_html else "text/plain"
                }
            }
        }
        
        if is_html:
            email_data["htmlBody"] = [{"partId": "body1", "type": "text/html"}]
        else:
            email_data["textBody"] = [{"partId": "body1", "type": "text/plain"}]
        
        if cc_emails:
            email_data["cc"] = cc_emails
        if bcc_emails:
            email_data["bcc"] = bcc_emails
        
        method_calls = [
            ["Email/set", {
                "accountId": self.account_id,
                "create": {"draft": email_data}
            }, "e"],
            ["EmailSubmission/set", {
                "accountId": self.account_id,
                "create": {
                    "submission": {
                        "#emailId": {"resultOf": "e", "name": "Email/set", "path": "/created/draft/id"},
                        "envelope": {
                            "mailFrom": {"email": ""},  # Will be set by server
                            "rcptTo": to_emails + cc_emails + bcc_emails
                        }
                    }
                }
            }, "s"]
        ]
        
        result = await self.make_jmap_request(method_calls)
        
        # Check for errors
        email_result = result["methodResponses"][0][1]
        if email_result.get("notCreated"):
            error = list(email_result["notCreated"].values())[0]
            return [types.TextContent(type="text", text=f"❌ Failed to create email: {error['description']}")]
        
        submission_result = result["methodResponses"][1][1]
        if submission_result.get("notCreated"):
            error = list(submission_result["notCreated"].values())[0]
            return [types.TextContent(type="text", text=f"❌ Failed to send email: {error['description']}")]
        
        submission_id = list(submission_result["created"].values())[0]["id"]
        return [types.TextContent(type="text", text=f"✅ Email sent successfully! Submission ID: {submission_id}")]

async def main():
    server = FastMailMCPServer()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fastmail",
                server_version="0.1.0",
                capabilities=server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
