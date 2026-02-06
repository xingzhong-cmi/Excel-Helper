"""
Custom identity verification system with unique implementation.
"""
import os
import json
import bcrypt
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass, asdict


@dataclass
class AccountProfile:
    """Represents a user account profile."""
    account_name: str
    account_uid: str
    admin_privileges: bool = False


class IdentityRegistry:
    """Custom registry for managing account identities and credentials."""
    
    def __init__(self, registry_location: str = "data/identity_vault.json"):
        self.vault_path = Path(registry_location)
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        self._bootstrap_vault()
        self._create_initial_account()
    
    def _bootstrap_vault(self):
        """Initialize the identity vault if absent."""
        if not self.vault_path.exists():
            self.vault_path.write_text(json.dumps({"accounts": {}}))
    
    def _create_initial_account(self):
        """Generate initial administrator account when vault is empty."""
        vault_data = self._read_vault()
        if not vault_data["accounts"]:
            initial_name = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            initial_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
            self.register_account(initial_name, initial_pass, admin_mode=True)
    
    def _read_vault(self) -> Dict:
        """Retrieve all account data from vault."""
        try:
            return json.loads(self.vault_path.read_text())
        except Exception:
            return {"accounts": {}}
    
    def _persist_vault(self, vault_data: Dict):
        """Write account data back to vault."""
        self.vault_path.write_text(json.dumps(vault_data, indent=2))
    
    def _digest_credential(self, raw_credential: str) -> str:
        """Create cryptographic digest of credential."""
        salt_rounds = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(raw_credential.encode('utf-8'), salt_rounds).decode('utf-8')
    
    def _validate_credential(self, raw_credential: str, stored_digest: str) -> bool:
        """Check if raw credential matches stored digest."""
        try:
            return bcrypt.checkpw(raw_credential.encode('utf-8'), stored_digest.encode('utf-8'))
        except Exception:
            return False
    
    def verify_identity(self, account_name: str, credential: str) -> Optional[AccountProfile]:
        """Verify account identity and return profile on success."""
        vault_data = self._read_vault()
        if account_name not in vault_data["accounts"]:
            return None
        
        account_record = vault_data["accounts"][account_name]
        if self._validate_credential(credential, account_record["credential_digest"]):
            return AccountProfile(
                account_name=account_name,
                account_uid=account_record["account_uid"],
                admin_privileges=account_record.get("admin_privileges", False)
            )
        return None
    
    def register_account(self, account_name: str, credential: str, admin_mode: bool = False) -> bool:
        """Register new account in the identity registry."""
        vault_data = self._read_vault()
        if account_name in vault_data["accounts"]:
            return False
        
        account_uid = f"uid_{len(vault_data['accounts']) + 1:04d}"
        vault_data["accounts"][account_name] = {
            "account_uid": account_uid,
            "credential_digest": self._digest_credential(credential),
            "admin_privileges": admin_mode
        }
        self._persist_vault(vault_data)
        
        # Establish isolated workspace for account
        workspace_root = Path(os.getenv("DATA_DIR", "data"))
        account_workspace = workspace_root / account_uid
        account_workspace.mkdir(parents=True, exist_ok=True)
        
        return True
    
    def enumerate_accounts(self):
        """List all registered account names."""
        vault_data = self._read_vault()
        return list(vault_data["accounts"].keys())
    
    def revoke_account(self, account_name: str) -> bool:
        """Remove account from registry."""
        vault_data = self._read_vault()
        if account_name in vault_data["accounts"]:
            del vault_data["accounts"][account_name]
            self._persist_vault(vault_data)
            return True
        return False
