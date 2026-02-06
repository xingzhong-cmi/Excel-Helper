"""
Planner module for generating execution plans from natural language instructions.
Supports both AI-powered (DeepSeek) and form-based plan generation.
"""
import json
import requests
import os
from typing import Dict, Any, Optional, List
from .plan import ExecutionPlan, Operation, OperationType, TargetSpec
from .plan import (
    FilterDeleteRowsParams, DeduplicateParams, FillNullsParams,
    TypeConversionParams, ColumnSplitParams, ColumnMergeParams,
    FillStrategy, DataType
)


class PlanGenerator:
    """Generates execution plans from instructions and metadata."""
    
    def __init__(self):
        """Initialize the plan generator."""
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
    
    def is_ai_available(self) -> bool:
        """Check if AI (DeepSeek) is available."""
        return bool(self.api_key)
    
    def generate_plan_from_instruction(
        self,
        instruction: str,
        file_metadata: Dict[str, Dict[str, Any]],
        selection: Optional[Dict[str, Any]] = None,
        active_file: Optional[str] = None,
        active_sheet: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate an execution plan from natural language instruction.
        
        Args:
            instruction: Natural language instruction
            file_metadata: Metadata about available files
            selection: Current selection info
            active_file: Currently active file alias
            active_sheet: Currently active sheet name
            
        Returns:
            Dict with 'success', 'plan' (ExecutionPlan or None), 'error', 'method'
        """
        if not instruction.strip():
            return {
                "success": False,
                "plan": None,
                "error": "Instruction cannot be empty",
                "method": "none"
            }
        
        # Try AI-powered generation first if available
        if self.is_ai_available():
            result = self._generate_with_ai(instruction, file_metadata, selection, active_file, active_sheet)
            if result["success"]:
                return result
            # If AI fails, will fall through to suggest form-based approach
        
        # If no AI or AI failed, return guidance for form-based generation
        return {
            "success": False,
            "plan": None,
            "error": "AI not available or failed. Please use the form-based plan builder below.",
            "method": "none",
            "suggestion": "Use the operation forms to build your plan step by step."
        }
    
    def _generate_with_ai(
        self,
        instruction: str,
        file_metadata: Dict[str, Dict[str, Any]],
        selection: Optional[Dict[str, Any]],
        active_file: Optional[str],
        active_sheet: Optional[str]
    ) -> Dict[str, Any]:
        """Generate plan using DeepSeek AI.
        
        Returns:
            Dict with 'success', 'plan', 'error', 'method'
        """
        prompt = self._build_ai_prompt(instruction, file_metadata, selection, active_file, active_sheet)
        
        try:
            response = self._call_deepseek_api(prompt)
            
            if not response["success"]:
                return {
                    "success": False,
                    "plan": None,
                    "error": response.get("error", "AI API call failed"),
                    "method": "ai_failed"
                }
            
            # Parse JSON response
            plan_json = response["content"]
            
            # Try to extract JSON if it's wrapped in markdown code blocks
            if "```json" in plan_json:
                plan_json = plan_json.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_json:
                plan_json = plan_json.split("```")[1].split("```")[0].strip()
            
            # Parse and validate plan
            try:
                plan = ExecutionPlan.parse_raw(plan_json)
                
                # Validate targets exist
                validation_errors = plan.validate_targets(file_metadata)
                if validation_errors:
                    return {
                        "success": False,
                        "plan": None,
                        "error": "Plan validation failed: " + "; ".join(validation_errors),
                        "method": "ai",
                        "raw_plan": plan_json
                    }
                
                return {
                    "success": True,
                    "plan": plan,
                    "error": None,
                    "method": "ai",
                    "usage": response.get("usage", {})
                }
            
            except Exception as e:
                return {
                    "success": False,
                    "plan": None,
                    "error": f"Failed to parse AI response as valid plan: {str(e)}",
                    "method": "ai_parse_failed",
                    "raw_response": plan_json
                }
        
        except Exception as e:
            return {
                "success": False,
                "plan": None,
                "error": f"AI generation error: {str(e)}",
                "method": "ai_failed"
            }
    
    def _build_ai_prompt(
        self,
        instruction: str,
        file_metadata: Dict[str, Dict[str, Any]],
        selection: Optional[Dict[str, Any]],
        active_file: Optional[str],
        active_sheet: Optional[str]
    ) -> str:
        """Build prompt for AI plan generation."""
        prompt_parts = [
            "You are an Excel automation assistant. Generate a JSON execution plan for the following instruction.",
            "",
            "IMPORTANT: Return ONLY valid JSON matching the ExecutionPlan schema. No explanation, no markdown, just JSON.",
            "",
            "Available operation types:",
            "- filter_delete_rows: Delete or keep rows based on conditions",
            "- deduplicate: Remove duplicate rows",
            "- fill_nulls: Fill empty cells",
            "- type_conversion: Convert column data types",
            "- column_split: Split a column by delimiter",
            "- column_merge: Merge multiple columns",
            "",
            "Schema example:",
            json.dumps({
                "description": "Brief description of the plan",
                "operations": [{
                    "type": "deduplicate",
                    "target": {"file_alias": "F1", "sheet_name": "Sheet1"},
                    "params": {"columns": ["ID"], "keep": "first"},
                    "description": "Remove duplicate IDs"
                }]
            }, indent=2),
            "",
            "Available files and sheets:"
        ]
        
        # Add file metadata
        for file_alias, metadata in file_metadata.items():
            prompt_parts.append(f"\n{file_alias}:")
            prompt_parts.append(f"  Sheets: {', '.join(metadata.get('sheets', []))}")
            
            columns = metadata.get('columns', {})
            for sheet_name, cols in list(columns.items())[:2]:
                if cols:
                    prompt_parts.append(f"  {sheet_name} columns: {', '.join(cols[:20])}")
        
        # Add context
        if active_file and active_sheet:
            prompt_parts.append(f"\nCurrent context: {active_file}.{active_sheet}")
        
        if selection:
            prompt_parts.append(f"\nCurrent selection: {json.dumps(selection, indent=2)}")
        
        prompt_parts.extend([
            "",
            "User instruction:",
            instruction,
            "",
            "Generate the JSON execution plan now:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _call_deepseek_api(self, prompt: str) -> Dict[str, Any]:
        """Call DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an Excel automation assistant. Generate only valid JSON execution plans. Never include explanations or markdown formatting."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000
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
                    "content": data["choices"][0]["message"]["content"].strip(),
                    "usage": data.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}: {response.text}"
                }
        
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def create_plan_from_form(self, operations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a plan from form-based operation data.
        
        Args:
            operations_data: List of operation dicts from form inputs
            
        Returns:
            Dict with 'success', 'plan', 'error'
        """
        try:
            operations = []
            
            for op_data in operations_data:
                op_type = OperationType(op_data["type"])
                target = TargetSpec(
                    file_alias=op_data["file_alias"],
                    sheet_name=op_data["sheet_name"]
                )
                
                # Create params based on operation type
                if op_type == OperationType.FILTER_DELETE_ROWS:
                    params = FilterDeleteRowsParams(**op_data["params"])
                elif op_type == OperationType.DEDUPLICATE:
                    params = DeduplicateParams(**op_data["params"])
                elif op_type == OperationType.FILL_NULLS:
                    params = FillNullsParams(**op_data["params"])
                elif op_type == OperationType.TYPE_CONVERSION:
                    params = TypeConversionParams(**op_data["params"])
                elif op_type == OperationType.COLUMN_SPLIT:
                    params = ColumnSplitParams(**op_data["params"])
                elif op_type == OperationType.COLUMN_MERGE:
                    params = ColumnMergeParams(**op_data["params"])
                else:
                    return {
                        "success": False,
                        "plan": None,
                        "error": f"Unsupported operation type: {op_type}"
                    }
                
                operation = Operation(
                    type=op_type,
                    target=target,
                    params=params,
                    description=op_data.get("description")
                )
                operations.append(operation)
            
            plan = ExecutionPlan(
                operations=operations,
                description=f"Plan with {len(operations)} operation(s)"
            )
            
            return {
                "success": True,
                "plan": plan,
                "error": None,
                "method": "form"
            }
        
        except Exception as e:
            return {
                "success": False,
                "plan": None,
                "error": f"Failed to create plan from form: {str(e)}",
                "method": "form"
            }
