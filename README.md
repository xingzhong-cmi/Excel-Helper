# Excel Helper V1 - Online Excel Processing Tool

📊 A web-based Excel processing tool with user authentication, file isolation, and AI-powered instruction optimization.

## Features

### 🔐 User Authentication & Isolation
- Username/password authentication with SQLite storage
- Admin panel for user management
- Complete file isolation between users (stored in `data/<user_id>/`)
- Secure session management

### 📤 File Management
- Upload multiple Excel files (.xlsx)
- Automatic file aliasing (F1, F2, ...)
- Multi-sheet support with easy switching
- Revision history tracking (configurable retention)
- Download any revision

### 👁️ Interactive Preview
- View up to 300 rows per sheet (configurable)
- Interactive table with cell/row/column selection
- Click-to-reference: insert selected cells into instructions
- Multi-file and multi-sheet navigation

### 📝 Smart Instructions
- Original instruction input
- AI-powered instruction optimization via DeepSeek API
- Editable optimized instructions
- Context-aware suggestions with file metadata

### ⚙️ Safe Execution
- Controlled executor with whitelist-based operations
- No arbitrary code execution
- Progress tracking (read → parse → execute → save → complete)
- Detailed operation logs and error reporting

### 📦 Version Control
- Automatic revision creation for all modifications
- Preview and download any revision
- "Accept Changes" to make a revision active
- Automatic cleanup of old revisions

## Quick Start

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/xingzhong-cmi/Excel-Helper.git
   cd Excel-Helper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your DeepSeek API key and admin credentials
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Access the app:**
   Open your browser to `http://localhost:8501`

6. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin123`

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# DeepSeek API (optional - app works without it)
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30

# Admin credentials
ADMIN_USER=admin
ADMIN_PASS=admin123
```

## Deployment

### Streamlit Community Cloud (Recommended)

1. **Fork this repository** to your GitHub account

2. **Go to [Streamlit Community Cloud](https://streamlit.io/cloud)**

3. **Create a new app:**
   - Repository: `your-username/Excel-Helper`
   - Branch: `main`
   - Main file: `app.py`

4. **Configure secrets** (optional for API features):
   - Go to App Settings → Secrets
   - Add your environment variables:
     ```toml
     DEEPSEEK_API_KEY = "your_api_key_here"
     DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
     DEEPSEEK_MODEL = "deepseek-chat"
     ADMIN_USER = "admin"
     ADMIN_PASS = "your_secure_password"
     ```

5. **Deploy!** Your app will be live at `https://your-app-name.streamlit.app`

### Hugging Face Spaces (Alternative)

1. **Create a new Space** at [Hugging Face Spaces](https://huggingface.co/spaces)

2. **Select Streamlit** as the SDK

3. **Upload files:**
   - All Python files from this repository
   - `requirements.txt`
   - `.streamlit/config.toml`

4. **Configure secrets:**
   - Go to Settings → Repository secrets
   - Add environment variables as needed

5. **Your app** will be available at `https://huggingface.co/spaces/your-username/excel-helper`

## Usage Guide

### 1. Login
- Use default credentials (admin/admin123) or credentials created by admin
- First-time setup creates admin user automatically

### 2. Upload Files
- Click "Browse files" to upload one or more Excel files
- Files are automatically assigned aliases (F1, F2, ...)
- Files are stored securely in your isolated user directory

### 3. Preview & Select
- Click file aliases in sidebar to switch between files
- Select sheets from dropdown
- Click rows in the table to select them
- Use "Insert Reference" to add selection to instruction

### 4. Create Instructions
- Enter your instruction in "Original Instruction" text box
- Click "Optimize Instruction" to get AI-enhanced version (requires API key)
- Edit the optimized instruction as needed

### 5. Execute
- Click "Execute" to run the instruction
- Watch progress through stages
- Review operation log and any errors
- Download the result file
- Click "Accept Changes" to make the revision active

### 6. Manage Users (Admin Only)
- Click "Manage Users" in sidebar
- Create new users with username and password
- Toggle user status (enable/disable)
- Assign admin privileges

## Architecture

```
Excel-Helper/
├── app.py                 # Main Streamlit application
├── src/
│   ├── auth.py           # User authentication & management
│   ├── file_manager.py   # File operations & versioning
│   ├── executor.py       # Controlled Excel operations
│   └── api.py            # DeepSeek API integration
├── data/                 # User data (git-ignored)
│   ├── users.db         # User database
│   └── <user_id>/       # User-isolated file storage
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Security Features

- ✅ Password hashing (SHA-256)
- ✅ User file isolation with logical validation
- ✅ Controlled executor (whitelist-only operations)
- ✅ No arbitrary code execution
- ✅ Session-based authentication
- ✅ XSRF protection enabled
- ✅ Secure file uploads with size limits

## Limitations (V1)

- Instruction parsing is simplified; production would use LLM for operation generation
- Excel formula preservation is best-effort (uses openpyxl)
- Complex formatting may not be fully preserved
- Maximum 200MB file upload (configurable)
- Preview limited to 300 rows per sheet (configurable)

## Future Enhancements (V2+)

- [ ] More sophisticated instruction parser using LLM
- [ ] Support for more Excel operations
- [ ] Collaboration features (shared files)
- [ ] Export to multiple formats (CSV, PDF)
- [ ] Scheduled/automated operations
- [ ] Audit logs and activity tracking
- [ ] API endpoints for programmatic access

## Troubleshooting

### "No module named 'src'"
- Make sure you're running from the repository root directory
- The app.py file adds src to the Python path automatically

### "API key not configured"
- This is optional! The app works without the DeepSeek API
- You can still use original instructions without optimization
- To enable optimization, set DEEPSEEK_API_KEY environment variable

### "Permission denied" errors
- Ensure the `data/` directory is writable
- Check file permissions on Linux/Mac systems

### Database errors
- Delete `data/users.db` to reset (will lose all users)
- Admin user will be recreated on next startup

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Built with ❤️ using Streamlit, OpenPyXL, and DeepSeek**