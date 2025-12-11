"""
Dependency graph builder for determining safe table insertion order.

This module uses NetworkX to build a directed graph of table dependencies
based on foreign key relationships and computes a topological sort to
determine the correct insertion order that respects all foreign key constraints.
"""

import networkx as nx
from networkx import NetworkXUnfeasible
from typing import Dict, Any


def get_insertion_order(tables: Dict[str, Dict[str, Any]]) -> list[str]:
    """
    Build a dependency graph from table foreign keys and return insertion order.
    
    Creates a directed graph where edges represent foreign key dependencies.
    An edge from table A to table B means B depends on A (B has a FK to A),
    so A must be inserted before B.
    
    Uses topological sort to determine a safe insertion order. Raises ValueError
    if a circular dependency is detected.
    
    Args:
        tables: Dictionary mapping table names to their schema info.
                Expected format:
                {
                    "table_name": {
                        "columns": {...},
                        "primary_key": "...",
                        "foreign_keys": {
                            "local_col": {
                                "ref_table": "referenced_table",
                                "ref_column": "referenced_column"
                            }
                        }
                    }
                }
    
    Returns:
        List of table names in the correct insertion order (dependencies first).
    
    Raises:
        ValueError: If a circular dependency is detected in the foreign key graph.
    
    Example:
        >>> schema = {
        ...     "countries": {
        ...         "columns": {"id": "INT", "name": "VARCHAR(100)"},
        ...         "primary_key": "id",
        ...         "foreign_keys": {}
        ...     },
        ...     "users": {
        ...         "columns": {"id": "INT", "country_id": "INT"},
        ...         "primary_key": "id",
        ...         "foreign_keys": {"country_id": {"ref_table": "countries", "ref_column": "id"}}
        ...     }
        ... }
        >>> get_insertion_order(schema)
        ['countries', 'users']
        
        >>> # Circular dependency example (will raise ValueError):
        >>> circular_schema = {
        ...     "table_a": {"foreign_keys": {"fk": {"ref_table": "table_b", "ref_column": "id"}}},
        ...     "table_b": {"foreign_keys": {"fk": {"ref_table": "table_a", "ref_column": "id"}}}
        ... }
        >>> get_insertion_order(circular_schema)
        ValueError: Circular dependency detected involving tables: table_a, table_b
    """
    # Create a directed graph
    graph = nx.DiGraph()
    
    # Add all tables as nodes
    for table_name in tables.keys():
        graph.add_node(table_name)
    
    # Add edges for foreign key dependencies
    # Edge direction: ref_table → dependent_table
    # (the referenced table must come before the table with the foreign key)
    for table_name, table_info in tables.items():
        foreign_keys = table_info.get("foreign_keys", {})
        
        for local_col, fk_info in foreign_keys.items():
            ref_table = fk_info.get("ref_table")
            
            if ref_table and ref_table in tables:
                # Add edge: ref_table → table_name
                # This means ref_table must be inserted before table_name
                graph.add_edge(ref_table, table_name)
    
    # Perform topological sort to get safe insertion order
    try:
        order = list(nx.topological_sort(graph))
        return order
    except NetworkXUnfeasible:
        # Cycle detected - find and report the cycle
        cycles = list(nx.simple_cycles(graph))
        if cycles:
            # Get all tables involved in cycles
            involved_tables = set()
            for cycle in cycles:
                involved_tables.update(cycle)
            cycle_tables = sorted(list(involved_tables))
            raise ValueError(
                f"Circular dependency detected involving tables: {', '.join(cycle_tables)}"
            )
        else:
            # Fallback if no cycles found but sort still failed
            raise ValueError("Circular dependency detected in table foreign keys")

