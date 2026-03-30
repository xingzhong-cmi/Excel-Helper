"""
Excel Helper V1 - Online Excel Processing Tool
Main Streamlit application with user authentication and file management.
"""
import streamlit as st
import sys
from pathlib import Path
import json

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

# Import new core modules
from core.planner import PlanGenerator
from core.executor import PlanExecutor
from core.diff import ChangeSummary
from core.plan import ExecutionPlan, OperationType, FillStrategy, DataType


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
    if "generated_plan" not in st.session_state:
        st.session_state.generated_plan = None
    if "execution_result" not in st.session_state:
        st.session_state.execution_result = None
    if "form_operations" not in st.session_state:
        st.session_state.form_operations = []


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
        
        # Configure AgGrid with row selection
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
                "sheet_name": st.session_state.active_sheet,
                "rows": list(selected_df.index),
                "row_count": len(selected_df),
                "columns": list(df.columns),
                "data_sample": selected_df.head(3).to_dict()
            }
            
            # Show selection card
            with st.expander("📊 Current Selection", expanded=True):
                st.write(f"**File:** {st.session_state.active_file}")
                st.write(f"**Sheet:** {st.session_state.active_sheet}")
                st.write(f"**Rows selected:** {len(selected_df)}")
                if len(selected_df) <= 10:
                    st.write(f"**Row indices:** {', '.join(map(str, selected_df.index))}")
                else:
                    st.write(f"**Row indices:** {', '.join(map(str, selected_df.index[:10]))}... (+{len(selected_df)-10} more)")
                
                # Insert reference button
                if st.button("📋 Insert Reference to Instruction"):
                    ref_text = f" {st.session_state.active_file}.{st.session_state.active_sheet}[rows:{','.join(map(str, selected_df.index[:5]))}{'...' if len(selected_df) > 5 else ''}]"
                    st.session_state.original_instruction += ref_text
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


