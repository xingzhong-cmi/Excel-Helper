"""
Plan schema and validation module using Pydantic.
Defines the structure for executable Excel operations.
"""
from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class OperationType(str, Enum):
    """Supported operation types (whitelist)."""
    FILTER_DELETE_ROWS = "filter_delete_rows"
    DEDUPLICATE = "deduplicate"
    FILL_NULLS = "fill_nulls"
    TYPE_CONVERSION = "type_conversion"
    COLUMN_SPLIT = "column_split"
    COLUMN_MERGE = "column_merge"


class FillStrategy(str, Enum):
    """Strategy for filling null values."""
    FIXED_VALUE = "fixed_value"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"


class DataType(str, Enum):
    """Target data types for conversion."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"


class TargetSpec(BaseModel):
    """Specifies the target file and sheet for an operation."""
    file_alias: str = Field(..., description="File alias (e.g., F1, F2)")
    sheet_name: str = Field(..., description="Sheet name to operate on")
    
    class Config:
        frozen = True


class FilterDeleteRowsParams(BaseModel):
    """Parameters for conditional row filtering/deletion."""
    column: str = Field(..., description="Column name to filter on")
    condition: Literal["equals", "not_equals", "contains", "not_contains", "empty", "not_empty", "greater_than", "less_than"]
    value: Optional[Union[str, int, float]] = Field(None, description="Value to compare against (not needed for empty/not_empty)")
    action: Literal["delete", "keep"] = Field("delete", description="Whether to delete matching rows or keep only matching rows")


class DeduplicateParams(BaseModel):
    """Parameters for deduplication."""
    columns: List[str] = Field(..., description="Columns to check for duplicates")
    keep: Literal["first", "last"] = Field("first", description="Which duplicate to keep")


class FillNullsParams(BaseModel):
    """Parameters for filling null values."""
    column: str = Field(..., description="Column name to fill")
    strategy: FillStrategy = Field(..., description="Fill strategy")
    value: Optional[Union[str, int, float]] = Field(None, description="Fixed value (required for fixed_value strategy)")
    
    @validator('value')
    def validate_value(cls, v, values):
        """Ensure value is provided for fixed_value strategy."""
        if values.get('strategy') == FillStrategy.FIXED_VALUE and v is None:
            raise ValueError("value is required when strategy is fixed_value")
        return v


class TypeConversionParams(BaseModel):
    """Parameters for type conversion."""
    column: str = Field(..., description="Column name to convert")
    target_type: DataType = Field(..., description="Target data type")
    date_format: Optional[str] = Field(None, description="Date format string (for date/datetime conversion)")


class ColumnSplitParams(BaseModel):
    """Parameters for splitting a column."""
    source_column: str = Field(..., description="Column to split")
    delimiter: str = Field(..., description="Delimiter to split on")
    new_column_names: List[str] = Field(..., description="Names for the new columns")
    max_splits: Optional[int] = Field(None, description="Maximum number of splits (-1 for unlimited)")


class ColumnMergeParams(BaseModel):
    """Parameters for merging columns."""
    source_columns: List[str] = Field(..., min_items=2, description="Columns to merge")
    target_column: str = Field(..., description="Name for the merged column")
    delimiter: str = Field(" ", description="Delimiter to join with")
    delete_sources: bool = Field(False, description="Whether to delete source columns after merge")


class Operation(BaseModel):
    """A single executable operation."""
    type: OperationType = Field(..., description="Type of operation")
    target: TargetSpec = Field(..., description="Target file and sheet")
    params: Union[
        FilterDeleteRowsParams,
        DeduplicateParams,
        FillNullsParams,
        TypeConversionParams,
        ColumnSplitParams,
        ColumnMergeParams
    ] = Field(..., description="Operation-specific parameters")
    description: Optional[str] = Field(None, description="Human-readable description of the operation")
    
    @validator('params')
    def validate_params_match_type(cls, v, values):
        """Ensure params type matches operation type."""
        op_type = values.get('type')
        param_type_map = {
            OperationType.FILTER_DELETE_ROWS: FilterDeleteRowsParams,
            OperationType.DEDUPLICATE: DeduplicateParams,
            OperationType.FILL_NULLS: FillNullsParams,
            OperationType.TYPE_CONVERSION: TypeConversionParams,
            OperationType.COLUMN_SPLIT: ColumnSplitParams,
            OperationType.COLUMN_MERGE: ColumnMergeParams,
        }
        expected_type = param_type_map.get(op_type)
        if expected_type and not isinstance(v, expected_type):
            raise ValueError(f"params must be {expected_type.__name__} for operation type {op_type}")
        return v


class ExecutionPlan(BaseModel):
    """A complete execution plan with multiple operations."""
    operations: List[Operation] = Field(..., min_items=1, description="List of operations to execute")
    description: Optional[str] = Field(None, description="Overall plan description")
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Remove duplicates and fill missing values in sales data",
                "operations": [
                    {
                        "type": "deduplicate",
                        "target": {"file_alias": "F1", "sheet_name": "Sheet1"},
                        "params": {
                            "columns": ["CustomerID", "OrderDate"],
                            "keep": "first"
                        },
                        "description": "Remove duplicate orders by customer and date"
                    },
                    {
                        "type": "fill_nulls",
                        "target": {"file_alias": "F1", "sheet_name": "Sheet1"},
                        "params": {
                            "column": "Region",
                            "strategy": "fixed_value",
                            "value": "Unknown"
                        },
                        "description": "Fill missing regions with 'Unknown'"
                    }
                ]
            }
        }
    
    def to_json(self) -> str:
        """Export plan as JSON string."""
        return self.json(indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ExecutionPlan':
        """Parse plan from JSON string."""
        return cls.parse_raw(json_str)
    
    def validate_targets(self, available_files: Dict[str, Dict[str, Any]]) -> List[str]:
        """Validate that all operation targets exist.
        
        Args:
            available_files: Dict mapping file_alias to metadata (sheets, columns, etc.)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        for i, op in enumerate(self.operations):
            # Check file exists
            if op.target.file_alias not in available_files:
                errors.append(f"Operation {i+1}: File {op.target.file_alias} not found")
                continue
            
            file_meta = available_files[op.target.file_alias]
            
            # Check sheet exists
            if op.target.sheet_name not in file_meta.get('sheets', []):
                errors.append(f"Operation {i+1}: Sheet {op.target.sheet_name} not found in {op.target.file_alias}")
                continue
            
            # Check columns exist (for operations that reference columns)
            sheet_columns = file_meta.get('columns', {}).get(op.target.sheet_name, [])
            
            if op.type == OperationType.FILTER_DELETE_ROWS:
                if op.params.column not in sheet_columns:
                    errors.append(f"Operation {i+1}: Column {op.params.column} not found in {op.target.file_alias}.{op.target.sheet_name}")
            
            elif op.type == OperationType.DEDUPLICATE:
                for col in op.params.columns:
                    if col not in sheet_columns:
                        errors.append(f"Operation {i+1}: Column {col} not found in {op.target.file_alias}.{op.target.sheet_name}")
            
            elif op.type in [OperationType.FILL_NULLS, OperationType.TYPE_CONVERSION]:
                if op.params.column not in sheet_columns:
                    errors.append(f"Operation {i+1}: Column {op.params.column} not found in {op.target.file_alias}.{op.target.sheet_name}")
            
            elif op.type == OperationType.COLUMN_SPLIT:
                if op.params.source_column not in sheet_columns:
                    errors.append(f"Operation {i+1}: Column {op.params.source_column} not found in {op.target.file_alias}.{op.target.sheet_name}")
            
            elif op.type == OperationType.COLUMN_MERGE:
                for col in op.params.source_columns:
                    if col not in sheet_columns:
                        errors.append(f"Operation {i+1}: Column {col} not found in {op.target.file_alias}.{op.target.sheet_name}")
        
        return errors
