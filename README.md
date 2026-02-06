# Excel Helper - AI-Powered Excel Processing Tool

A web-based Excel processing tool with AI-powered instruction optimization, multi-user support, file versioning, and interactive cell selection.

## Features

### 🔐 Authentication & User Isolation
- Secure user authentication with bcrypt password hashing
- Multi-user support with complete data isolation
- Each user has their own workspace with isolated file storage
- Simple account creation and management
- Secure logout functionality

### 📁 File Management & Preview
- Upload multiple Excel (.xlsx) files simultaneously
- Automatic file aliasing (F1, F2, F3, ...)
- Interactive file preview with multi-sheet support
- View up to 300 rows per sheet (configurable)
- Interactive cell/row selection using AgGrid
- Selected cells are automatically referenced in instructions

### ✨ AI-Powered Instruction Optimization
- Natural language instruction input
- AI optimization using DeepSeek API
- Context-aware optimization includes:
  - Selected cells/rows/columns
  - Available files and their structure
  - Worksheet names and column headers
- Editable optimized instructions
- Automatic multi-file operation support

### ⚙️ Excel Processing Engine
- Execute operations based on natural language instructions
- Support for multiple operation types:
  - Filtering data
  - Sorting columns
  - Calculations and aggregations
  - Column/row deletion
  - Data merging
- Real-time progress indicators
- Multi-file processing support

### 📊 Version Control & Iteration
- Complete revision history for each file
- Create new versions after each operation
- Preview results before accepting changes
- "Accept & Continue" workflow for iterative processing
- Configurable revision retention (default: 10 versions)
- Download any version at any time

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/xingzhong-cmi/Excel-Helper.git
   cd Excel-Helper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   - `DEEPSEEK_API_KEY`: Your DeepSeek API key
   - `DEEPSEEK_BASE_URL`: API endpoint (default: https://api.deepseek.com)
   - `DEEPSEEK_MODEL`: Model name (default: deepseek-chat)
   - `APP_SECRET_KEY`: Application secret key (change in production)
   - `DEFAULT_ADMIN_USERNAME`: Initial admin username
   - `DEFAULT_ADMIN_PASSWORD`: Initial admin password

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## Usage Guide

### Getting Started

1. **Login/Create Account**
   - On first launch, a default admin account is created
   - You can create additional accounts using the "Create Account" button
   - Login with your credentials

2. **Upload Excel Files**
   - Click "Browse files" in the sidebar
   - Select one or more .xlsx files
   - Files are automatically assigned aliases (F1, F2, ...)

3. **Preview Files**
   - Click on a file in the sidebar to preview it
   - Switch between worksheets using the dropdown
   - Click on rows to select them for operations

4. **Write Instructions**
   - Enter your operation in plain language in the "Original Instruction" box
   - Click "Optimize Instruction" to get AI-enhanced version
   - Edit the optimized instruction if needed

5. **Execute Operations**
   - Click "Execute Instruction" to process files
   - Review the results in the execution area
   - Download modified files or click "Accept & Continue" to update

### Example Instructions

**Filter data:**
```
Filter F1 to show only rows where Sales column is greater than 1000
```

**Sort data:**
```
Sort F1 by Date column in descending order
```

**Calculate:**
```
In F1, calculate the sum of columns A and B and put result in new column
```

**Multi-file operations:**
```
Merge F1 and F2 based on ID column
```

## Architecture

### Components

1. **identity_system.py**: User authentication and account management
2. **document_archive.py**: File storage and version control
3. **instruction_ai.py**: DeepSeek API integration for instruction optimization
4. **excel_processor.py**: Excel processing engine
5. **app.py**: Main Streamlit application

### Data Storage Structure

```
data/
├── identity_vault.json          # User credentials
└── uid_0001/                    # User workspace
    ├── doc_20240101_120000/     # Document container
    │   ├── record.json          # Document metadata
    │   ├── snap_0000.xlsx       # Initial version
    │   ├── snap_0001.xlsx       # Version 1
    │   └── snap_0002.xlsx       # Version 2
    └── doc_20240101_120100/     # Another document
        └── ...
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | Required |
| `DEEPSEEK_BASE_URL` | API endpoint | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | Model name | deepseek-chat |
| `DEEPSEEK_TIMEOUT` | API timeout (seconds) | 30 |
| `APP_SECRET_KEY` | Application secret | Required |
| `MAX_PREVIEW_ROWS` | Max rows to preview | 300 |
| `MAX_REVISIONS` | Max versions to keep | 10 |
| `DATA_DIR` | Data storage directory | data |
| `DEFAULT_ADMIN_USERNAME` | Initial admin username | admin |
| `DEFAULT_ADMIN_PASSWORD` | Initial admin password | admin123 |

## Deployment

### Local Deployment
Follow the installation steps above.

### Cloud Deployment

The application can be deployed to any platform that supports Python and Streamlit:

#### Streamlit Cloud
1. Push your code to GitHub
2. Connect your GitHub repository to Streamlit Cloud
3. Add environment variables in Streamlit Cloud settings
4. Deploy

#### Heroku
1. Create a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT
   ```
2. Add `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "[server]\nport = $PORT\nenableCORS = false\nheadless = true\n" > ~/.streamlit/config.toml
   ```
3. Deploy using Heroku CLI

#### Docker
1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py"]
   ```
2. Build and run:
   ```bash
   docker build -t excel-helper .
   docker run -p 8501:8501 --env-file .env excel-helper
   ```

## Security Considerations

- **Password Security**: Passwords are hashed using bcrypt with salt rounds
- **User Isolation**: Each user's data is stored in separate directories
- **Session Management**: Streamlit session state ensures user separation
- **API Keys**: Store API keys in environment variables, never in code
- **File Access**: File paths are validated to prevent directory traversal
- **HTTPS**: Use HTTPS in production deployments

## Troubleshooting

### DeepSeek API Issues
- Verify API key is correct
- Check internet connectivity
- Ensure API endpoint is accessible
- Review timeout settings

### File Upload Issues
- Check file format (must be .xlsx)
- Verify file size limits
- Ensure sufficient disk space

### Preview Issues
- Large files may take time to load
- Reduce MAX_PREVIEW_ROWS if performance is poor
- Check file integrity

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
- Check existing documentation
- Review configuration settings

## Acknowledgments

- Built with Streamlit
- Powered by DeepSeek AI
- Uses pandas, openpyxl for Excel processing
- AgGrid for interactive tables