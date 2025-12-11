import sqlparse
import logging
import re
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.ERROR)


def parse_sql_schema(sql_content: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse SQL schema content and extract tables, columns, primary keys, and foreign keys.
    
    Args:
        sql_content: String containing SQL CREATE TABLE statements
        
    Returns:
        Dictionary with table information
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
        return result
    
    return result


def _extract_table_name(statement_str):
    """Extract table name from CREATE TABLE statement, handling backticks."""
    try:
        # Match: CREATE TABLE table_name or CREATE TABLE `table_name`
        match = re.search(r'CREATE\s+TABLE\s+[`"]?(\w+)[`"]?', statement_str, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    except (ValueError, IndexError, AttributeError):
        return None


def _try_get_table_name(statement_str):
    """Try to extract table name for error logging."""
    try:
        return _extract_table_name(statement_str) or "unknown"
    except:
        return "unknown"


def _parse_table_definition(statement_str, table_info):
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
            
            # Check for PRIMARY KEY constraint
            if part_upper.startswith('PRIMARY KEY'):
                pk_column = _extract_primary_key_column(part)
                if pk_column:
                    table_info['primary_key'] = pk_column
                continue
            
            # Check for FOREIGN KEY
            if part_upper.startswith('FOREIGN KEY') or ('REFERENCES' in part_upper and not part_upper.startswith('CONSTRAINT')):
                fk_info = _extract_foreign_key(part)
                if fk_info:
                    local_col, ref_table, ref_col = fk_info
                    table_info['foreign_keys'][local_col] = {
                        'ref_table': ref_table,
                        'ref_column': ref_col
                    }
                continue
            
            # Check for CONSTRAINT ... FOREIGN KEY
            if 'REFERENCES' in part_upper and part_upper.startswith('CONSTRAINT'):
                fk_info = _extract_foreign_key(part)
                if fk_info:
                    local_col, ref_table, ref_col = fk_info
                    table_info['foreign_keys'][local_col] = {
                        'ref_table': ref_table,
                        'ref_column': ref_col
                    }
                continue
            
            # Otherwise, it's a column definition
            column_info = _extract_column_definition(part)
            if column_info:
                col_name, col_type, is_primary = column_info
                table_info['columns'][col_name] = col_type
                # Check for inline PRIMARY KEY
                if is_primary and not table_info['primary_key']:
                    table_info['primary_key'] = col_name
                    
    except (ValueError, IndexError, AttributeError) as e:
        logging.error("Error parsing table definition: %s", str(e))


def _smart_split(text):
    """Split text by commas while respecting parentheses."""
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


def _extract_column_definition(part):
    """Extract column name and type from a column definition."""
    try:
        part_clean = part.strip()
        
        # Check for PRIMARY KEY in the column definition
        is_primary = False
        if re.search(r'\bPRIMARY\s+KEY\b', part_clean, re.IGNORECASE):
            is_primary = True
        
        # Remove common keywords that might interfere
        # Match: [backtick]name[backtick] TYPE [constraints...]
        # More robust pattern to extract column name and type
        match = re.match(r'^[`"]?(\w+)[`"]?\s+([A-Za-z]+(?:\s*\([^)]*\))?(?:\s+\w+)*)', part_clean, re.IGNORECASE)
        if not match:
            # Try simpler pattern
            match = re.match(r'^[`"]?(\w+)[`"]?\s+(\w+(?:\s*\([^)]*\))?)', part_clean, re.IGNORECASE)
        
        if match:
            col_name = match.group(1)
            # Extract type part (everything after name until PRIMARY KEY, FOREIGN KEY, or end)
            type_part = part_clean[len(col_name):].strip()
            # Remove backticks from column name if present
            col_name = col_name.strip('`').strip('"').strip("'")
            
            # Extract type - take first word(s) before any constraint keywords
            type_match = re.match(r'^([A-Za-z]+\s*(?:\([^)]*\))?(?:\s+(?:UNSIGNED|AUTO_INCREMENT|NOT NULL|NULL))?)', type_part, re.IGNORECASE)
            if type_match:
                col_type = type_match.group(1).strip()
            else:
                # Fallback: take first few words
                words = type_part.split()
                if words:
                    col_type = words[0]
                else:
                    col_type = "UNKNOWN"
            
            # Clean up type - remove AUTO_INCREMENT, UNSIGNED, NOT NULL etc.
            col_type = re.sub(r'\s+(AUTO_INCREMENT|UNSIGNED|NOT\s+NULL|NULL)\b', '', col_type, flags=re.IGNORECASE)
            col_type = col_type.strip()
            
            return col_name, col_type, is_primary
        
        return None
    except (ValueError, IndexError, AttributeError):
        return None


def _extract_primary_key_column(part):
    """Extract primary key column name from PRIMARY KEY constraint."""
    try:
        # Match PRIMARY KEY (column_name) or PRIMARY KEY column_name
        # Also handle backticks
        match = re.search(r'PRIMARY\s+KEY\s*\(?[`"]?(\w+)[`"]?\)?', part, re.IGNORECASE)
        if match:
            col_name = match.group(1)
            return col_name.strip('`').strip('"').strip("'")
        return None
    except (ValueError, IndexError, AttributeError):
        return None


def _extract_foreign_key(part):
    """Extract foreign key information: (local_col, ref_table, ref_col)."""
    try:
        # Match patterns:
        # 1. FOREIGN KEY (local_col) REFERENCES ref_table (ref_col)
        # 2. local_col REFERENCES ref_table (ref_col)
        # 3. CONSTRAINT name FOREIGN KEY (local_col) REFERENCES ref_table (ref_col)
        
        # First try: FOREIGN KEY (col) REFERENCES table (ref_col)
        match = re.search(
            r'FOREIGN\s+KEY\s*\([`"]?(\w+)[`"]?\)\s+REFERENCES\s+[`"]?(\w+)[`"]?\s*\([`"]?(\w+)[`"]?\)',
            part,
            re.IGNORECASE
        )
        
        if not match:
            # Second try: col REFERENCES table (ref_col) - without FOREIGN KEY keyword
            match = re.search(
                r'([`"]?\w+[`"]?)\s+REFERENCES\s+[`"]?(\w+)[`"]?\s*\([`"]?(\w+)[`"]?\)',
                part,
                re.IGNORECASE
            )
        
        if match:
            local_col = match.group(1)
            ref_table = match.group(2)
            ref_col = match.group(3)
            # Remove backticks if present
            local_col = local_col.strip('`').strip('"').strip("'")
            ref_table = ref_table.strip('`').strip('"').strip("'")
            ref_col = ref_col.strip('`').strip('"').strip("'")
            return local_col, ref_table, ref_col
        return None
    except (ValueError, IndexError, AttributeError):
        return None
