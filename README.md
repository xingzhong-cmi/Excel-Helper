# Excel Helper MVP - Plan-Based Excel Processing Tool

📊 A web-based Excel processing tool with structured plan-based execution, user authentication, and AI-powered assistance.

## 🎯 MVP Overview

This MVP focuses on **usability and reliability** through structured, validated execution plans. Users can complete common Excel operations in 3 minutes: **Upload** → **Select** → **Instruct** → **Generate Plan** → **Execute** → **Download**.

### Key MVP Features

- **✅ Structured Execution Plans**: JSON-based plans with Pydantic validation ensure safe, predictable operations
- **🤖 AI + Manual Modes**: Works with or without DeepSeek API - form-based fallback always available
- **📋 5 Core Operations**: Filter/delete rows, deduplicate, fill nulls, type conversion, column split/merge
- **📊 Change Summaries**: Detailed before/after statistics for every operation
- **🔒 Safe Execution**: Whitelist-based operations, no arbitrary code execution
- **👁️ Interactive Selection**: Click rows to reference them in instructions

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
- Interactive table with row selection
- Click-to-reference: insert selected rows into instructions
- Multi-file and multi-sheet navigation
- Selection card shows current file, sheet, and rows

### 📝 Smart Instructions
- Original instruction input (supports Chinese and English)
- AI-powered plan generation via DeepSeek API (optional)
- Manual form-based plan builder (works without AI)
- Context-aware suggestions with file metadata

### 🎯 Plan-Based Execution (NEW!)
- **Generate Plan**: AI converts natural language to validated JSON plans
- **Manual Builder**: Form-based interface for creating plans operation-by-operation
- **Plan Preview**: Review the structured plan before execution
- **5 Core Operations**:
  1. **Filter/Delete Rows**: Remove or keep rows based on column conditions
  2. **Deduplicate**: Remove duplicate rows by column(s)
  3. **Fill Nulls**: Fill empty cells with fixed values or forward/backward fill
  4. **Type Conversion**: Convert columns to text/number/date with error tracking
  5. **Column Split/Merge**: Split by delimiter or merge multiple columns

### 📊 Execution Results (NEW!)
- **Change Summary**: Shows operations completed, rows affected, cells filled, failures, etc.
- **Preview**: First 300 rows of modified data
- **Download**: Get modified files with revision numbers
- **Accept Changes**: Apply modifications and continue working

### ⚙️ Safe Execution
- Controlled executor with whitelist-based operations
- Pydantic schema validation for all plans
- No arbitrary code execution
- Progress tracking and detailed error reporting

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

### Quick Start (3-Minute Workflow)

1. **Login** with admin/admin123 (or your credentials)
2. **Upload** an Excel file - it gets alias F1
3. **Preview** your data and optionally select rows
4. **Enter instruction** (e.g., "删除Status列为Cancelled的行" or "Remove rows where Status is Cancelled")
5. **Generate Plan**:
   - With AI: Click "Generate Plan (AI)" - converts instruction to JSON automatically
   - Without AI: Use the form builder to add operations manually
6. **Review Plan** - See exactly what will happen
7. **Execute Plan** - Run the operations
8. **Review Results** - See change summary (rows deleted, cells filled, etc.)
9. **Download** - Get your modified file

### Detailed Usage

#### 1. Login
- Use default credentials (admin/admin123) or credentials created by admin
- First-time setup creates admin user automatically

#### 2. Upload Files
- Click "Browse files" to upload one or more Excel files
- Files are automatically assigned aliases (F1, F2, ...)
- Files are stored securely in your isolated user directory

#### 3. Preview & Select
- Click file aliases in sidebar to switch between files
- Select sheets from dropdown
- Click rows in the table to select them
- Selection card shows: file alias, sheet name, row count
- Use "Insert Reference" to add selection like `F1.Sheet1[rows:0,1,2...]` to instruction

#### 4. Create Instructions (Two Ways)

**Option A: Natural Language (Requires DeepSeek API)**
- Enter instruction in Chinese or English
- Examples:
  - "删除Status列等于Cancelled的所有行"
  - "Remove duplicate rows based on ID column"
  - "Fill empty Region cells with 'Unknown'"
- Click "Generate Plan (AI)"
- AI converts to structured JSON plan

**Option B: Form Builder (No API Needed)**
- Click "Build Plan Manually" 
- Select operation type from dropdown
- Fill in parameters:
  - Choose file and sheet
  - Specify columns
  - Set conditions or values
