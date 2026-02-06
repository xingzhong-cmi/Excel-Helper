#!/usr/bin/env python3
"""
Example script demonstrating Excel Helper MVP functionality.
Shows how to create and execute plans programmatically.
"""
import sys
sys.path.insert(0, 'src')

from core.plan import (
    ExecutionPlan, Operation, OperationType, TargetSpec,
    DeduplicateParams, FillNullsParams, FillStrategy
)
from core.executor import PlanExecutor
import openpyxl
from openpyxl import Workbook
import pandas as pd


def create_sample_workbook():
    """Create a sample workbook with test data."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"
    
    # Add headers
    ws.append(["OrderID", "Customer", "Amount", "Status", "Region"])
    
    # Add data (with some issues to fix)
    data = [
        [1001, "Alice", 250.50, "Complete", "North"],
        [1002, "Bob", 180.00, "Complete", None],  # Missing region
        [1003, "Charlie", 420.25, "Cancelled", "South"],  # Will be deleted
        [1001, "Alice", 250.50, "Complete", "North"],  # Duplicate
        [1004, "David", 330.00, "Complete", "East"],
        [1005, "Eve", 195.75, "Pending", None],  # Missing region
        [1002, "Bob", 180.00, "Complete", "West"],  # Duplicate OrderID
    ]
    
    for row in data:
        ws.append(row)
    
    return wb


def example_1_basic_operations():
    """Example 1: Basic data cleaning operations."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Data Cleaning")
    print("="*70)
    
    # Create sample data
    wb = create_sample_workbook()
    print("\n📊 Sample data created with 7 rows")
    
    # Define operations
    target = TargetSpec(file_alias="F1", sheet_name="Sales")
    
    operations = [
        Operation(
            type=OperationType.FILTER_DELETE_ROWS,
            target=target,
            params={
                "column": "Status",
                "condition": "equals",
                "value": "Cancelled",
                "action": "delete"
            },
            description="Remove cancelled orders"
        ),
        Operation(
            type=OperationType.DEDUPLICATE,
            target=target,
            params=DeduplicateParams(
                columns=["OrderID"],
                keep="first"
            ),
            description="Remove duplicate order IDs"
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
    
    # Create plan
    plan = ExecutionPlan(
        operations=operations,
        description="Clean sales data: remove cancelled, deduplicate, fill nulls"
    )
    
    print("\n📋 Execution Plan:")
    print(plan.to_json())
    
    # Execute plan
    executor = PlanExecutor()
    workbooks = {"F1": wb}
    
    print("\n⚙️ Executing plan...")
    results = executor.execute_plan(plan, workbooks)
    
    # Display results
    print("\n📊 Execution Results:")
    print(f"  ✅ Success: {results['success']}")
    print(f"  ✔️  Operations completed: {results['operations_completed']}")
    print(f"  ❌ Operations failed: {results['operations_failed']}")
    
    print("\n📈 Changes Made:")
    for change in results['changes']:
        print(f"\n  Operation {change['operation']}: {change['description']}")
        if 'rows_deleted' in change:
            print(f"    - Rows deleted: {change['rows_deleted']}")
        if 'duplicates_removed' in change:
            print(f"    - Duplicates removed: {change['duplicates_removed']}")
        if 'cells_filled' in change:
            print(f"    - Cells filled: {change['cells_filled']}")
        print(f"    - Final rows: {change['final_rows']}")
    
    if results['errors']:
        print("\n⚠️  Errors:")
        for error in results['errors']:
            print(f"    - {error}")
    
    return wb, results


def example_2_plan_from_json():
    """Example 2: Create plan from JSON string."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Plan from JSON")
    print("="*70)
    
    # JSON plan (could come from API, file, or AI)
    plan_json = '''
    {
        "description": "Remove duplicates by Customer name",
        "operations": [
            {
                "type": "deduplicate",
                "target": {
                    "file_alias": "F1",
                    "sheet_name": "Sales"
                },
                "params": {
                    "columns": ["Customer"],
                    "keep": "first"
                },
                "description": "Keep first occurrence of each customer"
            }
        ]
    }
    '''
    
    print("\n📄 JSON Plan:")
    print(plan_json)
    
    # Parse JSON to plan
    plan = ExecutionPlan.from_json(plan_json)
    print("\n✅ Plan parsed successfully")
    print(f"   Operations: {len(plan.operations)}")
    print(f"   Description: {plan.description}")
    
    # Create sample data and execute
    wb = create_sample_workbook()
    executor = PlanExecutor()
    results = executor.execute_plan(plan, {"F1": wb})
    
    print("\n📊 Execution Results:")
    print(f"  Operations completed: {results['operations_completed']}")
    print(f"  Duplicates removed: {results['changes'][0]['duplicates_removed']}")
    
    return plan


def example_3_plan_validation():
    """Example 3: Plan validation with file metadata."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Plan Validation")
    print("="*70)
    
    # Create a plan
    target = TargetSpec(file_alias="F1", sheet_name="Sales")
    operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(columns=["OrderID", "Customer"], keep="first")
    )
    plan = ExecutionPlan(operations=[operation])
    
    # File metadata (from FileManager in real app)
    file_metadata = {
        "F1": {
            "sheets": ["Sales", "Inventory"],
            "columns": {
                "Sales": ["OrderID", "Customer", "Amount", "Status", "Region"],
                "Inventory": ["ProductID", "Stock", "Price"]
            }
        }
    }
    
    print("\n📁 Available Files and Sheets:")
    for alias, meta in file_metadata.items():
        print(f"  {alias}:")
        for sheet in meta['sheets']:
            cols = meta['columns'].get(sheet, [])
            print(f"    - {sheet}: {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")
    
    # Validate
    errors = plan.validate_targets(file_metadata)
    
    if not errors:
        print("\n✅ Plan validation passed!")
        print("   All targets (files, sheets, columns) exist")
    else:
        print("\n❌ Plan validation failed:")
        for error in errors:
            print(f"   - {error}")
    
    # Test with wrong column
    bad_operation = Operation(
        type=OperationType.DEDUPLICATE,
        target=target,
        params=DeduplicateParams(columns=["NonExistentColumn"], keep="first")
    )
    bad_plan = ExecutionPlan(operations=[bad_operation])
    errors = bad_plan.validate_targets(file_metadata)
    
    print("\n⚠️  Testing with invalid column:")
    if errors:
        print(f"   Caught error: {errors[0]}")
    
    return plan


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Excel Helper MVP - Code Examples")
    print("="*70)
    print("\nThese examples demonstrate the core MVP functionality:")
    print("  1. Creating and executing plans programmatically")
    print("  2. Parsing plans from JSON")
    print("  3. Validating plans against file metadata")
    
    try:
        # Run examples
        wb1, results1 = example_1_basic_operations()
        plan2 = example_2_plan_from_json()
        plan3 = example_3_plan_validation()
        
        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70)
        print("\nKey Takeaways:")
        print("  • Plans are type-safe with Pydantic validation")
        print("  • Operations are executed in sequence safely")
        print("  • Detailed change summaries are provided")
        print("  • Plans can be created programmatically or from JSON")
        print("  • Validation catches errors before execution")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
