"""
Excel Helper - AI-Powered Excel Processing Tool
Main Streamlit Application
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from identity_system import IdentityRegistry, AccountProfile
from document_archive import DocumentArchive, DocumentRecord
from instruction_ai import InstructionOptimizer
from excel_processor import SpreadsheetProcessor


# Page configuration
st.set_page_config(
    page_title="Excel Helper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'account_profile' not in st.session_state:
    st.session_state.account_profile = None
if 'uploaded_documents' not in st.session_state:
    st.session_state.uploaded_documents = {}
if 'active_document_key' not in st.session_state:
    st.session_state.active_document_key = None
if 'active_worksheet' not in st.session_state:
    st.session_state.active_worksheet = None
if 'cell_selection' not in st.session_state:
    st.session_state.cell_selection = None
if 'raw_instruction' not in st.session_state:
    st.session_state.raw_instruction = ""
if 'optimized_instruction' not in st.session_state:
    st.session_state.optimized_instruction = ""
if 'execution_results' not in st.session_state:
    st.session_state.execution_results = {}

# Initialize managers
@st.cache_resource
def get_identity_registry():
    return IdentityRegistry()

@st.cache_resource
def get_document_archive():
    return DocumentArchive()

@st.cache_resource
def get_instruction_optimizer():
    try:
        return InstructionOptimizer()
    except ValueError:
        return None

@st.cache_resource
def get_spreadsheet_processor():
    return SpreadsheetProcessor()


def render_login_interface():
    """Display login interface."""
    st.title("📊 Excel Helper")
    st.markdown("### AI-Powered Excel Processing Tool")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("#### Login")
        
        login_name = st.text_input("Account Name", key="login_username")
        login_credential = st.text_input("Password", type="password", key="login_password")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Sign In", use_container_width=True):
                if login_name and login_credential:
                    registry = get_identity_registry()
                    profile = registry.verify_identity(login_name, login_credential)
                    
                    if profile:
                        st.session_state.authenticated = True
                        st.session_state.account_profile = profile
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please enter both account name and password")
        
        with col_b:
            if st.button("Create Account", use_container_width=True):
                if login_name and login_credential:
                    registry = get_identity_registry()
                    if registry.register_account(login_name, login_credential):
                        st.success("Account created! Please sign in.")
                    else:
                        st.error("Account name already exists")
                else:
                    st.warning("Please enter both account name and password")


def render_sidebar():
    """Display sidebar with user info and file list."""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.account_profile.account_name}")
        
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.account_profile = None
            st.session_state.uploaded_documents = {}
            st.session_state.active_document_key = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📁 Uploaded Files")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload Excel Files",
            type=['xlsx'],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files:
            process_uploaded_files(uploaded_files)
        
        # Display uploaded documents
        if st.session_state.uploaded_documents:
            for doc_key, doc_info in st.session_state.uploaded_documents.items():
                alias = doc_info['alias']
                filename = doc_info['filename']
                
                button_label = f"{alias}: {filename[:20]}..." if len(filename) > 20 else f"{alias}: {filename}"
                
                if st.button(button_label, key=f"btn_{doc_key}", use_container_width=True):
                    st.session_state.active_document_key = doc_key
                    st.session_state.active_worksheet = None
                    st.rerun()


def process_uploaded_files(uploaded_files):
    """Process newly uploaded files."""
    archive = get_document_archive()
    account_uid = st.session_state.account_profile.account_uid
    
    for uploaded_file in uploaded_files:
        # Generate document key
        doc_key = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Check if already processed
        if doc_key not in st.session_state.uploaded_documents:
            # Save to archive
            file_bytes = uploaded_file.read()
            record = archive.archive_new_document(
                account_uid,
                doc_key,
                uploaded_file.name,
                file_bytes
            )
            
            # Assign alias
            alias_number = len(st.session_state.uploaded_documents) + 1
            alias = f"F{alias_number}"
            
            st.session_state.uploaded_documents[doc_key] = {
                'alias': alias,
                'filename': uploaded_file.name,
                'record': record
            }
            
            st.success(f"Uploaded {uploaded_file.name} as {alias}")


def render_preview_area():
    """Display file preview area."""
    st.markdown("### 👁️ Preview")
    
    if not st.session_state.uploaded_documents:
        st.info("Upload Excel files to begin")
        return
    
    if not st.session_state.active_document_key:
        st.info("Select a file from the sidebar")
        return
    
    # Get active document
    doc_key = st.session_state.active_document_key
    doc_info = st.session_state.uploaded_documents[doc_key]
    
    st.markdown(f"**File:** {doc_info['alias']} - {doc_info['filename']}")
    
    # Get file path
    archive = get_document_archive()
    account_uid = st.session_state.account_profile.account_uid
    file_path = archive.locate_current_snapshot(account_uid, doc_key)
    
    if not file_path:
        st.error("File not found")
        return
    
    # Get worksheets
    worksheets = archive.retrieve_worksheet_names(file_path)
    
    # Worksheet selector
    if not st.session_state.active_worksheet or st.session_state.active_worksheet not in worksheets:
        st.session_state.active_worksheet = worksheets[0]
    
    selected_worksheet = st.selectbox(
        "Select Worksheet",
        worksheets,
        index=worksheets.index(st.session_state.active_worksheet),
        key="worksheet_selector"
    )
    st.session_state.active_worksheet = selected_worksheet
    
    # Load and display data
    max_rows = int(os.getenv("MAX_PREVIEW_ROWS", "300"))
    df = archive.extract_spreadsheet_data(file_path, selected_worksheet)
    df_preview = df.head(max_rows)
    
    st.markdown(f"*Showing {len(df_preview)} of {len(df)} rows*")
    
    # Display with AgGrid for interactivity
    grid_builder = GridOptionsBuilder.from_dataframe(df_preview)
    grid_builder.configure_selection(selection_mode='single', use_checkbox=False)
    grid_builder.configure_grid_options(enableRangeSelection=True)
    grid_options = grid_builder.build()
    
    grid_response = AgGrid(
        df_preview,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        height=400
    )
    
    # Handle selection
    if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
        selected_row_data = grid_response['selected_rows'][0]
        row_index = df_preview[df_preview.eq(selected_row_data).all(axis=1)].index[0]
        
        st.session_state.cell_selection = {
            'file_alias': doc_info['alias'],
            'sheet_name': selected_worksheet,
            'selection_type': 'row',
            'selection_ref': f"Row {row_index + 1}"
        }
        
        st.info(f"Selected: {doc_info['alias']} - {selected_worksheet} - Row {row_index + 1}")


def render_instruction_area():
    """Display instruction input and optimization area."""
    st.markdown("### 📝 Instructions")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.text_area(
            "Original Instruction",
            value=st.session_state.raw_instruction,
            key="raw_instruction_input",
            height=100,
            help="Describe what you want to do with the Excel file(s)"
        )
        st.session_state.raw_instruction = st.session_state.raw_instruction_input
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Optimize Instruction", use_container_width=True):
            optimize_instruction()
    
    st.text_area(
        "Optimized Instruction (AI-Enhanced)",
        value=st.session_state.optimized_instruction,
        key="optimized_instruction_input",
        height=120,
        help="AI-optimized instruction (you can edit this)"
    )
    st.session_state.optimized_instruction = st.session_state.optimized_instruction_input


def optimize_instruction():
    """Optimize instruction using AI."""
    optimizer = get_instruction_optimizer()
    
    if not optimizer:
        st.error("DeepSeek API not configured. Please set DEEPSEEK_API_KEY in environment.")
        return
    
    if not st.session_state.raw_instruction.strip():
        st.warning("Please enter an instruction first")
        return
    
    with st.spinner("Optimizing instruction..."):
        # Prepare context
        context_info = {
            'selected_cells': st.session_state.cell_selection,
            'available_files': []
        }
        
        # Add file information
        archive = get_document_archive()
        account_uid = st.session_state.account_profile.account_uid
        
        for doc_key, doc_info in st.session_state.uploaded_documents.items():
            file_path = archive.locate_current_snapshot(account_uid, doc_key)
            if file_path:
                worksheets = archive.retrieve_worksheet_names(file_path)
                df = archive.extract_spreadsheet_data(file_path, worksheets[0])
                
                context_info['available_files'].append({
                    'alias': doc_info['alias'],
                    'filename': doc_info['filename'],
                    'sheets': worksheets,
                    'column_sample': df.columns.tolist()[:10]
                })
        
        # Optimize
        optimized = optimizer.optimize_instruction(
            st.session_state.raw_instruction,
            context_info
        )
        
        st.session_state.optimized_instruction = optimized
        st.success("Instruction optimized!")
        st.rerun()


def render_execution_area():
    """Display execution controls and results."""
    st.markdown("### ⚙️ Execution")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("▶️ Execute Instruction", use_container_width=True):
            execute_instruction()
    
    # Display results
    if st.session_state.execution_results:
        st.markdown("#### Results")
        
        for doc_key, result_data in st.session_state.execution_results.items():
            doc_info = st.session_state.uploaded_documents[doc_key]
            
            with st.expander(f"📄 {doc_info['alias']} - {doc_info['filename']}", expanded=True):
                st.markdown(f"**Status:** {result_data.get('status', 'Completed')}")
                st.markdown(f"**Description:** {result_data.get('description', 'N/A')}")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    # Download button
                    st.download_button(
                        label="⬇️ Download Result",
                        data=result_data['file_bytes'],
                        file_name=f"modified_{doc_info['filename']}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_b:
                    # Accept and continue button
                    if st.button(f"✅ Accept & Continue", key=f"accept_{doc_key}", use_container_width=True):
                        accept_changes(doc_key, result_data['file_bytes'])


def execute_instruction():
    """Execute the instruction on files."""
    instruction_to_use = st.session_state.optimized_instruction.strip() or st.session_state.raw_instruction.strip()
    
    if not instruction_to_use:
        st.warning("Please enter an instruction")
        return
    
    if not st.session_state.uploaded_documents:
        st.warning("Please upload files first")
        return
    
    processor = get_spreadsheet_processor()
    archive = get_document_archive()
    account_uid = st.session_state.account_profile.account_uid
    
    st.session_state.execution_results = {}
    
    progress_container = st.container()
    
    with progress_container:
        st.info("⏳ Reading files...")
        
        for doc_key, doc_info in st.session_state.uploaded_documents.items():
            file_path = archive.locate_current_snapshot(account_uid, doc_key)
            
            if file_path:
                try:
                    st.info(f"⏳ Processing {doc_info['alias']}...")
                    
                    # Execute
                    output_buffer, summary = processor.execute_on_file(file_path, instruction_to_use)
                    
                    st.session_state.execution_results[doc_key] = {
                        'status': 'Success',
                        'description': summary,
                        'file_bytes': output_buffer.getvalue()
                    }
                    
                    st.success(f"✅ Completed {doc_info['alias']}")
                    
                except Exception as e:
                    st.error(f"Error processing {doc_info['alias']}: {str(e)}")
                    st.session_state.execution_results[doc_key] = {
                        'status': 'Error',
                        'description': str(e),
                        'file_bytes': None
                    }
    
    st.rerun()


def accept_changes(doc_key: str, file_bytes: bytes):
    """Accept changes and create new revision."""
    archive = get_document_archive()
    account_uid = st.session_state.account_profile.account_uid
    doc_info = st.session_state.uploaded_documents[doc_key]
    
    try:
        # Create new snapshot
        new_snap_num = archive.capture_new_snapshot(
            account_uid,
            doc_key,
            file_bytes,
            f"Executed: {st.session_state.optimized_instruction[:50]}"
        )
        
        # Activate new snapshot
        archive.activate_snapshot(account_uid, doc_key, new_snap_num)
        
        # Clear execution results
        if doc_key in st.session_state.execution_results:
            del st.session_state.execution_results[doc_key]
        
        st.success(f"Changes accepted for {doc_info['alias']}. New version is now active.")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error accepting changes: {str(e)}")


def render_main_application():
    """Render the main application interface."""
    render_sidebar()
    
    # Main content area
    st.title("📊 Excel Helper")
    st.markdown("*AI-Powered Excel Processing Tool*")
    
    # Create layout
    preview_col, instruction_col = st.columns([1, 1])
    
    with preview_col:
        render_preview_area()
    
    with instruction_col:
        render_instruction_area()
    
    # Execution area (full width)
    render_execution_area()


def main():
    """Main application entry point."""
    if not st.session_state.authenticated:
        render_login_interface()
    else:
        render_main_application()


if __name__ == "__main__":
    main()
