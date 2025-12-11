"""
SQL exporter using Builder Pattern for generating INSERT statements.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class SQLInsertBuilder:
    """
    Builder for generating SQL INSERT statements.
    
    Uses Builder Pattern to construct INSERT statements from generated data.
    """
    
    def __init__(self, dialect: str = 'mysql'):
        """
        Initialize SQL INSERT builder.
        
        Args:
            dialect: SQL dialect ('mysql', 'postgres', etc.)
        """
        self.dialect = dialect
        self.statements = []
        self.metadata = {}
    
    def add_table(
        self, 
        table_name: str, 
        records: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> 'SQLInsertBuilder':
        """
        Add INSERT statements for a table.
        
        Args:
            table_name: Name of the table
            records: List of record dictionaries
            columns: Optional list of column names (uses all keys from first record if not provided)
            
        Returns:
            Self for method chaining
        """
        if not records:
            return self
        
        # Get column names
        if columns is None:
            columns = list(records[0].keys())
        
        # Generate INSERT statement for each record
        for record in records:
            insert_stmt = self._build_insert(table_name, record, columns)
            self.statements.append(insert_stmt)
        
        return self
    
    def add_metadata(
        self,
        total_tables: int = None,
        total_records: int = None,
        generated_at: datetime = None
    ) -> 'SQLInsertBuilder':
        """
        Add metadata to the SQL output.
        
        Args:
            total_tables: Total number of tables
            total_records: Total number of records
            generated_at: Generation timestamp
            
        Returns:
            Self for method chaining
        """
        self.metadata = {
            'total_tables': total_tables,
            'total_records': total_records,
            'generated_at': generated_at or datetime.now()
        }
        return self
    
    def _build_insert(
        self, 
        table_name: str, 
        record: Dict[str, Any],
        columns: List[str]
    ) -> str:
        """
        Build a single INSERT statement.
        
        Args:
            table_name: Name of the table
            record: Record dictionary
            columns: List of column names
            
        Returns:
            SQL INSERT statement string
        """
        # Build column names
        col_names = ', '.join(columns)
        
        # Build values
        values = []
        for col in columns:
            value = record.get(col)
            values.append(self._format_value(value))
        
        values_str = ', '.join(values)
        
        # Create INSERT statement
        return f"INSERT INTO {table_name} ({col_names}) VALUES ({values_str});"
    
    def _format_value(self, value: Any) -> str:
        """
        Format a Python value for SQL INSERT statement.
        
        Args:
            value: Python value (int, str, datetime, None, etc.)
            
        Returns:
            SQL-formatted string
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, bool):
            return '1' if value else '0'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            # String - escape single quotes and wrap in quotes
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
    
    def build(self) -> str:
        """
        Build the final SQL output with all INSERT statements.
        
        Returns:
            Complete SQL string with metadata comments and INSERT statements
        """
        output = []
        
        # Add metadata comments
        output.append("-- Generated INSERT statements")
        if self.metadata.get('generated_at'):
            output.append(f"-- Generated at: {self.metadata['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        if self.metadata.get('total_tables'):
            output.append(f"-- Total tables: {self.metadata['total_tables']}")
        if self.metadata.get('total_records'):
            output.append(f"-- Total records: {self.metadata['total_records']}")
        output.append("")
        output.append("")
        
        # Add INSERT statements
        output.extend(self.statements)
        
        return '\n'.join(output)
    
    def reset(self) -> 'SQLInsertBuilder':
        """
        Reset the builder to start fresh.
        
        Returns:
            Self for method chaining
        """
        self.statements = []
        self.metadata = {}
        return self

