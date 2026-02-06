"""
Diff module for generating change summaries and comparisons.
"""
from typing import Dict, Any, List
import pandas as pd


class ChangeSummary:
    """Generates human-readable change summaries from execution results."""
    
    @staticmethod
    def generate_summary(execution_results: Dict[str, Any]) -> str:
        """Generate a comprehensive change summary.
        
        Args:
            execution_results: Results from PlanExecutor.execute_plan()
            
        Returns:
            Formatted summary string
        """
        summary_lines = []
        
        # Overall status
        if execution_results["success"]:
            summary_lines.append("✅ **Execution Successful**")
        else:
            summary_lines.append("⚠️ **Execution Completed with Errors**")
        
        summary_lines.append("")
        
        # Operations summary
        total_ops = execution_results["operations_completed"] + execution_results["operations_failed"]
        summary_lines.append(f"**Operations:** {execution_results['operations_completed']}/{total_ops} completed successfully")
        
        if execution_results["operations_failed"] > 0:
            summary_lines.append(f"  - {execution_results['operations_failed']} operation(s) failed")
        
        summary_lines.append("")
        
        # Detailed changes
        if execution_results["changes"]:
            summary_lines.append("### Changes Made:")
            for change in execution_results["changes"]:
                summary_lines.append(f"\n**Operation {change['operation']}: {change['description']}**")
                summary_lines.extend(ChangeSummary._format_change_details(change))
        
        # Errors
        if execution_results["errors"]:
            summary_lines.append("\n### Errors:")
            for error in execution_results["errors"]:
                summary_lines.append(f"  - {error}")
        
        return "\n".join(summary_lines)
    
    @staticmethod
    def _format_change_details(change: Dict[str, Any]) -> List[str]:
        """Format details for a specific change."""
        lines = []
        op_type = change.get("type", "")
        
        # Row changes
        if "rows_deleted" in change:
            lines.append(f"  - Rows deleted: {change['rows_deleted']}")
        if "rows_kept" in change:
            lines.append(f"  - Rows kept: {change['rows_kept']}")
        
        # Deduplication
        if "duplicates_removed" in change:
            lines.append(f"  - Duplicates removed: {change['duplicates_removed']}")
            lines.append(f"  - Unique rows: {change['unique_rows']}")
            if "checked_columns" in change:
                lines.append(f"  - Checked columns: {', '.join(change['checked_columns'])}")
        
        # Fill nulls
        if "cells_filled" in change:
            lines.append(f"  - Cells filled: {change['cells_filled']}")
            if change.get("nulls_remaining", 0) > 0:
                lines.append(f"  - Nulls remaining: {change['nulls_remaining']}")
            if "strategy" in change:
                lines.append(f"  - Strategy: {change['strategy']}")
        
        # Type conversion
        if "conversions_successful" in change:
            lines.append(f"  - Successful conversions: {change['conversions_successful']}")
            if change.get("conversions_failed", 0) > 0:
                lines.append(f"  - Failed conversions: {change['conversions_failed']}")
                if "failed_rows" in change and change["failed_rows"]:
                    failed_str = ", ".join(map(str, change["failed_rows"][:5]))
                    lines.append(f"  - Failed rows (sample): {failed_str}")
        
        # Column operations
        if "columns_created" in change:
            lines.append(f"  - Columns created: {change['columns_created']}")
            if "new_columns" in change:
                lines.append(f"  - New columns: {', '.join(change['new_columns'])}")
        
        if "columns_deleted" in change and change["columns_deleted"] > 0:
            lines.append(f"  - Columns deleted: {change['columns_deleted']}")
        
        # Before/after stats
        if "initial_rows" in change:
            lines.append(f"  - Rows: {change['initial_rows']} → {change['final_rows']}")
        if "initial_columns" in change and change.get("columns_changed", 0) != 0:
            lines.append(f"  - Columns: {change['initial_columns']} → {change['final_columns']}")
        
        return lines
    
    @staticmethod
    def get_affected_rows_sample(df_before: pd.DataFrame, df_after: pd.DataFrame, max_rows: int = 5) -> Dict[str, Any]:
        """Get a sample of affected rows for preview.
        
        Args:
            df_before: DataFrame before changes
            df_after: DataFrame after changes
            max_rows: Maximum number of sample rows to return
            
        Returns:
            Dictionary with affected rows information
        """
        affected = {
            "rows_before": len(df_before),
            "rows_after": len(df_after),
            "rows_changed": abs(len(df_before) - len(df_after)),
            "sample_before": [],
            "sample_after": []
        }
        
        # Get sample of removed rows (if any)
        if len(df_before) > len(df_after):
            # Find rows that were removed (simple approach: compare indices)
            removed_indices = df_before.index.difference(df_after.index)
            if len(removed_indices) > 0:
                sample_indices = removed_indices[:max_rows]
                affected["sample_removed"] = df_before.loc[sample_indices].to_dict('records')
        
        # Get sample of first few rows after changes
        if len(df_after) > 0:
            affected["sample_after"] = df_after.head(max_rows).to_dict('records')
        
        return affected
    
    @staticmethod
    def generate_comparison_report(df_before: pd.DataFrame, df_after: pd.DataFrame) -> Dict[str, Any]:
        """Generate a detailed comparison report.
        
        Args:
            df_before: DataFrame before changes
            df_after: DataFrame after changes
            
        Returns:
            Dictionary with comparison metrics
        """
        report = {
            "shape_before": df_before.shape,
            "shape_after": df_after.shape,
            "rows_changed": len(df_before) - len(df_after),
            "columns_before": list(df_before.columns),
            "columns_after": list(df_after.columns),
            "columns_added": list(set(df_after.columns) - set(df_before.columns)),
            "columns_removed": list(set(df_before.columns) - set(df_after.columns)),
        }
        
        # Count null changes in common columns
        common_cols = set(df_before.columns) & set(df_after.columns)
        null_changes = {}
        for col in common_cols:
            nulls_before = df_before[col].isna().sum()
            nulls_after = df_after[col].isna().sum() if col in df_after.columns else 0
            if nulls_before != nulls_after:
                null_changes[col] = {
                    "before": int(nulls_before),
                    "after": int(nulls_after),
                    "change": int(nulls_before - nulls_after)
                }
        
        report["null_changes"] = null_changes
        
        return report
