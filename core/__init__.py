"""
Core module for Excel Helper MVP.
Contains plan schema, planner, executor, and diff utilities.
"""
from .plan import (
    ExecutionPlan, Operation, OperationType, TargetSpec,
    FilterDeleteRowsParams, DeduplicateParams, FillNullsParams,
    TypeConversionParams, ColumnSplitParams, ColumnMergeParams,
    FillStrategy, DataType
)
from .planner import PlanGenerator
from .executor import PlanExecutor
from .diff import ChangeSummary

__all__ = [
    "ExecutionPlan",
    "Operation",
    "OperationType",
    "TargetSpec",
    "FilterDeleteRowsParams",
    "DeduplicateParams",
    "FillNullsParams",
    "TypeConversionParams",
    "ColumnSplitParams",
    "ColumnMergeParams",
    "FillStrategy",
    "DataType",
    "PlanGenerator",
    "PlanExecutor",
    "ChangeSummary",
]