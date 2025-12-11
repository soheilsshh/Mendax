"""
Dependency graph builder for determining safe table insertion order.

This module uses NetworkX to build a directed graph of table dependencies
based on foreign key relationships and computes a topological sort to
determine the correct insertion order that respects all foreign key constraints.
"""

import networkx as nx
from networkx import NetworkXUnfeasible
from typing import Dict, Any, List, Set

from core.exceptions import CircularDependencyError


class DependencyGraph:
    """
    Builds and manages dependency graph for SQL table insertion order.
    
    Uses NetworkX to build a directed graph of table dependencies based on
    foreign key relationships and computes topological sort for safe insertion order.
    """
    
    def __init__(self, tables: Dict[str, Dict[str, Any]]):
        """
        Initialize dependency graph from table schema.
        
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
        """
        self.tables = tables
        self.graph = self._build_graph()
    
    def _build_graph(self) -> nx.DiGraph:
        """
        Build directed graph from foreign key relationships.
        
        Returns:
            NetworkX DiGraph with tables as nodes and dependencies as edges
        """
        graph = nx.DiGraph()
        
        # Add all tables as nodes
        for table_name in self.tables.keys():
            graph.add_node(table_name)
        
        # Add edges for foreign key dependencies
        # Edge direction: ref_table → dependent_table
        # (the referenced table must come before the table with the foreign key)
        for table_name, table_info in self.tables.items():
            foreign_keys = table_info.get("foreign_keys", {})
            
            for local_col, fk_info in foreign_keys.items():
                ref_table = fk_info.get("ref_table")
                
                if ref_table and ref_table in self.tables:
                    # Add edge: ref_table → table_name
                    # This means ref_table must be inserted before table_name
                    graph.add_edge(ref_table, table_name)
        
        return graph
    
    def get_insertion_order(self) -> List[str]:
        """
        Get safe insertion order using topological sort.
        
        Returns:
            List of table names in the correct insertion order (dependencies first).
            
        Raises:
            CircularDependencyError: If a circular dependency is detected.
        """
        try:
            order = list(nx.topological_sort(self.graph))
            return order
        except NetworkXUnfeasible:
            # Cycle detected - find and report the cycle
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                # Get all tables involved in cycles
                involved_tables = set()
                for cycle in cycles:
                    involved_tables.update(cycle)
                raise CircularDependencyError(sorted(list(involved_tables)))
            else:
                # Fallback if no cycles found but sort still failed
                raise CircularDependencyError(
                    list(self.tables.keys()),
                    "Circular dependency detected in table foreign keys"
                )
    
    def has_cycles(self) -> bool:
        """
        Check if the dependency graph contains cycles.
        
        Returns:
            True if cycles exist, False otherwise
        """
        try:
            # Try topological sort - if it fails, there's a cycle
            list(nx.topological_sort(self.graph))
            return False
        except NetworkXUnfeasible:
            return True
    
    def get_dependencies(self, table_name: str) -> List[str]:
        """
        Get list of tables that the given table depends on.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of table names that must be inserted before this table
        """
        if table_name not in self.graph:
            return []
        
        # Get all predecessors (tables this table depends on)
        return list(self.graph.predecessors(table_name))
    
    def get_dependents(self, table_name: str) -> List[str]:
        """
        Get list of tables that depend on the given table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of table names that depend on this table
        """
        if table_name not in self.graph:
            return []
        
        # Get all successors (tables that depend on this table)
        return list(self.graph.successors(table_name))
    
    def get_cycles(self) -> List[List[str]]:
        """
        Get all cycles in the dependency graph.
        
        Returns:
            List of cycles, where each cycle is a list of table names
        """
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []


# Backward compatibility: keep the old function interface
def get_insertion_order(tables: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Build a dependency graph from table foreign keys and return insertion order.
    
    This is a backward compatibility wrapper around DependencyGraph class.
    
    Args:
        tables: Dictionary mapping table names to their schema info.
        
    Returns:
        List of table names in the correct insertion order (dependencies first).
        
    Raises:
        CircularDependencyError: If a circular dependency is detected.
    """
    graph = DependencyGraph(tables)
    return graph.get_insertion_order()