def plan_generation_section():
    """Display plan generation section with AI and form-based options."""
    st.markdown('<div class="sub-header">🎯 Plan Generation</div>', unsafe_allow_html=True)
    
    instruction_to_use = st.session_state.optimized_instruction or st.session_state.original_instruction
    
    if not instruction_to_use and not st.session_state.generated_plan:
        st.info("Enter an instruction above or use the manual form below to create a plan")
        return
    
    # Show current plan if exists
    if st.session_state.generated_plan:
        st.success("✅ Plan generated successfully!")
        with st.expander("📋 View Generated Plan (JSON)", expanded=False):
            st.code(st.session_state.generated_plan.to_json(), language="json")
        
        # Show operation summary
        st.markdown("**Operations:**")
        for i, op in enumerate(st.session_state.generated_plan.operations):
            st.write(f"{i+1}. **{op.type.value}** on `{op.target.file_alias}.{op.target.sheet_name}`")
            if op.description:
                st.caption(f"   ↳ {op.description}")
    
    # Generate plan buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🤖 Generate Plan (AI)", key="generate_plan_ai", disabled=not instruction_to_use):
            generate_plan_with_ai(instruction_to_use)
    
    with col2:
        if st.button("🔄 Clear Plan", key="clear_plan"):
            st.session_state.generated_plan = None
            st.session_state.execution_result = None
            st.rerun()
    
    st.markdown("---")
    
    # Manual plan builder form
    with st.expander("📝 Manual Plan Builder", expanded=not st.session_state.generated_plan):
        st.markdown("**Build a plan manually by adding operations:**")
        
        # Get available files and sheets for dropdowns
        file_manager = FileManager(st.session_state.user["user_id"])
        available_files = list(st.session_state.files.keys())
        
        if not available_files:
            st.warning("No files available. Upload a file first.")
            return
        
        # Operation type selector
        op_type = st.selectbox(
            "Operation Type",
            options=[op.value for op in OperationType],
            key="form_op_type"
        )
        
        # Target selection
        col1, col2 = st.columns(2)
        with col1:
            target_file = st.selectbox("Target File", available_files, key="form_target_file")
        
        with col2:
            file_id = st.session_state.files[target_file]
            file_path = file_manager.get_file_path(file_id)
            sheet_names = file_manager.get_sheet_names(file_path) if file_path else []
            target_sheet = st.selectbox("Target Sheet", sheet_names, key="form_target_sheet")
        
        # Get columns for the selected sheet
        if file_path and target_sheet:
            df = file_manager.read_sheet_data(file_path, target_sheet)
            columns = list(df.columns) if not df.empty else []
        else:
            columns = []
        
        # Operation-specific parameters
        op_params = {}
        
        if op_type == "filter_delete_rows":
            col1, col2, col3 = st.columns(3)
            with col1:
                op_params["column"] = st.selectbox("Column", columns, key="filter_col")
            with col2:
                op_params["condition"] = st.selectbox(
                    "Condition",
                    ["equals", "not_equals", "contains", "not_contains", "empty", "not_empty", "greater_than", "less_than"],
                    key="filter_cond"
                )
            with col3:
                op_params["action"] = st.selectbox("Action", ["delete", "keep"], key="filter_action")
            
            if op_params["condition"] not in ["empty", "not_empty"]:
                op_params["value"] = st.text_input("Value", key="filter_value")
        
        elif op_type == "deduplicate":
            op_params["columns"] = st.multiselect("Columns to check", columns, key="dedup_cols")
            op_params["keep"] = st.selectbox("Keep", ["first", "last"], key="dedup_keep")
        
        elif op_type == "fill_nulls":
            op_params["column"] = st.selectbox("Column", columns, key="fill_col")
            op_params["strategy"] = st.selectbox(
                "Strategy",
                [s.value for s in FillStrategy],
                key="fill_strategy"
            )
            if op_params["strategy"] == "fixed_value":
                op_params["value"] = st.text_input("Fill Value", key="fill_value")
        
        elif op_type == "type_conversion":
            op_params["column"] = st.selectbox("Column", columns, key="convert_col")
            op_params["target_type"] = st.selectbox(
                "Target Type",
                [t.value for t in DataType],
                key="convert_type"
            )
            if op_params["target_type"] in ["date", "datetime"]:
                op_params["date_format"] = st.text_input("Date Format (e.g., %Y-%m-%d)", key="convert_format")
        
        elif op_type == "column_split":
            op_params["source_column"] = st.selectbox("Source Column", columns, key="split_col")
            op_params["delimiter"] = st.text_input("Delimiter", value=",", key="split_delim")
            new_column_names_input = st.text_input(
                "New Column Names (comma-separated)",
                key="split_names"
            )
            op_params["new_column_names"] = [name.strip() for name in new_column_names_input.split(",")] if new_column_names_input else []
            op_params["max_splits"] = st.number_input("Max Splits (-1 for unlimited)", value=-1, key="split_max")
        
        elif op_type == "column_merge":
            op_params["source_columns"] = st.multiselect("Source Columns", columns, key="merge_cols")
            op_params["target_column"] = st.text_input("Target Column Name", key="merge_target")
            op_params["delimiter"] = st.text_input("Delimiter", value=" ", key="merge_delim")
            op_params["delete_sources"] = st.checkbox("Delete source columns", key="merge_delete")
        
        # Description
        description = st.text_input("Operation Description (optional)", key="form_description")
        
        # Add operation button
        if st.button("➕ Add Operation to Plan"):
            try:
                operation_data = {
                    "type": op_type,
                    "file_alias": target_file,
                    "sheet_name": target_sheet,
                    "params": op_params,
                    "description": description or None
                }
                st.session_state.form_operations.append(operation_data)
                st.success(f"Operation added! Total: {len(st.session_state.form_operations)}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add operation: {str(e)}")
        
        # Show current operations
        if st.session_state.form_operations:
            st.markdown("**Current Operations:**")
            for i, op in enumerate(st.session_state.form_operations):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{i+1}. {op['type']} on {op['file_alias']}.{op['sheet_name']}")
                with col2:
                    if st.button("🗑️", key=f"remove_op_{i}"):
                        st.session_state.form_operations.pop(i)
                        st.rerun()
            
            # Build plan from operations
            if st.button("🔨 Build Plan from Operations"):
                build_plan_from_form()


