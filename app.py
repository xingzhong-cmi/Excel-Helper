"""
Excel Helper V1 - Online Excel Processing Tool
Main Streamlit application with user authentication and file management.
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auth import AuthManager
from file_manager import FileManager
from executor import ControlledExecutor
from api import DeepSeekAPI
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import openpyxl
import os


# Page configuration
st.set_page_config(
    page_title="Excel Helper V1",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "files" not in st.session_state:
        st.session_state.files = {}  # {file_alias: file_id}
    if "active_file" not in st.session_state:
        st.session_state.active_file = None
    if "active_sheet" not in st.session_state:
        st.session_state.active_sheet = None
    if "selection" not in st.session_state:
        st.session_state.selection = None
    if "original_instruction" not in st.session_state:
        st.session_state.original_instruction = ""
    if "optimized_instruction" not in st.session_state:
        st.session_state.optimized_instruction = ""


def login_page():
    """Display the login page."""
    st.markdown('<div class="main-header">📊 Excel Helper V1</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Welcome! Please login to continue.</div>', unsafe_allow_html=True)
    
    auth_manager = AuthManager()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if username and password:
                user = auth_manager.authenticate(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
        
        st.markdown("---")
        st.markdown("**Default admin credentials:**")
        st.code("Username: admin\nPassword: admin123")
        st.info("You can change these via environment variables ADMIN_USER and ADMIN_PASS")


def sidebar_navigation():
    """Display sidebar navigation."""
    with st.sidebar:
        st.markdown("### 👤 User Info")
        st.write(f"**Username:** {st.session_state.user['username']}")
        st.write(f"**Role:** {'Admin' if st.session_state.user['is_admin'] else 'User'}")
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.files = {}
            st.rerun()
        
        st.markdown("---")
        
        # Admin panel
        if st.session_state.user["is_admin"]:
            st.markdown("### 👨‍💼 Admin Panel")
            if st.button("Manage Users"):
                st.session_state.show_admin_panel = True
        
        st.markdown("---")
        st.markdown("### 📁 Files")
        
        if st.session_state.files:
            for alias, file_id in st.session_state.files.items():
                is_active = alias == st.session_state.active_file
                if st.button(f"{'▶ ' if is_active else ''}{alias}", key=f"file_{alias}"):
                    st.session_state.active_file = alias
                    st.rerun()
        else:
            st.info("No files uploaded yet")


def admin_panel():
    """Display admin panel for user management."""
    st.markdown('<div class="sub-header">👨‍💼 User Management</div>', unsafe_allow_html=True)
    
    auth_manager = AuthManager()
    
    # Create new user
    with st.expander("➕ Create New User", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username", key="new_user_username")
            new_password = st.text_input("Password", type="password", key="new_user_password")
        with col2:
            is_admin = st.checkbox("Admin privileges", key="new_user_admin")
            
        if st.button("Create User"):
            if new_username and new_password:
                if auth_manager.create_user(new_username, new_password, is_admin):
                    st.success(f"User '{new_username}' created successfully!")
                else:
                    st.error("Failed to create user. Username may already exist.")
            else:
                st.warning("Please provide both username and password")
    
    # List existing users
    st.markdown("### Existing Users")
    users = auth_manager.list_users()
    
    for user in users:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            st.write(f"**{user['username']}**")
        with col2:
            st.write("Admin" if user['is_admin'] else "User")
        with col3:
            status = "Active" if user['is_active'] else "Disabled"
            st.write(status)
        with col4:
            if user['username'] != st.session_state.user['username']:
                action = "Disable" if user['is_active'] else "Enable"
                if st.button(action, key=f"toggle_{user['username']}"):
                    auth_manager.toggle_user_status(user['username'])
                    st.rerun()


def file_upload_section():
    """Display file upload section."""
    st.markdown('<div class="sub-header">📤 Upload Files</div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (.xlsx)",
        type=["xlsx"],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        file_manager = FileManager(st.session_state.user["user_id"])
        
        for uploaded_file in uploaded_files:
            # Generate file alias
            file_num = len(st.session_state.files) + 1
            file_alias = f"F{file_num}"
            file_id = f"file_{st.session_state.user['user_id']}_{file_num}"
            
            # Check if already uploaded
            if file_alias not in st.session_state.files:
                try:
                    file_path = file_manager.save_uploaded_file(uploaded_file, file_id)
                    st.session_state.files[file_alias] = file_id
                    st.success(f"✅ {uploaded_file.name} uploaded as {file_alias}")
                    
                    # Set as active file if first upload
                    if not st.session_state.active_file:
                        st.session_state.active_file = file_alias
                except Exception as e:
                    st.error(f"Failed to upload {uploaded_file.name}: {str(e)}")


def preview_section():
    """Display preview section with file data."""
    if not st.session_state.active_file:
        st.info("Upload a file to preview")
        return
    
    st.markdown('<div class="sub-header">👁️ Preview</div>', unsafe_allow_html=True)
    
    file_manager = FileManager(st.session_state.user["user_id"])
    file_id = st.session_state.files[st.session_state.active_file]
    file_path = file_manager.get_file_path(file_id)
    
    if not file_path:
        st.error("File not found")
        return
    
    # Sheet selector
    sheet_names = file_manager.get_sheet_names(file_path)
    if not sheet_names:
        st.error("No sheets found in file")
        return
    
    if not st.session_state.active_sheet or st.session_state.active_sheet not in sheet_names:
        st.session_state.active_sheet = sheet_names[0]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.selectbox(
            "Select Sheet",
            sheet_names,
            key="sheet_selector",
            index=sheet_names.index(st.session_state.active_sheet),
            on_change=lambda: setattr(st.session_state, 'active_sheet', st.session_state.sheet_selector)
        )
    with col2:
        st.metric("Active File", st.session_state.active_file)
    
    # Load and display data
    try:
        df = file_manager.read_sheet_data(file_path, st.session_state.active_sheet)
        
        if df.empty:
            st.warning("No data in this sheet")
            return
        
        # Configure AgGrid for interactive selection
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            rowMultiSelectWithClick=True
        )
        gb.configure_default_column(editable=False, filterable=True)
        grid_options = gb.build()
        
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            height=400,
            theme="streamlit"
        )
        
        # Handle selection
        if grid_response["selected_rows"] is not None and len(grid_response["selected_rows"]) > 0:
            selected_df = pd.DataFrame(grid_response["selected_rows"])
            
            # Update selection in session state
            st.session_state.selection = {
                "file_alias": st.session_state.active_file,
                "sheet": st.session_state.active_sheet,
                "rows": list(selected_df.index),
                "columns": list(df.columns),
                "data_sample": selected_df.head(3).to_dict()
            }
            
            st.info(f"Selected {len(selected_df)} row(s)")
            
            # Show reference to insert
            if st.button("📋 Insert Reference to Instruction"):
                ref_text = f"{st.session_state.active_file}.{st.session_state.active_sheet}[rows:{','.join(map(str, selected_df.index[:5]))}]"
                st.session_state.original_instruction += f" {ref_text}"
                st.success("Reference added to instruction!")
                st.rerun()
        
        # Show data info
        st.caption(f"Showing {len(df)} rows × {len(df.columns)} columns (limited to first 300 rows)")
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")


def instruction_section():
    """Display instruction section."""
    st.markdown('<div class="sub-header">📝 Instructions</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Instruction**")
        original = st.text_area(
            "Enter your instruction",
            value=st.session_state.original_instruction,
            height=150,
            key="original_instruction_input",
            label_visibility="collapsed"
        )
        st.session_state.original_instruction = original
    
    with col2:
        st.markdown("**Optimized Instruction**")
        optimized = st.text_area(
            "Optimized instruction (editable)",
            value=st.session_state.optimized_instruction,
            height=150,
            key="optimized_instruction_input",
            label_visibility="collapsed"
        )
        st.session_state.optimized_instruction = optimized
    
    # Optimize button
    if st.button("✨ Optimize Instruction", key="optimize_button"):
        optimize_instruction()
    
    # Show current selection info
    if st.session_state.selection:
        with st.expander("📊 Current Selection Info"):
            st.json(st.session_state.selection)


def optimize_instruction():
    """Optimize instruction using DeepSeek API."""
    api = DeepSeekAPI()
    
    if not api.is_configured():
        st.warning("⚠️ DeepSeek API key not configured. Set DEEPSEEK_API_KEY environment variable.")
        st.info("You can still use the original instruction without optimization.")
        return
    
    if not st.session_state.original_instruction:
        st.warning("Please enter an instruction first")
        return
    
    # Gather file metadata
    file_manager = FileManager(st.session_state.user["user_id"])
    file_metadata = {}
    
    for alias, file_id in st.session_state.files.items():
        file_path = file_manager.get_file_path(file_id)
        if file_path:
            metadata = file_manager.get_file_metadata(file_path)
            file_metadata[alias] = metadata
    
    with st.spinner("🤖 Optimizing instruction..."):
        result = api.optimize_instruction(
            st.session_state.original_instruction,
            st.session_state.selection,
            file_metadata
        )
    
    if result["success"]:
        st.session_state.optimized_instruction = result["optimized_instruction"]
        st.success("✅ Instruction optimized!")
        st.rerun()
    else:
        st.error(f"❌ Optimization failed: {result.get('error', 'Unknown error')}")


def execution_section():
    """Display execution section."""
    st.markdown('<div class="sub-header">▶️ Execution</div>', unsafe_allow_html=True)
    
    instruction_to_use = st.session_state.optimized_instruction or st.session_state.original_instruction
    
    if not instruction_to_use:
        st.info("Please enter an instruction first")
        return
    
    st.markdown("**Instruction to execute:**")
    st.code(instruction_to_use)
    
    if st.button("▶️ Execute", key="execute_button"):
        execute_instruction(instruction_to_use)


def execute_instruction(instruction: str):
    """Execute the given instruction."""
    file_manager = FileManager(st.session_state.user["user_id"])
    executor = ControlledExecutor()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Stage 1: Reading files
        status_text.text("📖 Reading files...")
        progress_bar.progress(0.2)
        
        # Get file metadata
        file_metadata = {}
        for alias, file_id in st.session_state.files.items():
            file_path = file_manager.get_file_path(file_id)
            if file_path:
                metadata = file_manager.get_file_metadata(file_path)
                file_metadata[alias] = metadata
        
        # Stage 2: Parsing instruction
        status_text.text("🔍 Parsing instruction...")
        progress_bar.progress(0.4)
        
        operations = executor.parse_instruction(instruction, file_metadata)
        
        if not operations:
            st.warning("⚠️ No operations could be parsed from the instruction. This is a simplified implementation.")
            st.info("💡 In production, the LLM would generate structured operations from your instruction.")
            return
        
        # Stage 3: Executing operations
        status_text.text("⚙️ Executing operations...")
        progress_bar.progress(0.6)
        
        # For now, execute on the active file
        if st.session_state.active_file:
            file_id = st.session_state.files[st.session_state.active_file]
            file_path = file_manager.get_file_path(file_id)
            
            if file_path:
                wb = openpyxl.load_workbook(file_path)
                result = executor.execute_operations(
                    operations,
                    wb,
                    st.session_state.active_sheet
                )
                
                # Stage 4: Saving results
                status_text.text("💾 Saving results...")
                progress_bar.progress(0.8)
                
                if result["success"] or result["operations_completed"] > 0:
                    new_revision = file_manager.save_modified_file(file_id, wb)
                    
                    # Stage 5: Complete
                    status_text.text("✅ Complete!")
                    progress_bar.progress(1.0)
                    
                    st.success(f"✅ Execution completed! {result['operations_completed']} operations performed.")
                    st.info(f"📦 New revision created: rev_{new_revision}")
                    
                    if result["errors"]:
                        st.warning("⚠️ Some operations had errors:")
                        for error in result["errors"]:
                            st.text(f"  • {error}")
                    
                    # Show download button
                    with open(file_manager.get_file_path(file_id, new_revision), "rb") as f:
                        st.download_button(
                            "⬇️ Download Result",
                            f,
                            file_name=f"result_{file_id}_rev{new_revision}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # Accept changes button
                    if st.button("✔️ Accept Changes and Continue"):
                        st.success("Changes accepted! This revision is now active.")
                        st.rerun()
                else:
                    st.error("❌ Execution failed. No operations could be completed.")
                    for error in result["errors"]:
                        st.text(f"  • {error}")
        
    except Exception as e:
        st.error(f"❌ Execution failed: {str(e)}")
        status_text.text("❌ Failed")
        progress_bar.progress(1.0)


def main_app():
    """Main application interface."""
    st.markdown('<div class="main-header">📊 Excel Helper V1</div>', unsafe_allow_html=True)
    
    sidebar_navigation()
    
    # Show admin panel if requested
    if st.session_state.get("show_admin_panel", False):
        admin_panel()
        if st.button("← Back to Main"):
            st.session_state.show_admin_panel = False
            st.rerun()
        return
    
    # Main content
    file_upload_section()
    
    st.markdown("---")
    
    # Two-column layout for preview and instructions
    col1, col2 = st.columns([1, 1])
    
    with col1:
        preview_section()
    
    with col2:
        instruction_section()
    
    st.markdown("---")
    
    execution_section()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; font-size: 0.9rem;">
        Excel Helper V1 | Powered by Streamlit & DeepSeek
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main entry point."""
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()


if __name__ == "__main__":
    main()
