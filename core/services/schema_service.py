"""
Schema Service Layer

Orchestrates schema parsing, dependency graph building, data generation,
and SQL export in a unified service interface.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from core.exceptions import InvalidSchemaError, DataGenerationError
from core.utils.parser import parse_sql_schema
from core.utils.graph.dependency_graph import DependencyGraph
from core.utils.generators.data_generator import DataGenerator
from core.utils.generators.config import GeneratorConfig
from core.utils.exporters.sql_exporter import SQLInsertBuilder


class SchemaService:
    """
    Service layer for processing SQL schemas and generating data.
    
    Orchestrates the complete workflow:
    1. Parse SQL schema
    2. Build dependency graph
    3. Generate dummy data
    4. Export to SQL (optional)
    """
    
    def __init__(
        self,
        generator_config: Optional[GeneratorConfig] = None,
        sql_dialect: str = 'mysql'
    ):
        """
        Initialize schema service.
        
        Args:
            generator_config: Configuration for data generator (uses default if not provided)
            sql_dialect: SQL dialect for export ('mysql', 'postgres', etc.)
        """
        self.generator_config = generator_config or GeneratorConfig()
        self.sql_dialect = sql_dialect
        self.generator = DataGenerator(self.generator_config)
        self.exporter = SQLInsertBuilder(self.sql_dialect)
    
    def process_schema(
        self,
        sql_content: str,
        num_records: int = 100,
        export_sql: bool = False
    ) -> Dict[str, Any]:
        """
        Process SQL schema and generate data.
        
        Args:
            sql_content: SQL schema content with CREATE TABLE statements
            num_records: Number of records to generate for each table
            export_sql: Whether to also generate SQL INSERT statements
            
        Returns:
            Dictionary containing:
            {
                'schema': parsed schema dict,
                'insertion_order': list of table names in order,
                'data': generated data dict,
                'sql': SQL INSERT statements (if export_sql=True),
                'metadata': {
                    'total_tables': int,
                    'total_records': int,
                    'generated_at': datetime
                }
            }
            
        Raises:
            InvalidSchemaError: If schema is invalid or empty
            DataGenerationError: If data generation fails
        """
        # Step 1: Parse schema
        schema = parse_sql_schema(sql_content)
        if not schema:
            raise InvalidSchemaError("No valid tables found in SQL schema.")
        
        # Step 2: Build dependency graph
        graph = DependencyGraph(schema)
        insertion_order = graph.get_insertion_order()
        
        # Step 3: Generate data
        data = self.generator.generate(sql_content, num_records)
        
        # Prepare result
        result = {
            'schema': schema,
            'insertion_order': insertion_order,
            'data': data,
            'metadata': {
                'total_tables': len(schema),
                'total_records': sum(len(records) for records in data.values()),
                'generated_at': datetime.now()
            }
        }
        
        # Step 4: Export SQL if requested
        if export_sql:
            sql_output = self._export_to_sql(data, schema, insertion_order, result['metadata'])
            result['sql'] = sql_output
        
        return result
    
    def _export_to_sql(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        schema: Dict[str, Dict[str, Any]],
        insertion_order: List[str],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Export generated data to SQL INSERT statements.
        
        Args:
            data: Generated data dictionary
            schema: Parsed schema dictionary
            insertion_order: Table insertion order
            metadata: Metadata dictionary
            
        Returns:
            SQL string with INSERT statements
        """
        builder = SQLInsertBuilder(self.sql_dialect)
        
        builder.add_metadata(
            total_tables=metadata['total_tables'],
            total_records=metadata['total_records'],
            generated_at=metadata['generated_at']
        )
        
        # Add tables in insertion order
        for table_name in insertion_order:
            records = data.get(table_name, [])
            if records:
                table_info = schema.get(table_name, {})
                columns = list(table_info.get('columns', {}).keys())
                builder.add_table(table_name, records, columns)
        
        return builder.build()
    
    def parse_only(self, sql_content: str) -> Dict[str, Any]:
        """
        Parse SQL schema without generating data.
        
        Args:
            sql_content: SQL schema content
            
        Returns:
            Dictionary with parsed schema and insertion order
        """
        schema = parse_sql_schema(sql_content)
        if not schema:
            raise InvalidSchemaError("No valid tables found in SQL schema.")
        
        graph = DependencyGraph(schema)
        insertion_order = graph.get_insertion_order()
        
        return {
            'schema': schema,
            'insertion_order': insertion_order,
            'has_cycles': graph.has_cycles()
        }
    
    def generate_only(
        self,
        sql_content: str,
        num_records: int = 100
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate data without parsing (assumes schema is already parsed).
        
        Args:
            sql_content: SQL schema content
            num_records: Number of records per table
            
        Returns:
            Generated data dictionary
        """
        return self.generator.generate(sql_content, num_records)
    
    def export_only(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        schema: Dict[str, Dict[str, Any]],
        insertion_order: List[str]
    ) -> str:
        """
        Export data to SQL without generating new data.
        
        Args:
            data: Generated data dictionary
            schema: Parsed schema dictionary
            insertion_order: Table insertion order
            
        Returns:
            SQL INSERT statements string
        """
        metadata = {
            'total_tables': len(schema),
            'total_records': sum(len(records) for records in data.values()),
            'generated_at': datetime.now()
        }
        return self._export_to_sql(data, schema, insertion_order, metadata)