def generate_plan_with_ai(instruction: str):
    """Generate plan using AI."""
    planner = PlanGenerator()
    
    if not planner.is_ai_available():
        st.warning("⚠️ DeepSeek API key not configured. Use the manual plan builder below.")
        return
    
    # Gather file metadata
    file_manager = FileManager(st.session_state.user["user_id"])
    file_metadata = {}
    
    for alias, file_id in st.session_state.files.items():
        file_path = file_manager.get_file_path(file_id)
        if file_path:
            metadata = file_manager.get_file_metadata(file_path)
            file_metadata[alias] = metadata
    
    with st.spinner("🤖 Generating plan with AI..."):
        result = planner.generate_plan_from_instruction(
            instruction,
            file_metadata,
            st.session_state.selection,
            st.session_state.active_file,
            st.session_state.active_sheet
        )
    
    if result["success"]:
        st.session_state.generated_plan = result["plan"]
        st.success("✅ Plan generated successfully!")
        st.rerun()
    else:
        st.error(f"❌ Plan generation failed: {result.get('error', 'Unknown error')}")
        if result.get("raw_response"):
            with st.expander("🔍 View raw AI response"):
                st.code(result["raw_response"])


def build_plan_from_form():
    """Build plan from manually added operations."""
    if not st.session_state.form_operations:
        st.warning("No operations added yet")
        return
    
    planner = PlanGenerator()
    
    with st.spinner("🔨 Building plan..."):
        result = planner.create_plan_from_form(st.session_state.form_operations)
    
    if result["success"]:
        st.session_state.generated_plan = result["plan"]
        st.session_state.form_operations = []  # Clear form operations
        st.success("✅ Plan created from form!")
        st.rerun()
    else:
        st.error(f"❌ Failed to create plan: {result.get('error', 'Unknown error')}")


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
    """Display execution section with new PlanExecutor."""
    st.markdown('<div class="sub-header">▶️ Execution</div>', unsafe_allow_html=True)
    
    if not st.session_state.generated_plan:
        st.info("Generate a plan first to execute operations")
        return
    
    st.markdown("**Ready to execute:**")
    st.write(f"📋 {len(st.session_state.generated_plan.operations)} operation(s) in the plan")
    
    if st.button("▶️ Execute Plan", key="execute_plan_button"):
        execute_plan()
    
    # Show results if available
    if st.session_state.execution_result:
        display_execution_results()


def execute_plan():
    """Execute the generated plan using PlanExecutor."""
    file_manager = FileManager(st.session_state.user["user_id"])
    executor = PlanExecutor()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Stage 1: Loading workbooks
        status_text.text("📖 Loading workbooks...")
        progress_bar.progress(0.2)
        
        # Load all workbooks referenced in the plan
        workbooks = {}
        file_aliases = set(op.target.file_alias for op in st.session_state.generated_plan.operations)
        
        for alias in file_aliases:
            if alias in st.session_state.files:
                file_id = st.session_state.files[alias]
                file_path = file_manager.get_file_path(file_id)
                if file_path:
                    workbooks[alias] = openpyxl.load_workbook(file_path)
        
        # Stage 2: Executing plan
        status_text.text("⚙️ Executing operations...")
        progress_bar.progress(0.4)
        
        result = executor.execute_plan(st.session_state.generated_plan, workbooks)
        
        # Stage 3: Saving results
        status_text.text("💾 Saving results...")
        progress_bar.progress(0.7)
        
        # Save modified workbooks
        saved_files = {}
        for alias, wb in workbooks.items():
            if alias in st.session_state.files:
                file_id = st.session_state.files[alias]
                new_revision = file_manager.save_modified_file(file_id, wb)
                saved_files[alias] = {"revision": new_revision, "file_id": file_id}
        
        # Stage 4: Complete
        status_text.text("✅ Complete!")
        progress_bar.progress(1.0)
        
        # Store result
        st.session_state.execution_result = {
            **result,
            "saved_files": saved_files
        }
        
        st.success(f"✅ Execution completed! {result['operations_completed']} operations performed.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Execution failed: {str(e)}")
        status_text.text("❌ Failed")
        progress_bar.progress(1.0)


