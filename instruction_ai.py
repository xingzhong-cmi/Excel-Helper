"""
AI-powered instruction optimization using DeepSeek API.
"""
import os
import json
import time
from typing import Dict, List, Optional
from openai import OpenAI


class InstructionOptimizer:
    """Optimizes natural language instructions for Excel processing."""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_endpoint = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout_duration = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not configured")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_endpoint
        )
    
    def _construct_optimization_prompt(self, raw_instruction: str, 
                                      context_data: Dict) -> str:
        """Build comprehensive prompt for instruction optimization."""
        prompt_sections = []
        
        prompt_sections.append("You are an Excel processing assistant. Transform the user's instruction into a clear, executable, and reproducible operation description.")
        prompt_sections.append("\n## User's Original Instruction:")
        prompt_sections.append(raw_instruction)
        
        if context_data.get("selected_cells"):
            prompt_sections.append("\n## User Selected:")
            selection_info = context_data["selected_cells"]
            prompt_sections.append(f"- File: {selection_info.get('file_alias')}")
            prompt_sections.append(f"- Sheet: {selection_info.get('sheet_name')}")
            prompt_sections.append(f"- Selection Type: {selection_info.get('selection_type')}")
            prompt_sections.append(f"- Selection: {selection_info.get('selection_ref')}")
        
        if context_data.get("available_files"):
            prompt_sections.append("\n## Available Files:")
            for file_info in context_data["available_files"]:
                file_alias = file_info.get("alias")
                origin_name = file_info.get("filename")
                sheets = file_info.get("sheets", [])
                prompt_sections.append(f"- {file_alias}: {origin_name}")
                prompt_sections.append(f"  Worksheets: {', '.join(sheets)}")
                
                if file_info.get("column_sample"):
                    prompt_sections.append(f"  Columns: {', '.join(file_info['column_sample'])}")
        
        prompt_sections.append("\n## Task:")
        prompt_sections.append("Rewrite the instruction to be:")
        prompt_sections.append("1. Specific about which file(s) to operate on (use file aliases like F1, F2)")
        prompt_sections.append("2. Clear about which worksheets and columns/rows to target")
        prompt_sections.append("3. Precise about the operation to perform")
        prompt_sections.append("4. Reproducible - someone else should understand exactly what to do")
        prompt_sections.append("\nProvide ONLY the optimized instruction, no explanations.")
        
        return "\n".join(prompt_sections)
    
    def optimize_instruction(self, raw_instruction: str, 
                           context_data: Optional[Dict] = None,
                           retry_attempts: int = 3) -> str:
        """Transform user instruction into optimized, executable form."""
        if not raw_instruction or not raw_instruction.strip():
            return ""
        
        context_data = context_data or {}
        
        optimization_prompt = self._construct_optimization_prompt(
            raw_instruction, 
            context_data
        )
        
        for attempt_number in range(retry_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert at understanding and clarifying Excel processing instructions."},
                        {"role": "user", "content": optimization_prompt}
                    ],
                    temperature=0.3,
                    timeout=self.timeout_duration
                )
                
                optimized_text = response.choices[0].message.content.strip()
                return optimized_text
                
            except Exception as error:
                if attempt_number == retry_attempts - 1:
                    # Final attempt failed, return original with note
                    return f"[API unavailable] {raw_instruction}"
                time.sleep(2 ** attempt_number)  # Exponential backoff
        
        return raw_instruction
    
    def check_api_availability(self) -> bool:
        """Verify API connectivity and credentials."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                timeout=10
            )
            return True
        except Exception:
            return False
