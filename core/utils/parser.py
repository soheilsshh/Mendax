"""
SQL Schema Parser

Parses CREATE TABLE statements to extract table structure including:
- Column definitions (name and type)
- Primary keys
- Foreign keys
"""

import sqlparse
import logging
import re
from typing import Dict, Any, Optional, Tuple, List

from core.exceptions import SchemaParsingError

# Set up logging
logging.basicConfig(level=logging.ERROR)

# Valid SQL data types (case-insensitive)
VALID_SQL_TYPES = {
    'INT', 'INTEGER', 'TINYINT', 'SMALLINT', 'MEDIUMINT', 'BIGINT',
    'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL',
    'CHAR', 'VARCHAR', 'TEXT', 'TINYTEXT', 'MEDIUMTEXT', 'LONGTEXT',
    'BINARY', 'VARBINARY', 'BLOB', 'TINYBLOB', 'MEDIUMBLOB', 'LONGBLOB',
    'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'YEAR',
    'BOOLEAN', 'BOOL', 'BIT', 'JSON', 'UUID'
}


def parse_sql_schema(sql_content: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse SQL schema content and extract tables, columns, primary keys, and foreign keys.
    
    Args:
        sql_content: String containing SQL CREATE TABLE statements
        
    Returns:
        Dictionary with table information:
        {
            'table_name': {
                'columns': {'col_name': 'TYPE'},
                'primary_key': 'col_name' or None,
                'foreign_keys': {'local_col': {'ref_table': 'table', 'ref_column': 'col'}}
            }
        }
    """
    result = {}

    try:
        # Parse SQL statements
        statements = sqlparse.parse(sql_content)
        
        for statement in statements:
            try:
                # Convert to string and check if it's CREATE TABLE
                stmt_str = str(statement).strip()
                if not re.match(r'^\s*CREATE\s+TABLE\s+', stmt_str, re.IGNORECASE):
                    continue
                
                # Extract table name
                table_name = _extract_table_name(stmt_str)
                if not table_name:
                    continue
                
                # Initialize table entry
            result[table_name] = {
                    'columns': {},
                    'primary_key': None,
                    'foreign_keys': {}
                }
                
                # Extract columns, primary keys, and foreign keys
                _parse_table_definition(stmt_str, result[table_name])
                
            except (ValueError, IndexError, AttributeError) as e:
                table_name = _try_get_table_name(str(statement))
                logging.error("Failed to parse table: %s - Error: %s", table_name, str(e))
                continue
                
    except Exception as e:
        logging.error("Failed to parse SQL content: %s", str(e))
        raise SchemaParsingError(f"Failed to parse SQL content: {str(e)}") from e
    
    return result


def _extract_table_name(statement_str: str) -> Optional[str]:
    """Extract table name from CREATE TABLE statement, handling backticks."""
    try:
        # Match: CREATE TABLE table_name or CREATE TABLE `table_name`
        match = re.search(r'CREATE\s+TABLE\s+[`"]?(\w+)[`"]?', statement_str, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    except (ValueError, IndexError, AttributeError) as e:
        logging.error("Error extracting table name: %s", str(e))
        return None


def _try_get_table_name(statement_str: str) -> str:
    """Try to extract table name for error logging."""
    try:
        return _extract_table_name(statement_str) or "unknown"
    except Exception:
        return "unknown"


def _parse_table_definition(statement_str: str, table_info: Dict[str, Any]) -> None:
    """Parse table definition to extract columns, primary keys, and foreign keys."""
    try:
        # Find the content inside parentheses
        match = re.search(r'CREATE\s+TABLE\s+[^(]+\(([\s\S]*)\)', statement_str, re.IGNORECASE)
        if not match:
            return
        
        table_body = match.group(1).strip()
        if not table_body:
            return
        
        # Split by commas, but handle nested parentheses (for foreign key references)
        parts = _smart_split(table_body)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            part_upper = part.upper().strip()
            
            # Skip known constraint/keyword patterns BEFORE trying to parse as column
            if _is_constraint_or_keyword(part_upper):
                # Handle PRIMARY KEY constraint
                if part_upper.startswith('PRIMARY KEY'):
                    pk_column = _extract_primary_key_column(part)
                    if pk_column:
                        table_info['primary_key'] = pk_column
                    continue
                
                # Handle FOREIGN KEY (standalone or with CONSTRAINT)
                if part_upper.startswith('FOREIGN KEY') or \
                   (part_upper.startswith('CONSTRAINT') and 'FOREIGN KEY' in part_upper) or \
                   ('REFERENCES' in part_upper and not _looks_like_column(part)):
                    fk_info = _extract_foreign_key(part)
                    if fk_info:
                        local_col, ref_table, ref_col = fk_info
                        table_info['foreign_keys'][local_col] = {
                            'ref_table': ref_table,
                            'ref_column': ref_col
                        }
                    continue
                
                # Skip other constraints (KEY, UNIQUE, CHECK, etc.)
                continue
            
            # Try to parse as column definition
            column_info = _extract_column_definition(part)
            if column_info:
                col_name, col_type, is_primary = column_info
                # Validate that we got a valid SQL type
                if _is_valid_sql_type(col_type):
                    table_info['columns'][col_name] = col_type
                    # Check for inline PRIMARY KEY
                    if is_primary and not table_info['primary_key']:
                        table_info['primary_key'] = col_name
                else:
                    logging.error("Invalid SQL type detected: %s in column definition: %s", col_type, part)
                    
    except (ValueError, IndexError, AttributeError) as e:
        logging.error("Error parsing table definition: %s", str(e))


def _is_constraint_or_keyword(part_upper: str) -> bool:
    """
    Check if a part is a constraint or keyword, not a column definition.
    
    Returns True if the part starts with known constraint keywords.
    """
    constraint_keywords = [
        'PRIMARY KEY',
        'FOREIGN KEY',
        'CONSTRAINT',
        'KEY',  # Index definition
        'UNIQUE KEY',
        'UNIQUE',
        'INDEX',
        'CHECK',
        'FULLTEXT',
        'SPATIAL',
    ]
    
    for keyword in constraint_keywords:
        if part_upper.startswith(keyword):
            return True
    
    return False


def _looks_like_column(part: str) -> bool:
    """
    Check if a part looks like a column definition (identifier + type).
    
    A column definition should start with an identifier followed by a valid SQL type.
    """
    # Pattern: identifier (with optional backticks) followed by whitespace and a type
    # This is a quick check, full validation happens in _extract_column_definition
    pattern = r'^[`"]?\w+[`"]?\s+[A-Za-z]+'
    return bool(re.match(pattern, part, re.IGNORECASE))


def _smart_split(text: str) -> List[str]:
    """Split text by commas while respecting nested parentheses."""
    parts = []
    current = ""
    depth = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif char == ',' and depth == 0:
            if current.strip():
                parts.append(current.strip())
            current = ""
        else:
            current += char
        i += 1
    
    if current.strip():
        parts.append(current.strip())
    
    return parts


def _extract_column_definition(part: str) -> Optional[Tuple[str, str, bool]]:
    """
    Extract column name and type from a column definition.
    
    Returns:
        Tuple of (column_name, column_type, is_primary) or None if parsing fails
    """
    try:
        part_clean = part.strip()
        
        # Skip if it looks like a constraint
        part_upper = part_clean.upper()
        if _is_constraint_or_keyword(part_upper):
            return None
        
        # Check for inline PRIMARY KEY
        is_primary = bool(re.search(r'\bPRIMARY\s+KEY\b', part_clean, re.IGNORECASE))
        
        # Pattern: [backtick]column_name[backtick] TYPE[(params)] [modifiers...]
        # More robust regex that requires identifier + valid type pattern
        match = re.match(
            r'^[`"]?(\w+)[`"]?\s+([A-Za-z]+(?:\s*\([^)]*\))?)', 
            part_clean, 
            re.IGNORECASE
        )
        
        if not match:
            return None
        
        col_name = match.group(1).strip('`').strip('"').strip("'")
        type_part = match.group(2)
        
        # Extract the base type and parameters (e.g., VARCHAR(100))
        # The type should be a word, optionally followed by parentheses
        type_match = re.match(r'^([A-Za-z]+)\s*(\([^)]*\))?', type_part, re.IGNORECASE)
        if not type_match:
            return None
        
        base_type = type_match.group(1).upper()
        params = type_match.group(2) if type_match.group(2) else ''
        
        # Construct the full type (e.g., VARCHAR(100))
        col_type = base_type + params
        
        # Normalize type (uppercase for consistency)
        col_type = col_type.upper()
        
        return col_name, col_type, is_primary
        
    except (ValueError, IndexError, AttributeError) as e:
        logging.error("Error extracting column definition from '%s': %s", part, str(e))
        return None


def _is_valid_sql_type(type_str: str) -> bool:
    """
    Validate that a string is a valid SQL data type.
    
    Args:
        type_str: Type string (e.g., 'INT', 'VARCHAR(100)', 'BIGINT')
    
    Returns:
        True if it's a valid SQL type
    """
    # Extract base type (remove parentheses and parameters)
    base_type = re.match(r'^([A-Za-z]+)', type_str, re.IGNORECASE)
    if not base_type:
        return False
    
    base_type_upper = base_type.group(1).upper()
    return base_type_upper in VALID_SQL_TYPES


def _extract_primary_key_column(part: str) -> Optional[str]:
    """Extract primary key column name from PRIMARY KEY constraint."""
    try:
        # Match PRIMARY KEY (column_name) - handle backticks
        match = re.search(r'PRIMARY\s+KEY\s*\([`"]?(\w+)[`"]?\)', part, re.IGNORECASE)
        if match:
            col_name = match.group(1)
            return col_name.strip('`').strip('"').strip("'")
        
        # Also try without parentheses (less common)
        match = re.search(r'PRIMARY\s+KEY\s+[`"]?(\w+)[`"]?', part, re.IGNORECASE)
        if match:
            col_name = match.group(1)
            return col_name.strip('`').strip('"').strip("'")
        
        return None
    except (ValueError, IndexError, AttributeError) as e:
        logging.error("Error extracting primary key from '%s': %s", part, str(e))
        return None


def _extract_foreign_key(part: str) -> Optional[Tuple[str, str, str]]:
    """
    Extract foreign key information: (local_col, ref_table, ref_col).
    
    Returns:
        Tuple of (local_column, referenced_table, referenced_column) or None
    """
    try:
        # Pattern 1: FOREIGN KEY (local_col) REFERENCES ref_table (ref_col)
        match = re.search(
            r'FOREIGN\s+KEY\s*\([`"]?(\w+)[`"]?\)\s+REFERENCES\s+[`"]?(\w+)[`"]?\s*\([`"]?(\w+)[`"]?\)',
            part,
            re.IGNORECASE
        )
        
        if match:
            local_col = match.group(1).strip('`').strip('"').strip("'")
            ref_table = match.group(2).strip('`').strip('"').strip("'")
            ref_col = match.group(3).strip('`').strip('"').strip("'")
            return local_col, ref_table, ref_col
        
        # Pattern 2: CONSTRAINT name FOREIGN KEY (local_col) REFERENCES ref_table (ref_col)
        # This is handled by the same pattern above since we search for FOREIGN KEY
        
        # Pattern 3: local_col REFERENCES ref_table (ref_col) - standalone (without FOREIGN KEY)
        match = re.search(
            r'^[`"]?(\w+)[`"]?\s+REFERENCES\s+[`"]?(\w+)[`"]?\s*\([`"]?(\w+)[`"]?\)',
            part,
            re.IGNORECASE
        )
        
        if match:
            local_col = match.group(1).strip('`').strip('"').strip("'")
            ref_table = match.group(2).strip('`').strip('"').strip("'")
            ref_col = match.group(3).strip('`').strip('"').strip("'")
            return local_col, ref_table, ref_col
        
        return None
    except (ValueError, IndexError, AttributeError) as e:
        logging.error("Error extracting foreign key from '%s': %s", part, str(e))
        return None
