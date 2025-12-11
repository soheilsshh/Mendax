"""
Data Generator for SQL Schemas

DEPRECATED: This module is kept for backward compatibility.
Please use core.utils.generators.data_generator.DataGenerator instead.
"""

from typing import Dict, List, Any
from core.utils.generators.data_generator import generate_data as _generate_data

def generate_data(sql_content: str, num_records: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate dummy data for SQL schema tables.
    
    DEPRECATED: This is a backward compatibility wrapper.
    Please use DataGenerator class from core.utils.generators.data_generator instead.
    
    Args:
        sql_content: SQL schema content with CREATE TABLE statements
        num_records: Number of records to generate for each table
        
    Returns:
        Dictionary mapping table names to lists of generated row dictionaries
    """
    return _generate_data(sql_content, num_records)

