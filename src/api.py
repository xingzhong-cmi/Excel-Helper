"""
API integration module for DeepSeek LLM.
"""
import os
import requests
from typing import Dict, Optional


class DeepSeekAPI:
    """Integration with DeepSeek API for instruction optimization."""
    
    def __init__(self):
        """Initialize the API client."""
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
    
    def is_configured(self) -> bool:
        """Check if the API is properly configured.
        
        Returns:
            True if API key is configured, False otherwise
        """
        return bool(self.api_key)
    
    def optimize_instruction(self, original_instruction: str, selection: Optional[Dict],
                           file_metadata: Dict) -> Dict[str, any]:
        """Optimize an instruction using the DeepSeek API.
        
        Args:
            original_instruction: Original user instruction
            selection: Currently selected cells/rows/columns (if any)
            file_metadata: Metadata about the files (aliases, sheets, columns)
            
        Returns:
            Dictionary with optimized instruction and metadata
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "API key not configured",
                "optimized_instruction": ""
            }
        
        # Build the prompt
        prompt = self._build_optimization_prompt(
            original_instruction, selection, file_metadata
        )
        
        try:
            response = self._call_api(prompt)
            
            if response["success"]:
                return {
                    "success": True,
                    "optimized_instruction": response["content"],
                    "usage": response.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error"),
                    "optimized_instruction": ""
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"API call failed: {str(e)}",
                "optimized_instruction": ""
            }
    
    def _build_optimization_prompt(self, instruction: str, selection: Optional[Dict],
                                   file_metadata: Dict) -> str:
        """Build the prompt for instruction optimization.
        
        Args:
            instruction: Original instruction
            selection: Selection information
            file_metadata: File metadata
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are an Excel operation assistant. Your task is to optimize user instructions into clear, executable operations.",
            "",
            "Available files and their metadata:"
        ]
        
        # Add file information
        for file_alias, metadata in file_metadata.items():
            prompt_parts.append(f"\n{file_alias}:")
            prompt_parts.append(f"  Sheets: {', '.join(metadata.get('sheets', []))}")
            
            columns = metadata.get('columns', {})
            for sheet_name, cols in list(columns.items())[:3]:  # Limit to first 3 sheets
                if cols:
                    prompt_parts.append(f"  {sheet_name} columns: {', '.join(cols[:10])}")
        
        # Add selection information
        if selection:
            prompt_parts.append(f"\nCurrent selection:")
            prompt_parts.append(f"  File: {selection.get('file_alias', 'N/A')}")
            prompt_parts.append(f"  Sheet: {selection.get('sheet', 'N/A')}")
            if selection.get('cells'):
                prompt_parts.append(f"  Cells: {selection['cells']}")
            if selection.get('columns'):
                prompt_parts.append(f"  Columns: {', '.join(selection['columns'])}")
        
        prompt_parts.extend([
            "",
            "User instruction:",
            instruction,
            "",
            "Please provide an optimized, executable instruction that:",
            "1. Uses file aliases (F1, F2, etc.) to reference specific files",
            "2. Specifies sheet names when needed",
            "3. Clearly defines the operations to perform",
            "4. Is structured and unambiguous",
            "5. Can be executed safely on Excel files",
            "",
            "Return only the optimized instruction without explanation."
        ])
        
        return "\n".join(prompt_parts)
    
    def _call_api(self, prompt: str) -> Dict:
        """Call the DeepSeek API.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Dictionary with response data
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}: {response.text}"
                }
        
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