- Click "Add Operation"
- Repeat for multiple operations
- Click "Build Plan from Operations"

#### 5. Review Plan
- Expandable JSON view shows the structured plan
- Operation summary lists each step
- Verify targets (file, sheet, columns) are correct

#### 6. Execute Plan
- Click "Execute Plan" button
- Progress bar shows: Loading → Executing → Saving
- Watch operation count increase

#### 7. Review Results
- **Change Summary** shows:
  - Operations completed/failed
  - Rows deleted, duplicates removed
  - Cells filled, nulls remaining
  - Type conversion successes/failures
  - Columns added/removed
- **Preview** shows first 300 rows of result
- **Errors** displayed if any operations failed

#### 8. Download & Continue
- Click download button for each modified file
- File name includes revision number
- Click "Accept Changes and Continue" to make this version active
- Or "Start New Operation" to keep original active

#### 9. Manage Users (Admin Only)
- Click "Manage Users" in sidebar
- Create new users with username and password
- Toggle user status (enable/disable)
- Assign admin privileges

## Operation Examples

### Example 1: Clean Sales Data
```
Instruction: "Remove cancelled orders, deduplicate by order ID, and fill missing regions"

Generated Plan:
1. Filter/Delete Rows: Status = 'Cancelled' → delete
2. Deduplicate: by OrderID column, keep first
3. Fill Nulls: Region column with 'Unknown'

Result: 
- Rows deleted: 15
- Duplicates removed: 8
- Cells filled: 23
```

### Example 2: Data Type Cleanup
```
Instruction: "Convert Amount to number and OrderDate to date format"

Generated Plan:
1. Type Conversion: Amount → number
2. Type Conversion: OrderDate → date (format: %Y-%m-%d)

Result:
- Successful conversions: 145
- Failed conversions: 3 (shows row numbers)
```

### Example 3: Column Manipulation
```
Instruction: "Split FullName into FirstName and LastName, then merge Address columns"

Generated Plan:
1. Column Split: FullName by " " → [FirstName, LastName]
2. Column Merge: [Street, City, State] → FullAddress with ", "

Result:
- Columns created: 2
- Columns merged: 3 into 1
```

## Architecture

