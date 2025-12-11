"""
Data Generator for SQL Schemas

Generates dummy data for SQL tables using Faker, respecting foreign key constraints
and table dependencies determined by the dependency graph.
"""

import re
import random
from typing import Dict, List, Any, Optional
from faker import Faker

from core.utils.parser import parse_sql_schema
from core.utils.graph import get_insertion_order

# Initialize Faker instance
fake = Faker()


def generate_data(sql_content: str, num_records: int = 100) -> Dict[str, List[Dict[str, Any]]]:
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
    """
    # Parse the schema
    schema = parse_sql_schema(sql_content)
    
    if not schema:
        raise ValueError("No valid tables found in SQL schema. Please provide valid CREATE TABLE statements.")
    
    # Get insertion order (respects foreign key dependencies)
    try:
        table_order = get_insertion_order(schema)
    except ValueError as e:
        raise ValueError(f"Cannot generate data due to schema issues: {str(e)}")
    
    # Track generated primary keys for foreign key references
    primary_keys = {}  # {table_name: [pk_value1, pk_value2, ...]}
    
    # Store generated data
    generated_data = {}
    
    # Generate data for each table in dependency order
    for table_name in table_order:
        table_info = schema[table_name]
        
        # Generate records for this table
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
                value = _generate_column_value(
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
                    # Sometimes set to None for nullable foreign keys (30% chance)
                    if random.random() < 0.3 and col_name in columns:
                        record[fk_col] = None
                    else:
                        record[fk_col] = random.choice(primary_keys[ref_table])
                else:
                    # No referenced data available yet (shouldn't happen with correct order)
                    record[fk_col] = None
            
            table_records.append(record)
        
        # Store generated data
        generated_data[table_name] = table_records
        
        # Track primary keys for foreign key references
        if primary_key_col:
            primary_keys[table_name] = [
                record[primary_key_col] for record in table_records
            ]
    
    return generated_data


def _generate_column_value(
    col_name: str,
    col_type: str,
    is_primary_key: bool = False,
    record_num: int = 0
) -> Any:
    """
    Generate a value for a column based on its name and type.
    
    Args:
        col_name: Column name
        col_type: SQL column type (e.g., 'INT', 'VARCHAR(100)')
        is_primary_key: Whether this is a primary key
        record_num: Record number (used for auto-increment)
        
    Returns:
        Generated value appropriate for the column type
    """
    col_name_lower = col_name.lower()
    col_type_upper = col_type.upper()
    
    # Handle primary keys (auto-increment behavior)
    if is_primary_key:
        # Extract base type
        base_type = re.sub(r'\([^)]*\)', '', col_type_upper).strip()
        if base_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'MEDIUMINT']:
            return record_num + 1  # Auto-increment
        elif base_type in ['VARCHAR', 'CHAR', 'TEXT']:
            # String primary keys - use UUID-like values
            return fake.uuid4()
    
    # Smart field detection based on column name
    if 'email' in col_name_lower:
        return fake.email()
    elif 'username' in col_name_lower:
        return fake.user_name()
    elif 'name' in col_name_lower and 'user' not in col_name_lower:
        return fake.name()
    elif 'phone' in col_name_lower:
        return fake.phone_number()
    elif 'url' in col_name_lower or 'link' in col_name_lower:
        return fake.url()
    elif 'address' in col_name_lower:
        return fake.address()
    elif 'city' in col_name_lower and 'id' not in col_name_lower:
        return fake.city()
    elif 'country' in col_name_lower and 'id' not in col_name_lower:
        return fake.country()
    elif 'password' in col_name_lower or 'hash' in col_name_lower:
        return fake.password(length=20)
    elif 'created_at' in col_name_lower or 'updated_at' in col_name_lower:
        return fake.date_time_between(start_date='-1y', end_date='now')
    elif 'date' in col_name_lower and 'id' not in col_name_lower:
        return fake.date()
    elif 'time' in col_name_lower and 'id' not in col_name_lower:
        return fake.time()
    elif 'description' in col_name_lower or 'content' in col_name_lower or 'text' in col_name_lower:
        return fake.text(max_nb_chars=200)
    elif 'title' in col_name_lower:
        return fake.sentence(nb_words=3)
    elif 'slug' in col_name_lower:
        return fake.slug()
    elif 'code' in col_name_lower and 'id' not in col_name_lower:
        return fake.country_code()
    
    # Type-based generation
    base_type = re.sub(r'\([^)]*\)', '', col_type_upper).strip()
    
    # Extract length/precision if available (e.g., VARCHAR(100))
    length_match = re.search(r'\((\d+)\)', col_type_upper)
    max_length = int(length_match.group(1)) if length_match else None
    
    if base_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'MEDIUMINT']:
        if 'unsigned' in col_type_upper:
            return fake.random_int(min=0, max=2147483647)
        return fake.random_int(min=-2147483648, max=2147483647)
    
    elif base_type in ['DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL']:
        if max_length:
            return round(fake.pyfloat(left_digits=max_length-2, right_digits=2), 2)
        return fake.pyfloat(left_digits=10, right_digits=2)
    
    elif base_type in ['VARCHAR', 'CHAR']:
        if max_length:
            if max_length <= 10:
                return fake.word()[:max_length]
            elif max_length <= 50:
                return fake.text(max_nb_chars=max_length).strip()
            else:
                return fake.text(max_nb_chars=max_length).strip()
        return fake.text(max_nb_chars=50).strip()
    
    elif base_type in ['TEXT', 'TINYTEXT', 'MEDIUMTEXT', 'LONGTEXT']:
        return fake.text(max_nb_chars=500)
    
    elif base_type == 'DATE':
        return fake.date()
    
    elif base_type in ['DATETIME', 'TIMESTAMP']:
        return fake.date_time_between(start_date='-1y', end_date='now')
    
    elif base_type == 'TIME':
        return fake.time()
    
    elif base_type in ['BOOLEAN', 'BOOL']:
        return fake.boolean()
    
    elif base_type == 'BIT':
        return fake.random_int(min=0, max=1)
    
    elif base_type == 'JSON':
        return fake.json()
    
    elif base_type == 'UUID':
        return fake.uuid4()
    
    elif base_type == 'YEAR':
        return fake.year()
    
    # Default: return string
    return fake.word()

