"""
Dependency graph builder for determining safe table insertion order.

DEPRECATED: This module is kept for backward compatibility.
Please use core.utils.graph.dependency_graph.DependencyGraph instead.
"""

from typing import Dict, Any
from core.utils.graph.dependency_graph import get_insertion_order as _get_insertion_order


def get_insertion_order(tables: Dict[str, Dict[str, Any]]) -> list[str]:
    """
    Build a dependency graph from table foreign keys and return insertion order.
    
    DEPRECATED: This is a backward compatibility wrapper.
    Please use DependencyGraph class from core.utils.graph.dependency_graph instead.
    
    Args:
        tables: Dictionary mapping table names to their schema info.
    
    Returns:
        List of table names in the correct insertion order (dependencies first).
        
    Raises:
        CircularDependencyError: If a circular dependency is detected.
    """
    return _get_insertion_order(tables)
