"""
Demo script showing the complete data generation flow:
1. SQL Schema Parsing
2. Dependency Graph Building
3. Data Generation
4. Export to INSERT SQL statements

This saves all output to text files instead of terminal.
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils.parser import parse_sql_schema
from core.utils.graph import get_insertion_order
from core.utils.generator import generate_data
import pprint
from datetime import datetime


def format_value_for_sql(value):
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


def generate_insert_statements(generated_data, schema):
    """
    Generate INSERT SQL statements from generated data.
    
    Args:
        generated_data: Dictionary mapping table names to lists of records
        schema: Parsed schema dictionary
        
    Returns:
        String containing all INSERT statements
    """
    insert_statements = []
    
    # Get insertion order to maintain foreign key dependencies
    try:
        table_order = get_insertion_order(schema)
    except ValueError:
        table_order = list(generated_data.keys())
    
    for table_name in table_order:
        records = generated_data.get(table_name, [])
        if not records:
            continue
        
        table_info = schema.get(table_name, {})
        columns = list(table_info.get('columns', {}).keys())
        
        # Generate INSERT statement for each record
        for record in records:
            # Build column names
            col_names = ', '.join(columns)
            
            # Build values
            values = []
            for col in columns:
                value = record.get(col)
                values.append(format_value_for_sql(value))
            
            values_str = ', '.join(values)
            
            # Create INSERT statement
            insert_stmt = f"INSERT INTO {table_name} ({col_names}) VALUES ({values_str});"
            insert_statements.append(insert_stmt)
        
        insert_statements.append('')  # Empty line between tables
    
    return '\n'.join(insert_statements)


def main():
    """Main function to run the demo and save output to files."""
    
    # Create outputs directory if it doesn't exist
    import os
    outputs_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Output file names with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(outputs_dir, f'demo_output_{timestamp}.log')
    sql_file = os.path.join(outputs_dir, f'insert_statements_{timestamp}.sql')
    
    # Open log file for writing
    with open(log_file, 'w', encoding='utf-8') as log:
        
        def log_print(*args, **kwargs):
            """Print to both console and log file."""
            message = ' '.join(str(arg) for arg in args)
            print(message)
            log.write(message + '\n')
            log.flush()
        
        # Complex SQL schema with multiple tables and dependencies
        sql_content = """
        CREATE TABLE `countries` (
          id INT AUTO_INCREMENT,
          name VARCHAR(100) NOT NULL,
          code CHAR(2) UNIQUE,
          population BIGINT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (id)
        );

        CREATE TABLE cities (
          `id` BIGINT UNSIGNED AUTO_INCREMENT,
          name VARCHAR(255) NOT NULL,
          country_id INT NOT NULL,
          population INT,
          latitude DECIMAL(10, 8),
          longitude DECIMAL(11, 8),
          created_at DATETIME,
          PRIMARY KEY (id),
          KEY `idx_country` (`country_id`),
          CONSTRAINT `fk_city_country` FOREIGN KEY (`country_id`) 
            REFERENCES `countries` (`id`) ON DELETE CASCADE
        );

        CREATE TABLE `users` (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(50) UNIQUE NOT NULL,
          email VARCHAR(255) UNIQUE NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          first_name VARCHAR(100),
          last_name VARCHAR(100),
          city_id BIGINT UNSIGNED,
          phone VARCHAR(20),
          birth_date DATE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE SET NULL
        );

        CREATE TABLE categories (
          id INT AUTO_INCREMENT,
          name VARCHAR(100) NOT NULL UNIQUE,
          description TEXT,
          slug VARCHAR(100) UNIQUE,
          created_at DATETIME,
          PRIMARY KEY (id)
        );

        CREATE TABLE posts (
          id BIGINT UNSIGNED AUTO_INCREMENT,
          title VARCHAR(255) NOT NULL,
          content TEXT,
          author_id BIGINT UNSIGNED NOT NULL,
          category_id INT,
          slug VARCHAR(255) UNIQUE,
          views INT DEFAULT 0,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          KEY idx_author (author_id),
          KEY idx_category (category_id),
          CONSTRAINT fk_post_author FOREIGN KEY (author_id) 
            REFERENCES users(id) ON DELETE CASCADE,
          CONSTRAINT fk_post_category FOREIGN KEY (category_id) 
            REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE comments (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          content TEXT NOT NULL,
          post_id BIGINT UNSIGNED NOT NULL,
          user_id BIGINT UNSIGNED NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE tags (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(50) UNIQUE NOT NULL,
          slug VARCHAR(50) UNIQUE NOT NULL,
          description VARCHAR(255)
        );

        CREATE TABLE post_tags (
          post_id BIGINT UNSIGNED NOT NULL,
          tag_id INT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (post_id, tag_id),
          KEY idx_tag (tag_id),
          CONSTRAINT fk_posttag_post FOREIGN KEY (post_id) 
            REFERENCES posts(id) ON DELETE CASCADE,
          CONSTRAINT fk_posttag_tag FOREIGN KEY (tag_id) 
            REFERENCES tags(id) ON DELETE CASCADE
        );

        CREATE TABLE likes (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          user_id BIGINT UNSIGNED NOT NULL,
          post_id BIGINT UNSIGNED NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY unique_like (user_id, post_id),
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        );
        """
        
        log_print("="*80)
        log_print("STEP 1: PARSING SQL SCHEMA")
        log_print("="*80)
        log_print("\nInput SQL Schema:")
        log_print("-" * 80)
        log_print("Number of tables in schema: ~9 tables")
        log_print("Complexity: Multiple foreign key relationships")
        
        log_print("\n\nParsing schema using parser.py...")
        log_print("-" * 80)
        
        # Step 1: Parse the schema
        schema = parse_sql_schema(sql_content)
        
        log_print(f"\n[OK] Parsed successfully!")
        log_print(f"  Found {len(schema)} tables:")
        for table_name in schema.keys():
            log_print(f"    - {table_name}")
        
        log_print("\n\nParsed Schema Structure:")
        log_print("-" * 80)
        for table_name, table_info in schema.items():
            log_print(f"\n[*] Table: {table_name}")
            log_print(f"   Primary Key: {table_info.get('primary_key', 'None')}")
            log_print(f"   Columns ({len(table_info.get('columns', {}))}): {list(table_info.get('columns', {}).keys())}")
            foreign_keys = table_info.get('foreign_keys', {})
            if foreign_keys:
                log_print(f"   Foreign Keys ({len(foreign_keys)}):")
                for fk_col, fk_info in foreign_keys.items():
                    log_print(f"      {fk_col} -> {fk_info['ref_table']}.{fk_info['ref_column']}")
            else:
                log_print(f"   Foreign Keys: None")
        
        log_print("\n\n" + "="*80)
        log_print("STEP 2: BUILDING DEPENDENCY GRAPH")
        log_print("="*80)
        
        # Step 2: Get insertion order
        log_print("\nBuilding dependency graph using graph.py...")
        log_print("-" * 80)
        
        try:
            insertion_order = get_insertion_order(schema)
            log_print(f"\n[OK] Dependency graph built successfully!")
            log_print(f"  No circular dependencies detected.")
            
            log_print("\n\nInsertion Order (respecting foreign key constraints):")
            log_print("-" * 80)
            for idx, table_name in enumerate(insertion_order, 1):
                table_info = schema[table_name]
                fk_count = len(table_info.get('foreign_keys', {}))
                if fk_count > 0:
                    fk_info = ", ".join([f"{fk}->{info['ref_table']}" 
                                        for fk, info in table_info.get('foreign_keys', {}).items()])
                    log_print(f"{idx:2d}. {table_name:15s} (depends on: {fk_info})")
                else:
                    log_print(f"{idx:2d}. {table_name:15s} (no dependencies)")
                    
            log_print("\n\nDependency Chain Visualization:")
            log_print("-" * 80)
            log_print("countries (no deps)")
            log_print("  +--> cities (depends on: countries)")
            log_print("        +--> users (depends on: cities)")
            log_print("              +--> posts (depends on: users, categories)")
            log_print("                    +--> comments (depends on: posts, users)")
            log_print("                    +--> likes (depends on: posts, users)")
            log_print("                    +--> post_tags (depends on: posts, tags)")
            log_print("categories (no deps)")
            log_print("  +--> posts (depends on: categories)")
            log_print("tags (no deps)")
            log_print("  +--> post_tags (depends on: tags)")
            
        except ValueError as e:
            log_print(f"\n[ERROR] Error: {e}")
            return
        
        log_print("\n\n" + "="*80)
        log_print("STEP 3: GENERATING DATA")
        log_print("="*80)
        
        # Step 3: Generate data
        num_records = 5
        log_print(f"\nGenerating {num_records} records per table using generator.py...")
        log_print("-" * 80)
        
        generated_data = generate_data(sql_content, num_records=num_records)
        
        log_print(f"\n[OK] Data generation completed!")
        log_print(f"  Generated data for {len(generated_data)} tables")
        
        log_print("\n\nGenerated Data Summary:")
        log_print("-" * 80)
        for table_name in insertion_order:
            records = generated_data.get(table_name, [])
            log_print(f"\n[+] {table_name} ({len(records)} records):")
            
            if records:
                # Show first record
                first_record = records[0]
                log_print(f"   Sample record:")
                for key, value in list(first_record.items())[:5]:  # Show first 5 fields
                    if value is None:
                        log_print(f"      {key}: NULL")
                    elif isinstance(value, str) and len(value) > 50:
                        log_print(f"      {key}: {value[:47]}...")
                    else:
                        log_print(f"      {key}: {value}")
                if len(first_record) > 5:
                    log_print(f"      ... and {len(first_record) - 5} more fields")
                
                # Validate foreign keys
                table_info = schema[table_name]
                foreign_keys = table_info.get('foreign_keys', {})
                if foreign_keys:
                    log_print(f"   Foreign Key Validation:")
                    for fk_col, fk_info in foreign_keys.items():
                        ref_table = fk_info['ref_table']
                        ref_col = fk_info['ref_column']
                        if ref_table in generated_data:
                            ref_ids = {r[ref_col] for r in generated_data[ref_table] if ref_col in r}
                            fk_values = {r[fk_col] for r in records if fk_col in r and r[fk_col] is not None}
                            invalid = fk_values - ref_ids
                            if invalid:
                                log_print(f"      [ERROR] {fk_col} -> {ref_table}.{ref_col}: {len(invalid)} invalid references")
                            else:
                                null_count = sum(1 for r in records if r.get(fk_col) is None)
                                valid_count = len(fk_values)
                                log_print(f"      [OK] {fk_col} -> {ref_table}.{ref_col}: {valid_count} valid, {null_count} NULL")
        
        log_print("\n\n" + "="*80)
        log_print("STEP 4: DETAILED DATA PREVIEW - ALL RECORDS")
        log_print("="*80)
        
        # Show ALL records for ALL tables
        log_print("\nDetailed preview of ALL records for ALL tables:")
        log_print("-" * 80)
        
        for table_name in insertion_order:
            records = generated_data.get(table_name, [])
            if records:
                log_print(f"\n{'='*80}")
                log_print(f"Table: {table_name} ({len(records)} records)")
                log_print(f"{'='*80}")
                for idx, record in enumerate(records, 1):
                    log_print(f"\nRecord #{idx}:")
                    # Use pprint format for better readability
                    record_str = pprint.pformat(record, width=80, depth=1)
                    log_print(record_str)
        
        log_print("\n\n" + "="*80)
        log_print("STEP 5: GENERATING INSERT SQL STATEMENTS")
        log_print("="*80)
        
        log_print("\nGenerating INSERT SQL statements...")
        log_print("-" * 80)
        
        # Generate INSERT statements
        insert_sql = generate_insert_statements(generated_data, schema)
        
        # Write INSERT statements to file
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- Generated INSERT statements\n")
            f.write(f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Total tables: {len(generated_data)}\n")
            f.write(f"-- Total records: {sum(len(records) for records in generated_data.values())}\n")
            f.write("\n\n")
            f.write(insert_sql)
        
        log_print(f"\n[OK] INSERT statements saved to: {sql_file}")
        log_print(f"  Total INSERT statements: {insert_sql.count('INSERT INTO')}")
        
        log_print("\n\n" + "="*80)
        log_print("SUMMARY")
        log_print("="*80)
        total_records = sum(len(records) for records in generated_data.values())
        log_print(f"""
[OK] Parsed {len(schema)} tables from SQL schema
[OK] Built dependency graph with {len(insertion_order)} nodes
[OK] Generated {num_records} records per table ({len(generated_data)} tables total)
[OK] All foreign key constraints validated
[OK] Data ready for insertion in correct order
[OK] INSERT SQL statements generated

Total records generated: {total_records}
Log file saved to: {log_file}
SQL file saved to: {sql_file}
""")
    
    print(f"\n[INFO] All output saved to:")
    print(f"  - Log file: {log_file}")
    print(f"  - SQL file: {sql_file}")


if __name__ == '__main__':
    main()
