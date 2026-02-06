"""
Unit tests for plan validation and schema.
"""
import pytest
import json
from core.plan import (
    ExecutionPlan, Operation, OperationType, TargetSpec,
    FilterDeleteRowsParams, DeduplicateParams, FillNullsParams,
    TypeConversionParams, ColumnSplitParams, ColumnMergeParams,
    FillStrategy, DataType
)


def test_filter_delete_params_validation():
    """Test FilterDeleteRowsParams validation."""
    # Valid params
    params = FilterDeleteRowsParams(
        column="Status",
        condition="equals",
        value="Active",
        action="keep"
    )
    assert params.column == "Status"
    assert params.condition == "equals"
    
    # Empty condition
    params_empty = FilterDeleteRowsParams(
        column="Name",
        condition="empty",
        action="delete"
    )
    assert params_empty.value is None


def test_deduplicate_params():
    """Test DeduplicateParams."""
    params = DeduplicateParams(
        columns=["ID", "Email"],
        keep="first"
    )
    assert len(params.columns) == 2
    assert params.keep == "first"


def test_fill_nulls_params_validation():
    """Test FillNullsParams validation."""
    # Valid fixed value
    params = FillNullsParams(
        column="Region",
        strategy=FillStrategy.FIXED_VALUE,
        value="Unknown"
    )
    assert params.value == "Unknown"
    
    # Forward fill doesn't need value
    params_ff = FillNullsParams(
        column="Price",
        strategy=FillStrategy.FORWARD_FILL
    )
    assert params_ff.value is None
    
    # Should fail without value for fixed_value strategy
    with pytest.raises(ValueError):
        FillNullsParams(
            column="Region",
            strategy=FillStrategy.FIXED_VALUE,
            value=None
        )


def test_type_conversion_params():
    """Test TypeConversionParams."""
    params = TypeConversionParams(
        column="Amount",
        target_type=DataType.NUMBER
    )
    assert params.target_type == DataType.NUMBER
    
    # Date conversion with format
    params_date = TypeConversionParams(
        column="OrderDate",
        target_type=DataType.DATE,
        date_format="%Y-%m-%d"
    )
    assert params_date.date_format == "%Y-%m-%d"


def test_column_split_params():
    """Test ColumnSplitParams."""
    params = ColumnSplitParams(
        source_column="FullName",
        delimiter=" ",
        new_column_names=["FirstName", "LastName"]
    )
    assert params.delimiter == " "
    assert len(params.new_column_names) == 2


def test_column_merge_params():
    """Test ColumnMergeParams."""
    params = ColumnMergeParams(
        source_columns=["FirstName", "LastName"],
        target_column="FullName",
        delimiter=" ",
        delete_sources=True
    )
    assert len(params.source_columns) == 2
    assert params.delete_sources is True


def test_operation_creation():
    """Test Operation creation."""
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    params = DeduplicateParams(columns=["ID"], keep="first")
    
    operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=params,
        description="Remove duplicate IDs"
    )
    
    assert operation.type == OperationType.DEDUPLICATE
    assert operation.target.file_alias == "F1"
    assert operation.description == "Remove duplicate IDs"


def test_operation_params_type_validation():
    """Test that operation validates params match type."""
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    
    # Should fail: using deduplicate params for filter operation
    with pytest.raises(ValueError):
        Operation(
            type=OperationType.FILTER_DELETE_ROWS,
            target=target,
            params=DeduplicateParams(columns=["ID"], keep="first")
        )


def test_execution_plan_creation():
    """Test ExecutionPlan creation."""
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    
    op1 = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(columns=["ID"], keep="first")
    )
    
    op2 = Operation(
        type=OperationType.FILL_NULLS,
        target=target,
        params=FillNullsParams(
            column="Region",
            strategy=FillStrategy.FIXED_VALUE,
            value="Unknown"
        )
    )
    
    plan = ExecutionPlan(
        operations=[op1, op2],
        description="Test plan"
    )
    
    assert len(plan.operations) == 2
    assert plan.description == "Test plan"


def test_execution_plan_json_serialization():
    """Test plan JSON serialization and deserialization."""
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    
    operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(columns=["ID", "Email"], keep="first"),
        description="Remove duplicates"
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    # Serialize to JSON
    json_str = plan.to_json()
    assert isinstance(json_str, str)
    
    # Parse JSON
    data = json.loads(json_str)
    assert "operations" in data
    assert len(data["operations"]) == 1
    
    # Deserialize back to plan
    plan2 = ExecutionPlan.from_json(json_str)
    assert len(plan2.operations) == 1
    assert plan2.operations[0].type == OperationType.DEDUPLICATE


def test_plan_validate_targets():
    """Test plan target validation."""
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    
    operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(columns=["ID"], keep="first")
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    # Valid metadata
    metadata = {
        "F1": {
            "sheets": ["Sheet1", "Sheet2"],
            "columns": {
                "Sheet1": ["ID", "Name", "Email"],
                "Sheet2": ["Data"]
            }
        }
    }
    
    errors = plan.validate_targets(metadata)
    assert len(errors) == 0
    
    # Missing file
    errors = plan.validate_targets({})
    assert len(errors) > 0
    assert "not found" in errors[0].lower()
    
    # Missing sheet
    metadata_no_sheet = {
        "F1": {
            "sheets": ["Sheet2"],
            "columns": {"Sheet2": ["Data"]}
        }
    }
    errors = plan.validate_targets(metadata_no_sheet)
    assert len(errors) > 0
    
    # Missing column
    metadata_no_column = {
        "F1": {
            "sheets": ["Sheet1"],
            "columns": {"Sheet1": ["Name", "Email"]}
        }
    }
    errors = plan.validate_targets(metadata_no_column)
    assert len(errors) > 0
    assert "ID" in errors[0]


def test_complex_plan_example():
    """Test a complex multi-operation plan."""
    target = TargetSpec(file_alias="F1", sheet_name="Sales")
    
    operations = [
        Operation(
            type=OperationType.FILTER_DELETE_ROWS,
            target=target,
            params=FilterDeleteRowsParams(
                column="Status",
                condition="equals",
                value="Cancelled",
                action="delete"
            ),
            description="Remove cancelled orders"
        ),
        Operation(
            type=OperationType.DEDUPLICATE,
            target=target,
            params=DeduplicateParams(
                columns=["OrderID"],
                keep="first"
            ),
            description="Remove duplicate orders"
        ),
        Operation(
            type=OperationType.FILL_NULLS,
            target=target,
            params=FillNullsParams(
                column="CustomerRegion",
                strategy=FillStrategy.FIXED_VALUE,
                value="Unknown"
            ),
            description="Fill missing regions"
        ),
        Operation(
            type=OperationType.TYPE_CONVERSION,
            target=target,
            params=TypeConversionParams(
                column="OrderDate",
                target_type=DataType.DATE,
                date_format="%Y-%m-%d"
            ),
            description="Convert order dates"
        )
    ]
    
    plan = ExecutionPlan(
        operations=operations,
        description="Clean and process sales data"
    )
    
    assert len(plan.operations) == 4
    
    # Validate JSON round-trip
    json_str = plan.to_json()
    plan2 = ExecutionPlan.from_json(json_str)
    assert len(plan2.operations) == 4
    assert plan2.operations[0].type == OperationType.FILTER_DELETE_ROWS
    assert plan2.operations[1].type == OperationType.DEDUPLICATE
    assert plan2.operations[2].type == OperationType.FILL_NULLS
    assert plan2.operations[3].type == OperationType.TYPE_CONVERSION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