def display_execution_results():
    """Display execution results with change summary, preview, and download."""
    result = st.session_state.execution_result
    file_manager = FileManager(st.session_state.user["user_id"])

    st.markdown("---")
    st.markdown("### 📊 Execution Results")

    saved_files = result.get("saved_files", {})

    # Use tabs: Summary | Preview | Download
    tab_summary, tab_preview, tab_download = st.tabs(["📋 Summary", "👁️ Preview", "⬇️ Download"])

    with tab_summary:
        summary = ChangeSummary.generate_summary(result)
        st.markdown(summary)

    with tab_preview:
        if not saved_files:
            st.info("No modified files to preview.")
        else:
            # One sub-tab per modified file
            file_aliases = list(saved_files.keys())
            if len(file_aliases) == 1:
                alias = file_aliases[0]
                _render_file_preview(alias, saved_files[alias], file_manager)
            else:
                file_tabs = st.tabs(file_aliases)
                for file_tab, alias in zip(file_tabs, file_aliases):
                    with file_tab:
                        _render_file_preview(alias, saved_files[alias], file_manager)

    with tab_download:
        if not saved_files:
            st.info("No files available for download.")
        else:
            for alias, file_info in saved_files.items():
                file_id = file_info["file_id"]
                revision = file_info["revision"]
                file_path = file_manager.get_file_path(file_id, revision)

                if file_path:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    st.download_button(
                        label=f"⬇️ Download {alias} (rev_{revision})",
                        data=file_bytes,
                        file_name=f"{alias}_result_rev{revision}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{alias}",
                    )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✔️ Accept Changes and Continue"):
            st.success("Changes accepted! You can continue working with the modified files.")
            st.session_state.execution_result = None
            st.rerun()

    with col2:
        if st.button("🔄 Start New Operation"):
            st.session_state.generated_plan = None
            st.session_state.execution_result = None
            st.session_state.original_instruction = ""
            st.session_state.optimized_instruction = ""
            st.rerun()


def _render_file_preview(alias: str, file_info: dict, file_manager: "FileManager"):
    """Render a sheet-selector and dataframe preview for one modified file."""
    file_id = file_info["file_id"]
    revision = file_info["revision"]
    file_path = file_manager.get_file_path(file_id, revision)

    if not file_path:
        st.warning(f"File {alias} (rev_{revision}) not found.")
        return

    sheet_names = file_manager.get_sheet_names(file_path)
    if not sheet_names:
        st.warning(f"No sheets found in {alias}.")
        return

    selected_sheet = st.selectbox(
        "Select sheet to preview",
        sheet_names,
        key=f"preview_sheet_{alias}",
    )

    try:
        # Read a full row-count using openpyxl (header row excluded), then
        # load up to 300 rows for display via pandas.
        with openpyxl.load_workbook(file_path, read_only=True, data_only=True) as _wb:
            total_rows = max(_wb[selected_sheet].max_row - 1, 0)  # subtract header

        df = file_manager.read_sheet_data(file_path, selected_sheet, max_rows=300)
        st.dataframe(df, use_container_width=True)
        st.caption(
            f"Showing first {len(df)} rows of {total_rows} total rows"
            f" × {len(df.columns)} columns"
        )
    except Exception as e:
        st.error(f"Error loading preview: {str(e)}")


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
    
    # Plan generation section
    plan_generation_section()
    
    st.markdown("---")
    
    # Execution section
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