```
Excel-Helper/
├── app.py                 # Main Streamlit application (875 lines)
├── core/                  # NEW: Core execution engine
│   ├── __init__.py       # Module exports
│   ├── plan.py           # Pydantic schemas for execution plans
│   ├── planner.py        # AI + form-based plan generation
│   ├── executor.py       # Safe plan execution engine
│   └── diff.py           # Change summary generation
├── src/                   # Original modules (preserved)
│   ├── auth.py           # User authentication & management
│   ├── file_manager.py   # File operations & versioning
│   ├── executor.py       # Legacy executor (kept for compatibility)
│   └── api.py            # DeepSeek API integration
├── tests/                 # NEW: Unit tests
│   ├── test_plan.py      # Plan validation tests (12 tests)
│   └── test_executor.py  # Executor operation tests (7 tests)
├── data/                  # User data (git-ignored)
│   ├── users.db          # User database
│   └── <user_id>/        # User-isolated file storage
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Key Components

**Core Module** (NEW):
- **plan.py**: Pydantic models for 5 operation types with validation
- **planner.py**: Generates plans from natural language (AI) or forms (manual)
- **executor.py**: Executes validated plans safely on pandas DataFrames
- **diff.py**: Compares before/after states, generates change summaries

**Plan Schema Example**:
```json
{
  "description": "Clean customer data",
  "operations": [
    {
      "type": "deduplicate",
      "target": {"file_alias": "F1", "sheet_name": "Customers"},
      "params": {"columns": ["Email"], "keep": "first"},
      "description": "Remove duplicate emails"
    },
    {
      "type": "fill_nulls",
      "target": {"file_alias": "F1", "sheet_name": "Customers"},
      "params": {
        "column": "Phone",
        "strategy": "fixed_value",
        "value": "N/A"
      },
      "description": "Fill missing phone numbers"
    }
  ]
}
```

## Security Features

- ✅ **Password hashing** (SHA-256)
- ✅ **User file isolation** with logical validation
- ✅ **Pydantic validation** for all execution plans
- ✅ **Whitelist-only operations** (5 core operations)
- ✅ **No arbitrary code execution** or eval()
- ✅ **Session-based authentication**
- ✅ **XSRF protection** enabled
- ✅ **Secure file uploads** with size limits
- ✅ **Plan validation** before execution (targets, columns, data types)

## MVP Scope & Limitations

### What's Included (MVP V1)
- ✅ 5 core high-frequency operations
- ✅ Single active file + active sheet per execution
- ✅ AI-powered plan generation (DeepSeek)
- ✅ Form-based manual plan builder
- ✅ Detailed change summaries
- ✅ Preview and download results
- ✅ Works without AI (form fallback)
- ✅ Multi-user support with isolation
- ✅ Comprehensive unit tests (19 tests)

### Current Limitations
- Operations target single file + sheet (V1 scope)
- Excel formula preservation is best-effort (openpyxl)
- Complex formatting may not be fully preserved
- Maximum 200MB file upload (configurable)
- Preview limited to 300 rows per sheet (configurable)
- AI plan generation requires DeepSeek API key (optional)

## Future Enhancements (V2+)

### Near-term
- [ ] Cross-file operations in a single plan
- [ ] More operation types (formulas, conditional formatting, pivot tables)
- [ ] Cell-level selection (currently row-level)
- [ ] Plan templates library
- [ ] Batch processing multiple files

### Long-term
- [ ] Collaboration features (shared files)
- [ ] Export to multiple formats (CSV, PDF)
- [ ] Scheduled/automated operations
- [ ] Audit logs and activity tracking
- [ ] API endpoints for programmatic access
- [ ] Custom operation plugins

## Troubleshooting

### "No module named 'core'" or "No module named 'src'"
- Make sure you're running from the repository root directory
- The app.py file adds paths automatically
- Try: `cd Excel-Helper && streamlit run app.py`

### "API key not configured" or AI features not working
- **This is optional!** The app works without the DeepSeek API
- Use the **form-based plan builder** instead (no AI needed)
- To enable AI: set `DEEPSEEK_API_KEY` environment variable
- Get API key from https://platform.deepseek.com/

### "Plan validation failed" error
- Check that column names match exactly (case-sensitive)
- Verify file alias (F1, F2, etc.) and sheet name are correct
- Use the preview section to see available columns
- Try the form builder to avoid typos

### "Permission denied" errors
- Ensure the `data/` directory is writable
- Check file permissions on Linux/Mac systems

### Database errors
- Delete `data/users.db` to reset (will lose all users)
- Admin user will be recreated on next startup

## Development & Testing

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_plan.py -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

### Test Coverage
- **19 total tests** covering core functionality
- **12 plan validation tests**: Schema, operations, JSON serialization
- **7 executor tests**: All 5 operations, multi-operation plans, error handling

### Adding New Operations

To add a new operation type:

1. **Define params class** in `core/plan.py`:
   ```python
   class MyOperationParams(BaseModel):
       column: str
       value: str
   ```

2. **Add to OperationType enum**:
   ```python
   class OperationType(str, Enum):
       MY_OPERATION = "my_operation"
   ```

3. **Implement executor** in `core/executor.py`:
   ```python
   def _execute_my_operation(self, df, params):
       # Your logic here
       return result_df, summary_dict
   ```

4. **Add form UI** in `app.py` under `build_manual_plan()`:
   ```python
   elif op_type == "my_operation":
       # Form fields for your operation
   ```

5. **Write tests** in `tests/test_executor.py`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass: `pytest tests/ -v`
5. Update documentation
6. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function signatures
- Add docstrings for public functions
- Keep functions focused and testable

## License

See LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Built with ❤️ using Streamlit, Pydantic, Pandas, OpenPyXL, and DeepSeek**

## MVP Features Changelog

### V1 MVP (Current)
- ✅ **Plan-based execution**: Structured, validated JSON plans
- ✅ **5 core operations**: Filter, deduplicate, fill nulls, type conversion, split/merge
- ✅ **Dual mode**: AI-powered + manual form builder
- ✅ **Change summaries**: Detailed before/after statistics
- ✅ **Unit tests**: 19 tests with 100% pass rate
- ✅ **Multi-language**: Chinese and English instructions
- ✅ **Safety**: Pydantic validation, whitelist operations

### Coming in V2
- 🔄 Cross-file operations
- 🔄 Cell-level selection
- 🔄 Formula operations
- 🔄 Plan templates
- 🔄 Batch processing