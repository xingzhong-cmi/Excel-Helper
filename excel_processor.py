"""
Excel processing engine with instruction execution.
"""
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from io import BytesIO
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows


class SpreadsheetProcessor:
    """Processes Excel files based on natural language instructions."""
    
    def __init__(self):
        self.operation_handlers = {
            'filter': self._handle_filter_operation,
            'sort': self._handle_sort_operation,
            'calculate': self._handle_calculate_operation,
            'delete': self._handle_delete_operation,
            'modify': self._handle_modify_operation,
            'merge': self._handle_merge_operation,
        }
    
    def parse_instruction(self, instruction_text: str) -> Dict:
        """Extract operation details from instruction."""
        instruction_lower = instruction_text.lower()
        
        # Detect file references (F1, F2, etc.)
        file_pattern = r'\b(f\d+)\b'
        file_matches = re.findall(file_pattern, instruction_lower, re.IGNORECASE)
        
        # Detect operation type
        operation_type = 'modify'  # default
        if any(keyword in instruction_lower for keyword in ['filter', 'where', 'matching']):
            operation_type = 'filter'
        elif any(keyword in instruction_lower for keyword in ['sort', 'order by', 'arrange']):
            operation_type = 'sort'
        elif any(keyword in instruction_lower for keyword in ['calculate', 'sum', 'average', 'count']):
            operation_type = 'calculate'
        elif any(keyword in instruction_lower for keyword in ['delete', 'remove', 'drop']):
            operation_type = 'delete'
        elif any(keyword in instruction_lower for keyword in ['merge', 'join', 'combine']):
            operation_type = 'merge'
        
        # Extract column references
        column_pattern = r'\bcolumn[s]?\s+([A-Z]+(?:\s*,\s*[A-Z]+)*)\b'
        column_matches = re.findall(column_pattern, instruction_text, re.IGNORECASE)
        
        return {
            'operation_type': operation_type,
            'target_files': list(set([f.upper() for f in file_matches])),
            'target_columns': column_matches,
            'raw_instruction': instruction_text
        }
    
    def _handle_filter_operation(self, dataframe: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Apply filtering operation to dataframe."""
        instruction = params.get('raw_instruction', '')
        
        # Extract filter conditions (simplified)
        if '>' in instruction:
            parts = instruction.split('>')
            if len(parts) >= 2:
                column_name = parts[0].strip().split()[-1]
                try:
                    threshold = float(re.findall(r'\d+', parts[1])[0])
                    if column_name in dataframe.columns:
                        return dataframe[dataframe[column_name] > threshold]
                except:
                    pass
        
        return dataframe
    
    def _handle_sort_operation(self, dataframe: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Apply sorting operation to dataframe."""
        instruction = params.get('raw_instruction', '')
        
        # Extract sort column
        for column in dataframe.columns:
            if column.lower() in instruction.lower():
                ascending = 'descending' not in instruction.lower() and 'desc' not in instruction.lower()
                return dataframe.sort_values(by=column, ascending=ascending)
        
        return dataframe
    
    def _handle_calculate_operation(self, dataframe: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Apply calculation operation to dataframe."""
        instruction = params.get('raw_instruction', '').lower()
        
        # Add calculated column (simplified example)
        if 'sum' in instruction:
            numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                dataframe['calculated_sum'] = dataframe[numeric_cols[0]] + dataframe[numeric_cols[1]]
        
        return dataframe
    
    def _handle_delete_operation(self, dataframe: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Apply deletion operation to dataframe."""
        instruction = params.get('raw_instruction', '').lower()
        
        # Delete columns or rows
        for column in dataframe.columns:
            if column.lower() in instruction:
                return dataframe.drop(columns=[column])
        
        return dataframe
    
    def _handle_modify_operation(self, dataframe: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Apply modification operation to dataframe."""
        # Placeholder for general modifications
        return dataframe
    
    def _handle_merge_operation(self, dataframe: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Handle merge operation (requires multiple files)."""
        # This would need access to multiple dataframes
        return dataframe
    
    def execute_on_file(self, file_path: Path, instruction_text: str,
                       sheet_name: Optional[str] = None) -> Tuple[BytesIO, str]:
        """Execute instruction on Excel file and return modified file."""
        # Parse instruction
        parsed_instruction = self.parse_instruction(instruction_text)
        operation_type = parsed_instruction['operation_type']
        
        # Read Excel file
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            sheets_to_process = {sheet_name: df}
        else:
            sheets_to_process = pd.read_excel(file_path, sheet_name=None)
        
        # Process each sheet
        modified_sheets = {}
        for sheet, dataframe in sheets_to_process.items():
            handler = self.operation_handlers.get(operation_type, self._handle_modify_operation)
            modified_sheets[sheet] = handler(dataframe, parsed_instruction)
        
        # Write to BytesIO
        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            for sheet_name, dataframe in modified_sheets.items():
                dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output_buffer.seek(0)
        
        execution_summary = f"Applied {operation_type} operation"
        return output_buffer, execution_summary
    
    def execute_multi_file(self, file_paths: Dict[str, Path], instruction_text: str) -> Dict[str, BytesIO]:
        """Execute instruction across multiple files."""
        results = {}
        
        for file_alias, file_path in file_paths.items():
            # Check if this file is mentioned in instruction
            if file_alias.upper() in instruction_text.upper():
                output_buffer, summary = self.execute_on_file(file_path, instruction_text)
                results[file_alias] = output_buffer
        
        return results
