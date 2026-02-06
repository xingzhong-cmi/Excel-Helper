"""
Unit tests for plan executor operations.
"""
import pytest
import pandas as pd
import openpyxl
from openpyxl import Workbook
from core.executor import PlanExecutor
from core.plan import (
    ExecutionPlan, Operation, OperationType, TargetSpec,
    FilterDeleteRowsParams, DeduplicateParams, FillNullsParams,
    TypeConversionParams, DataType, FillStrategy
)


@pytest.fixture
def sample_workbook():
    """Create a sample workbook for testing."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    
    # Add headers
    ws.append(["ID", "Name", "Status", "Amount", "Region"])
    
    # Add data
    data = [
        [1, "Alice", "Active", "100", "North"],
        [2, "Bob", "Inactive", "200", "South"],
        [3, "Charlie", "Active", "150", None],
        [1, "Alice", "Active", "100", "North"],  # Duplicate
        [4, "David", "Cancelled", "300", "East"],
        [5, "Eve", "Active", None, "West"],
    ]
    
    for row in data:
        ws.append(row)
    
    return wb


def test_executor_filter_delete_rows(sample_workbook):
    """Test filter/delete rows operation."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    operation = Operation(
        type=OperationType.FILTER_DELETE_ROWS,
        target=target,
        params=FilterDeleteRowsParams(
            column="Status",
            condition="equals",
            value="Cancelled",
            action="delete"
        )
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    results = executor.execute_plan(plan, {"F1": sample_workbook})
    
    assert results["success"] is True
    assert results["operations_completed"] == 1
    assert results["operations_failed"] == 0
    
    # Check that rows were deleted
    change = results["changes"][0]
    assert change["rows_deleted"] > 0
    assert change["success"] is True


def test_executor_deduplicate(sample_workbook):
    """Test deduplication operation."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(
            columns=["ID", "Name"],
            keep="first"
        )
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    results = executor.execute_plan(plan, {"F1": sample_workbook})
    
    assert results["success"] is True
    assert results["operations_completed"] == 1
    
    change = results["changes"][0]
    assert change["duplicates_removed"] > 0
    assert change["success"] is True


def test_executor_fill_nulls(sample_workbook):
    """Test fill nulls operation."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    operation = Operation(
        type=OperationType.FILL_NULLS,
        target=target,
        params=FillNullsParams(
            column="Region",
            strategy=FillStrategy.FIXED_VALUE,
            value="Unknown"
        )
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    results = executor.execute_plan(plan, {"F1": sample_workbook})
    
    assert results["success"] is True
    assert results["operations_completed"] == 1
    
    change = results["changes"][0]
    assert change["cells_filled"] > 0
    assert change["success"] is True


def test_executor_type_conversion(sample_workbook):
    """Test type conversion operation."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    operation = Operation(
        type=OperationType.TYPE_CONVERSION,
        target=target,
        params=TypeConversionParams(
            column="Amount",
            target_type=DataType.NUMBER
        )
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    results = executor.execute_plan(plan, {"F1": sample_workbook})
    
    assert results["success"] is True
    assert results["operations_completed"] == 1
    
    change = results["changes"][0]
    assert "conversions_successful" in change
    assert change["success"] is True


def test_executor_multi_operation_plan(sample_workbook):
    """Test executing multiple operations in sequence."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    
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
                columns=["ID"],
                keep="first"
            ),
            description="Remove duplicates"
        ),
        Operation(
            type=OperationType.FILL_NULLS,
            target=target,
            params=FillNullsParams(
                column="Region",
                strategy=FillStrategy.FIXED_VALUE,
                value="Unknown"
            ),
            description="Fill missing regions"
        )
    ]
    
    plan = ExecutionPlan(operations=operations)
    
    results = executor.execute_plan(plan, {"F1": sample_workbook})
    
    assert results["success"] is True
    assert results["operations_completed"] == 3
    assert results["operations_failed"] == 0
    assert len(results["changes"]) == 3


def test_executor_error_handling_missing_workbook():
    """Test error handling when workbook is missing."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F2", sheet_name="Sheet1")
    operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(columns=["ID"], keep="first")
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    results = executor.execute_plan(plan, {"F1": Workbook()})
    
    assert results["success"] is False
    assert results["operations_failed"] == 1
    assert len(results["errors"]) > 0


def test_executor_error_handling_missing_column(sample_workbook):
    """Test error handling when column doesn't exist."""
    executor = PlanExecutor()
    
    target = TargetSpec(file_alias="F1", sheet_name="Sheet1")
    operation = Operation(
        type=OperationType.FILL_NULLS,
        target=target,
        params=FillNullsParams(
            column="NonExistentColumn",
            strategy=FillStrategy.FIXED_VALUE,
            value="Test"
        )
    )
    
    plan = ExecutionPlan(operations=[operation])
    
    results = executor.execute_plan(plan, {"F1": sample_workbook})
    
    # Should fail but not crash
    assert results["operations_failed"] == 1
    assert len(results["errors"]) > 0 or not results["changes"][0]["success"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
