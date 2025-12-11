"""
Example usage of the new SchemaService architecture.

This demonstrates how to use the Service Layer pattern.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.services.schema_service import SchemaService
from core.utils.generators.config import GeneratorConfig

# Example SQL schema
sql_content = """
CREATE TABLE countries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  code CHAR(2)
);

CREATE TABLE users (
  id INT PRIMARY KEY,
  username VARCHAR(50),
  email VARCHAR(255),
  country_id INT,
  FOREIGN KEY (country_id) REFERENCES countries(id)
);
"""

def main():
    print("="*80)
    print("Example 1: Using default configuration")
    print("="*80)
    
    # Create service with default config
    service = SchemaService()
    
    # Process schema and generate data
    result = service.process_schema(sql_content, num_records=5, export_sql=True)
    
    print(f"\nParsed {result['metadata']['total_tables']} tables")
    print(f"Generated {result['metadata']['total_records']} records")
    print(f"\nInsertion order: {result['insertion_order']}")
    print(f"\nSQL output length: {len(result['sql'])} characters")
    
    print("\n" + "="*80)
    print("Example 2: Using custom configuration")
    print("="*80)
    
    # Create custom config
    config = GeneratorConfig(
        locale='en_US',
        seed=42,  # For reproducible data
        nullable_fk_probability=0.2  # 20% chance of NULL foreign keys
    )
    
    service2 = SchemaService(generator_config=config)
    result2 = service2.process_schema(sql_content, num_records=3)
    
    print(f"\nGenerated {result2['metadata']['total_records']} records with seed=42")
    print("\nSample data from 'users' table:")
    for i, record in enumerate(result2['data']['users'][:2], 1):
        print(f"  User {i}: {record}")
    
    print("\n" + "="*80)
    print("Example 3: Using individual methods")
    print("="*80)
    
    # Parse only
    parse_result = service.parse_only(sql_content)
    print(f"\nParsed schema: {list(parse_result['schema'].keys())}")
    print(f"Has cycles: {parse_result['has_cycles']}")
    
    # Generate only
    data = service.generate_only(sql_content, num_records=2)
    print(f"\nGenerated data for {len(data)} tables")
    
    # Export only
    sql = service.export_only(
        data=data,
        schema=parse_result['schema'],
        insertion_order=parse_result['insertion_order']
    )
    print(f"\nExported SQL: {len(sql)} characters")
    
    print("\n" + "="*80)
    print("All examples completed successfully!")
    print("="*80)


if __name__ == '__main__':
    main()

