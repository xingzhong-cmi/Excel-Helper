"""
Document archive and versioning system with custom implementation.
"""
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
from dataclasses import dataclass, asdict
from io import BytesIO


@dataclass
class DocumentSnapshot:
    """Represents a versioned snapshot of a document."""
    snapshot_number: int
    captured_at: str
    note: str
    storage_filename: str


@dataclass
class DocumentRecord:
    """Metadata record for a managed document."""
    document_key: str
    origin_filename: str
    registered_at: str
    current_snapshot: int
    snapshot_history: List[Dict]


class DocumentArchive:
    """Manages document storage with version control capabilities."""
    
    def __init__(self, archive_root: str = "data"):
        self.archive_base = Path(archive_root)
        self.archive_base.mkdir(parents=True, exist_ok=True)
    
    def _get_account_archive(self, account_uid: str) -> Path:
        """Retrieve archive directory for specific account."""
        account_dir = self.archive_base / account_uid
        account_dir.mkdir(parents=True, exist_ok=True)
        return account_dir
    
    def _get_document_container(self, account_uid: str, document_key: str) -> Path:
        """Retrieve container directory for specific document."""
        doc_container = self._get_account_archive(account_uid) / document_key
        doc_container.mkdir(parents=True, exist_ok=True)
        return doc_container
    
    def archive_new_document(self, account_uid: str, document_key: str, 
                            origin_name: str, binary_content: bytes) -> DocumentRecord:
        """Archive new document and establish initial snapshot."""
        doc_container = self._get_document_container(account_uid, document_key)
        
        # Establish document record
        timestamp_now = datetime.now().isoformat()
        doc_record = DocumentRecord(
            document_key=document_key,
            origin_filename=origin_name,
            registered_at=timestamp_now,
            current_snapshot=0,
            snapshot_history=[]
        )
        
        # Create initial snapshot
        snapshot_file = doc_container / "snap_0000.xlsx"
        snapshot_file.write_bytes(binary_content)
        
        # Record snapshot in history
        initial_snapshot = DocumentSnapshot(
            snapshot_number=0,
            captured_at=timestamp_now,
            note="Original upload",
            storage_filename="snap_0000.xlsx"
        )
        doc_record.snapshot_history.append(asdict(initial_snapshot))
        
        # Persist metadata
        metadata_file = doc_container / "record.json"
        metadata_file.write_text(json.dumps(asdict(doc_record), indent=2))
        
        return doc_record
    
    def fetch_document_record(self, account_uid: str, document_key: str) -> Optional[DocumentRecord]:
        """Retrieve document metadata record."""
        metadata_path = self._get_document_container(account_uid, document_key) / "record.json"
        if not metadata_path.exists():
            return None
        
        record_data = json.loads(metadata_path.read_text())
        return DocumentRecord(**record_data)
    
    def persist_document_record(self, account_uid: str, document_key: str, record: DocumentRecord):
        """Save updated document metadata."""
        metadata_path = self._get_document_container(account_uid, document_key) / "record.json"
        metadata_path.write_text(json.dumps(asdict(record), indent=2))
    
    def locate_current_snapshot(self, account_uid: str, document_key: str) -> Optional[Path]:
        """Get path to currently active document snapshot."""
        record = self.fetch_document_record(account_uid, document_key)
        if not record:
            return None
        
        current_snap_num = record.current_snapshot
        snap_filename = f"snap_{current_snap_num:04d}.xlsx"
        snap_path = self._get_document_container(account_uid, document_key) / snap_filename
        return snap_path if snap_path.exists() else None
    
    def capture_new_snapshot(self, account_uid: str, document_key: str, 
                            binary_content: bytes, description: str = "") -> int:
        """Create new versioned snapshot of document."""
        record = self.fetch_document_record(account_uid, document_key)
        if not record:
            raise ValueError(f"Document {document_key} not registered in archive")
        
        # Calculate next snapshot number
        next_snap_num = len(record.snapshot_history)
        
        # Write snapshot file
        snap_filename = f"snap_{next_snap_num:04d}.xlsx"
        snap_path = self._get_document_container(account_uid, document_key) / snap_filename
        snap_path.write_bytes(binary_content)
        
        # Add to history
        new_snapshot = DocumentSnapshot(
            snapshot_number=next_snap_num,
            captured_at=datetime.now().isoformat(),
            note=description or f"Snapshot {next_snap_num}",
            storage_filename=snap_filename
        )
        record.snapshot_history.append(asdict(new_snapshot))
        
        # Prune old snapshots if limit exceeded
        retention_limit = int(os.getenv("MAX_REVISIONS", "10"))
        if len(record.snapshot_history) > retention_limit:
            # Remove oldest snapshots
            snapshots_to_prune = record.snapshot_history[:-retention_limit]
            for old_snap in snapshots_to_prune:
                old_path = self._get_document_container(account_uid, document_key) / old_snap["storage_filename"]
                if old_path.exists():
                    old_path.unlink()
            record.snapshot_history = record.snapshot_history[-retention_limit:]
        
        # Update record
        self.persist_document_record(account_uid, document_key, record)
        
        return next_snap_num
    
    def activate_snapshot(self, account_uid: str, document_key: str, snapshot_number: int):
        """Set specific snapshot as currently active version."""
        record = self.fetch_document_record(account_uid, document_key)
        if not record:
            raise ValueError(f"Document {document_key} not found")
        
        if not any(s["snapshot_number"] == snapshot_number for s in record.snapshot_history):
            raise ValueError(f"Snapshot {snapshot_number} does not exist")
        
        record.current_snapshot = snapshot_number
        self.persist_document_record(account_uid, document_key, record)
    
    def locate_specific_snapshot(self, account_uid: str, document_key: str, 
                                 snapshot_number: int) -> Optional[Path]:
        """Get path to specific snapshot by number."""
        snap_filename = f"snap_{snapshot_number:04d}.xlsx"
        snap_path = self._get_document_container(account_uid, document_key) / snap_filename
        return snap_path if snap_path.exists() else None
    
    def enumerate_account_documents(self, account_uid: str) -> List[DocumentRecord]:
        """List all documents belonging to account."""
        account_archive = self._get_account_archive(account_uid)
        documents = []
        
        for doc_dir in account_archive.iterdir():
            if doc_dir.is_dir():
                record_path = doc_dir / "record.json"
                if record_path.exists():
                    record_data = json.loads(record_path.read_text())
                    documents.append(DocumentRecord(**record_data))
        
        return documents
    
    def extract_spreadsheet_data(self, file_location: Path, 
                                 worksheet_name: Optional[str] = None) -> pd.DataFrame:
        """Load spreadsheet data into DataFrame."""
        return pd.read_excel(file_location, sheet_name=worksheet_name)
    
    def retrieve_worksheet_names(self, file_location: Path) -> List[str]:
        """Get list of worksheet names from spreadsheet."""
        excel_document = pd.ExcelFile(file_location)
        return excel_document.sheet_names
