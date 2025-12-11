"""
Data Generator for SQL Schemas

Generates dummy data for SQL tables using Faker, respecting foreign key constraints
and table dependencies determined by the dependency graph.
"""

import random
from typing import Dict, List, Any

from core.exceptions import InvalidSchemaError, DataGenerationError
from core.utils.generators.config import GeneratorConfig
from core.utils.generators.field_generators import FieldGeneratorFactory
from core.utils.parser import parse_sql_schema
from core.utils.graph import get_insertion_order


class DataGenerator:
    """
    Generates dummy data for SQL schema tables.
    
    Uses Strategy Pattern for field generation and respects foreign key constraints.
    """
    
    def __init__(self, config: GeneratorConfig = None):
        """
        Initialize data generator.
        
        Args:
            config: Generator configuration (uses default if not provided)
        """
        self.config = config or GeneratorConfig()
        self.field_factory = FieldGeneratorFactory(self.config)
    
    def generate(
        self, 
        sql_content: str, 
        num_records: int = 100
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate dummy data for SQL schema tables.
        
        Args:
            sql_content: SQL schema content with CREATE TABLE statements
            num_records: Number of records to generate for each table
            
        Returns:
            Dictionary mapping table names to lists of generated row dictionaries:
            {
                'table_name': [
                    {'column1': value1, 'column2': value2, ...},
                    ...
                ]
            }
            
        Raises:
            InvalidSchemaError: If schema is invalid or empty
            DataGenerationError: If data generation fails
        """
        # Parse the schema
        schema = parse_sql_schema(sql_content)
        
        if not schema:
            raise InvalidSchemaError("No valid tables found in SQL schema. Please provide valid CREATE TABLE statements.")
        
        # Get insertion order (respects foreign key dependencies)
        try:
            table_order = get_insertion_order(schema)
        except ValueError as e:
            raise DataGenerationError(f"Cannot generate data due to schema issues: {str(e)}")
        
        # Track generated primary keys for foreign key references
        primary_keys = {}  # {table_name: [pk_value1, pk_value2, ...]}
        
        # Store generated data
        generated_data = {}
        
        # Generate data for each table in dependency order
        for table_name in table_order:
            try:
                table_info = schema[table_name]
                
                # Generate records for this table
                table_records = self._generate_table_records(
                    table_name=table_name,
                    table_info=table_info,
                    num_records=num_records,
                    primary_keys=primary_keys
                )
                
                # Store generated data
                generated_data[table_name] = table_records
                
                # Track primary keys for foreign key references
                primary_key_col = table_info.get('primary_key')
                if primary_key_col:
                    primary_keys[table_name] = [
                        record[primary_key_col] for record in table_records
                    ]
            except Exception as e:
                raise DataGenerationError(f"Error generating data for table '{table_name}': {str(e)}")
        
        return generated_data
    
    def _generate_table_records(
        self,
        table_name: str,
        table_info: Dict[str, Any],
        num_records: int,
        primary_keys: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate records for a single table."""
        table_records = []
        primary_key_col = table_info.get('primary_key')
        foreign_keys = table_info.get('foreign_keys', {})
        columns = table_info.get('columns', {})
        
        for record_num in range(num_records):
            record = {}
            
            # Generate data for each column
            for col_name, col_type in columns.items():
                # Skip if this is a foreign key (will be filled later)
                if col_name in foreign_keys:
                    continue
                
                # Generate value based on column type and name
                value = self.field_factory.generate_value(
                    col_name=col_name,
                    col_type=col_type,
                    is_primary_key=(col_name == primary_key_col),
                    record_num=record_num
                )
                record[col_name] = value
            
            # Fill foreign keys with references to previously generated data
            for fk_col, fk_info in foreign_keys.items():
                ref_table = fk_info['ref_table']
                ref_col = fk_info['ref_column']
                
                if ref_table in primary_keys and primary_keys[ref_table]:
                    # Randomly select from available primary key values
                    # Sometimes set to None for nullable foreign keys
                    if random.random() < self.config.nullable_fk_probability:
                        record[fk_col] = None
                    else:
                        record[fk_col] = random.choice(primary_keys[ref_table])
                else:
                    # No referenced data available yet (shouldn't happen with correct order)
                    record[fk_col] = None
            
            table_records.append(record)
        
        return table_records


# Backward compatibility: keep the old function interface
def generate_data(sql_content: str, num_records: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate dummy data for SQL schema tables (backward compatibility function).
    
    Args:
        sql_content: SQL schema content with CREATE TABLE statements
        num_records: Number of records to generate for each table
        
    Returns:
        Dictionary mapping table names to lists of generated row dictionaries
    """
    generator = DataGenerator()
    return generator.generate(sql_content, num_records)

