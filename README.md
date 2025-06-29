# FastMail MCP Server

A Model Context Protocol (MCP) server for integrating with FastMail's JMAP API. This server provides tools for reading emails, searching, managing folders, and sending emails through FastMail.

## 🚀 Features

- **📁 Mailbox Management**: List and find mailboxes/folders
- **📧 Email Reading**: Get emails from specific folders with previews
- **🔍 Advanced Search**: Search by keyword, sender, subject, date range, attachments
- **📤 Email Sending**: Send emails with CC/BCC support
- **🎯 Folder Targeting**: Search within specific folders
- **⚡ Fast Performance**: Uses FastMail's modern JMAP protocol

## 📋 Prerequisites

- Python 3.8+
- FastMail account with API access
- API token from FastMail (Settings → Privacy & Security → Integrations)

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd fastmail-mcp-server
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your FastMail API token:**
   - Log into FastMail
   - Go to Settings → Privacy & Security → Integrations
   - Create a new API token
   - Copy the token (starts with `fmu1-`)

## 🚀 Usage

### Running the Server

```bash
python fastmail_mcp_server.py
```

The server will start and listen for MCP commands via stdio.

### Configuration

First, configure your FastMail credentials:

```json
{
  "tool": "configure_fastmail",
  "arguments": {
    "apiToken": "fmu1-your-token-here"
  }
}
```

### Available Tools

#### 📁 **configure_fastmail**
Set up your FastMail API credentials.

#### 📁 **list_mailboxes**
List all mailboxes with their names, roles, and email counts.
```json
{
  "tool": "list_mailboxes",
  "arguments": {
    "role": "inbox"  // Optional: filter by role
  }
}
```

#### 🔍 **find_mailbox**
Find a specific mailbox by name or role.
```json
{
  "tool": "find_mailbox", 
  "arguments": {
    "name": "Work",     // Partial matching supported
    "role": "sent"      // Or search by role
  }
}
```

#### 📧 **get_emails**
Get emails from a specific mailbox.
```json
{
  "tool": "get_emails",
  "arguments": {
    "mailboxId": "mailbox-id-here",  // From list_mailboxes
    "mailboxName": "Inbox",          // Alternative to mailboxId
    "limit": 20,                     // Max emails to fetch
    "includeBody": false             // Include full email body
  }
}
```

#### 🔍 **search_emails**
Search emails with advanced filtering.
```json
{
  "tool": "search_emails",
  "arguments": {
    "keyword": "project update",     // Text search
    "from_email": "boss@company.com", // From specific sender
    "subject": "meeting",            // Subject contains
    "mailboxId": "inbox-id",         // Search within folder
    "hasAttachment": true,           // Has attachments
    "after": "2024-01-01",          // Date range
    "before": "2024-12-31",
    "limit": 50,
    "includeBody": false
  }
}
```

#### 📖 **get_email_body**
Get the full body content of a specific email.
```json
{
  "tool": "get_email_body",
  "arguments": {
    "emailId": "email-id-here",
    "format": "text"  // "text", "html", or "both"
  }
}
```

#### 📤 **send_email**
Send an email through FastMail.
```json
{
  "tool": "send_email",
  "arguments": {
    "to": ["recipient@example.com"],
    "cc": ["cc@example.com"],        // Optional
    "bcc": ["bcc@example.com"],      // Optional  
    "subject": "Hello from MCP!",
    "body": "This is the email body.",
    "isHtml": false                  // Set to true for HTML emails
  }
}
```

## 🔧 Integration with MCP Clients

### Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "fastmail": {
      "command": "python",
      "args": ["/path/to/fastmail_mcp_server.py"]
    }
  }
}
```

### Other MCP Clients

This server follows the standard MCP protocol and should work with any MCP-compatible client.

## 🏗 Project Structure

```
fastmail-mcp-server/
├── fastmail_mcp_server.py    # Main server implementation
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Package configuration
├── README.md                # This file
└── examples/                # Example usage scripts
    └── test_server.py       # Test script
```

## 🔒 Security Notes

- **API Token Security**: Never commit your API token to version control
- **Permissions**: The API token has access to your entire FastMail account
- **Network**: All communication uses HTTPS with FastMail's secure APIs

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your API token is correct and has proper permissions
2. **Connection Error**: Check your internet connection and FastMail service status
3. **Missing Emails**: Ensure you're searching in the correct mailbox

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export MCP_DEBUG=1
python fastmail_mcp_server.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- [FastMail](https://fastmail.com) for their excellent JMAP API
- [Model Context Protocol](https://github.com/anthropics/mcp) by Anthropic
- [JMAP Specification](https://jmap.io) by the IETF

## 📚 Additional Resources

- [FastMail API Documentation](https://www.fastmail.com/dev/)
- [JMAP Specification](https://jmap.io)
- [MCP Documentation](https://github.com/anthropics/mcp)
