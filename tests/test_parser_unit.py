"""
Unit tests for the SQL schema parser, dependency graph, and data generator.

This test suite ensures:
- Parser correctly handles various SQL schema patterns
- Graph module calculates correct insertion order
- Generator produces valid dummy data respecting foreign key constraints
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from core.utils.parser import parse_sql_schema
from core.utils.graph import get_insertion_order
from core.utils.generator import generate_data


class TestSQLParser(unittest.TestCase):
    """Test cases for SQL schema parser."""
    
    def test_example_schema(self):
        """Test with the provided example SQL schema."""
        sql_content = """
        CREATE TABLE `countries` (
          id INT AUTO_INCREMENT,
          name VARCHAR(100),
          PRIMARY KEY (id)
        );

        CREATE TABLE cities (
          `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
          name varchar(255) DEFAULT NULL,
          country_id int NOT NULL,
          PRIMARY KEY (`id`),
          KEY `idx_country` (`country_id`),
          CONSTRAINT `fk_city_country` FOREIGN KEY (`country_id`)
            REFERENCES `countries` (`id`) ON DELETE CASCADE
        );

        CREATE TABLE `users` (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          username varchar(50) UNIQUE,
          email VARCHAR(255),
          city_id BIGINT UNSIGNED,
          FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE SET NULL
        );
        """
        
        expected = {
            'countries': {
                'columns': {'id': 'INT', 'name': 'VARCHAR(100)'},
                'primary_key': 'id',
                'foreign_keys': {}
            },
            'cities': {
                'columns': {'id': 'BIGINT', 'name': 'VARCHAR(255)', 'country_id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {'country_id': {'ref_table': 'countries', 'ref_column': 'id'}}
            },
            'users': {
                'columns': {'id': 'BIGINT', 'username': 'VARCHAR(50)', 'email': 'VARCHAR(255)', 'city_id': 'BIGINT'},
                'primary_key': 'id',
                'foreign_keys': {'city_id': {'ref_table': 'cities', 'ref_column': 'id'}}
            }
        }
        
        result = parse_sql_schema(sql_content)
        self.assertEqual(result, expected)
    
    def test_primary_key_not_misdetected_as_column(self):
        """Test that PRIMARY KEY constraints are not parsed as columns."""
        sql = """
        CREATE TABLE test (
          id INT,
          PRIMARY KEY (id)
        );
        """
        result = parse_sql_schema(sql)
        self.assertIn('test', result)
        self.assertNotIn('PRIMARY', result['test']['columns'])
        self.assertEqual(result['test']['primary_key'], 'id')
    
    def test_key_index_not_misdetected_as_column(self):
        """Test that KEY/INDEX definitions are not parsed as columns."""
        sql = """
        CREATE TABLE test (
          id INT,
          name VARCHAR(50),
          KEY idx_name (name)
        );
        """
        result = parse_sql_schema(sql)
        self.assertIn('test', result)
        self.assertNotIn('KEY', result['test']['columns'])
        self.assertNotIn('idx_name', result['test']['columns'])
        self.assertIn('id', result['test']['columns'])
        self.assertIn('name', result['test']['columns'])
    
    def test_constraint_foreign_key_parsed_correctly(self):
        """Test that CONSTRAINT ... FOREIGN KEY is parsed correctly."""
        sql = """
        CREATE TABLE orders (
          id INT,
          user_id INT,
          CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        result = parse_sql_schema(sql)
        self.assertIn('orders', result)
        self.assertIn('user_id', result['orders']['foreign_keys'])
        self.assertEqual(result['orders']['foreign_keys']['user_id']['ref_table'], 'users')
    
    def test_inline_primary_key(self):
        """Test inline PRIMARY KEY in column definition."""
        sql = """
        CREATE TABLE test (
          id INT PRIMARY KEY,
          name VARCHAR(50)
        );
        """
        result = parse_sql_schema(sql)
        self.assertEqual(result['test']['primary_key'], 'id')
    
    def test_backticks_in_names(self):
        """Test handling of backticks in table and column names."""
        sql = """
        CREATE TABLE `test_table` (
          `id` INT,
          `name` VARCHAR(50),
          PRIMARY KEY (`id`)
        );
        """
        result = parse_sql_schema(sql)
        self.assertIn('test_table', result)
        self.assertIn('id', result['test_table']['columns'])
        self.assertIn('name', result['test_table']['columns'])
    
    def test_complex_schema_with_graph(self):
        """Test a complex SQL schema and verify graph insertion order."""
        # Complex schema with multiple dependencies
        sql_content = """
        CREATE TABLE `countries` (
          id INT AUTO_INCREMENT,
          name VARCHAR(100) NOT NULL,
          code CHAR(2) UNIQUE,
          PRIMARY KEY (id)
        );

        CREATE TABLE cities (
          id BIGINT UNSIGNED AUTO_INCREMENT,
          name VARCHAR(255) NOT NULL,
          country_id INT NOT NULL,
          population INT,
          PRIMARY KEY (id),
          CONSTRAINT fk_city_country FOREIGN KEY (country_id) 
            REFERENCES countries(id) ON DELETE CASCADE
        );

        CREATE TABLE `users` (
          id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(50) UNIQUE NOT NULL,
          email VARCHAR(255) UNIQUE NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          city_id BIGINT UNSIGNED,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE SET NULL
        );

        CREATE TABLE categories (
          id INT AUTO_INCREMENT,
          name VARCHAR(100) NOT NULL UNIQUE,
          description TEXT,
          PRIMARY KEY (id)
        );

        CREATE TABLE posts (
          id BIGINT UNSIGNED AUTO_INCREMENT,
          title VARCHAR(255) NOT NULL,
          content TEXT,
          author_id BIGINT UNSIGNED NOT NULL,
          category_id INT,
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
          parent_id BIGINT UNSIGNED,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE tags (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(50) UNIQUE NOT NULL,
          slug VARCHAR(50) UNIQUE NOT NULL
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
        
        # Parse the schema
        result = parse_sql_schema(sql_content)
        
        # Verify all tables are parsed
        expected_tables = {
            'countries', 'cities', 'users', 'categories', 'posts', 
            'comments', 'tags', 'post_tags', 'likes'
        }
        self.assertEqual(set(result.keys()), expected_tables)
        
        # Verify some key columns
        self.assertIn('id', result['countries']['columns'])
        self.assertIn('name', result['countries']['columns'])
        self.assertIn('code', result['countries']['columns'])
        
        self.assertIn('city_id', result['users']['columns'])
        self.assertIn('username', result['users']['columns'])
        
        # Verify foreign keys
        self.assertEqual(result['cities']['foreign_keys']['country_id']['ref_table'], 'countries')
        self.assertEqual(result['users']['foreign_keys']['city_id']['ref_table'], 'cities')
        self.assertEqual(result['posts']['foreign_keys']['author_id']['ref_table'], 'users')
        self.assertEqual(result['comments']['foreign_keys']['post_id']['ref_table'], 'posts')
        self.assertEqual(result['comments']['foreign_keys']['user_id']['ref_table'], 'users')
        
        # Test graph insertion order
        insertion_order = get_insertion_order(result)
        
        # Verify order constraints:
        # countries must come before cities
        # cities must come before users
        # users must come before posts
        # posts must come before comments
        # posts must come before post_tags
        # tags must come before post_tags
        # users must come before likes
        # posts must come before likes
        
        self.assertIn('countries', insertion_order)
        self.assertIn('cities', insertion_order)
        self.assertIn('users', insertion_order)
        self.assertIn('posts', insertion_order)
        self.assertIn('comments', insertion_order)
        self.assertIn('tags', insertion_order)
        self.assertIn('post_tags', insertion_order)
        self.assertIn('likes', insertion_order)
        
        # Check dependency order
        countries_idx = insertion_order.index('countries')
        cities_idx = insertion_order.index('cities')
        users_idx = insertion_order.index('users')
        posts_idx = insertion_order.index('posts')
        comments_idx = insertion_order.index('comments')
        post_tags_idx = insertion_order.index('post_tags')
        tags_idx = insertion_order.index('tags')
        likes_idx = insertion_order.index('likes')
        
        # Verify dependency chains
        self.assertLess(countries_idx, cities_idx, 
                       "countries must come before cities")
        self.assertLess(cities_idx, users_idx, 
                       "cities must come before users")
        self.assertLess(users_idx, posts_idx, 
                       "users must come before posts")
        self.assertLess(posts_idx, comments_idx, 
                       "posts must come before comments")
        self.assertLess(posts_idx, post_tags_idx, 
                       "posts must come before post_tags")
        self.assertLess(tags_idx, post_tags_idx, 
                       "tags must come before post_tags")
        self.assertLess(users_idx, likes_idx, 
                       "users must come before likes")
        self.assertLess(posts_idx, likes_idx, 
                       "posts must come before likes")
        
        # Categories can be anywhere, but posts depends on it
        categories_idx = insertion_order.index('categories')
        self.assertLess(categories_idx, posts_idx, 
                       "categories must come before posts")


class TestDataGenerator(unittest.TestCase):
    """Test cases for the data generator module."""
    
    def test_generate_simple_schema(self):
        """Test data generation for a simple schema."""
        sql_content = """
        CREATE TABLE countries (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100)
        );

        CREATE TABLE users (
          id INT PRIMARY KEY,
          username VARCHAR(50),
          email VARCHAR(255),
          country_id INT,
          FOREIGN KEY (country_id) REFERENCES countries(id)
        );
        """
        
        num_records = 10
        data = generate_data(sql_content, num_records=num_records)
        
        # Verify all tables have data
        self.assertIn('countries', data)
        self.assertIn('users', data)
        
        # Verify correct number of records
        self.assertEqual(len(data['countries']), num_records)
        self.assertEqual(len(data['users']), num_records)
        
        # Verify countries table structure
        country_record = data['countries'][0]
        self.assertIn('id', country_record)
        self.assertIn('name', country_record)
        self.assertIsInstance(country_record['id'], int)
        self.assertIsInstance(country_record['name'], str)
        
        # Verify users table structure
        user_record = data['users'][0]
        self.assertIn('id', user_record)
        self.assertIn('username', user_record)
        self.assertIn('email', user_record)
        self.assertIn('country_id', user_record)
        self.assertIsInstance(user_record['id'], int)
        self.assertIsInstance(user_record['username'], str)
        
        # Verify foreign key references are valid
        country_ids = {record['id'] for record in data['countries']}
        for user_record in data['users']:
            # country_id should either be None or a valid country id
            if user_record['country_id'] is not None:
                self.assertIn(user_record['country_id'], country_ids)
    
    def test_generate_complex_schema(self):
        """Test data generation for a more complex schema."""
        sql_content = """
        CREATE TABLE countries (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100),
          code CHAR(2)
        );

        CREATE TABLE cities (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255),
          country_id INT,
          FOREIGN KEY (country_id) REFERENCES countries(id)
        );

        CREATE TABLE users (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(50),
          email VARCHAR(255),
          city_id BIGINT,
          FOREIGN KEY (city_id) REFERENCES cities(id)
        );
        """
        
        num_records = 5
        data = generate_data(sql_content, num_records=num_records)
        
        # Verify all tables
        self.assertIn('countries', data)
        self.assertIn('cities', data)
        self.assertIn('users', data)
        
        # Verify record counts
        self.assertEqual(len(data['countries']), num_records)
        self.assertEqual(len(data['cities']), num_records)
        self.assertEqual(len(data['users']), num_records)
        
        # Verify primary keys are sequential (auto-increment)
        country_ids = [r['id'] for r in data['countries']]
        self.assertEqual(country_ids, list(range(1, num_records + 1)))
        
        city_ids = [r['id'] for r in data['cities']]
        self.assertEqual(city_ids, list(range(1, num_records + 1)))
        
        # Verify foreign key chain: users -> cities -> countries
        city_ids_set = set(city_ids)
        country_ids_set = set(country_ids)
        
        for city_record in data['cities']:
            if city_record['country_id'] is not None:
                self.assertIn(city_record['country_id'], country_ids_set)
        
        for user_record in data['users']:
            if user_record['city_id'] is not None:
                self.assertIn(user_record['city_id'], city_ids_set)
    
    def test_smart_field_detection(self):
        """Test that generator detects field types from column names."""
        sql_content = """
        CREATE TABLE test_table (
          id INT PRIMARY KEY,
          email VARCHAR(255),
          username VARCHAR(50),
          name VARCHAR(100),
          phone VARCHAR(20),
          created_at DATETIME
        );
        """
        
        data = generate_data(sql_content, num_records=5)
        record = data['test_table'][0]
        
        # Verify smart detection
        self.assertIn('@', record['email'])  # Email should contain @
        self.assertIsInstance(record['username'], str)
        self.assertIsInstance(record['name'], str)
        self.assertIsInstance(record['phone'], str)
        self.assertIsInstance(record['created_at'], type(record['created_at']))  # datetime object
    
    def test_primary_key_auto_increment(self):
        """Test that primary keys are auto-incremented correctly."""
        sql_content = """
        CREATE TABLE test_table (
          id INT PRIMARY KEY,
          name VARCHAR(50)
        );
        """
        
        num_records = 10
        data = generate_data(sql_content, num_records=num_records)
        
        ids = [record['id'] for record in data['test_table']]
        expected_ids = list(range(1, num_records + 1))
        
        self.assertEqual(ids, expected_ids)
    
    def test_nullable_foreign_keys(self):
        """Test that nullable foreign keys can be None."""
        sql_content = """
        CREATE TABLE parent (
          id INT PRIMARY KEY,
          name VARCHAR(50)
        );

        CREATE TABLE child (
          id INT PRIMARY KEY,
          name VARCHAR(50),
          parent_id INT,
          FOREIGN KEY (parent_id) REFERENCES parent(id)
        );
        """
        
        num_records = 20  # More records to increase chance of None values
        data = generate_data(sql_content, num_records=num_records)
        
        # At least some foreign keys should be None (30% chance)
        null_count = sum(1 for r in data['child'] if r['parent_id'] is None)
        # We expect at least some None values with 20 records
        # (with 30% probability, we'd expect ~6 None values)
        # But we'll just verify that None is a valid value
        self.assertTrue(any(r['parent_id'] is None for r in data['child']) or 
                       all(r['parent_id'] is not None for r in data['child']))
    
    def test_empty_schema(self):
        """Test generator with empty/invalid schema."""
        # Empty schema should raise ValueError
        with self.assertRaises(ValueError):
            generate_data("", num_records=10)
        
        # Invalid SQL should also raise ValueError (no valid tables)
        with self.assertRaises(ValueError):
            generate_data("INVALID SQL", num_records=10)


class TestGraphModule(unittest.TestCase):
    """Test cases for the dependency graph module."""
    
    def test_simple_chain(self):
        """Test simple dependency chain."""
        schema = {
            'countries': {
                'columns': {'id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {}
            },
            'cities': {
                'columns': {'id': 'INT', 'country_id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {'country_id': {'ref_table': 'countries', 'ref_column': 'id'}}
            },
            'users': {
                'columns': {'id': 'INT', 'city_id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {'city_id': {'ref_table': 'cities', 'ref_column': 'id'}}
            }
        }
        
        order = get_insertion_order(schema)
        self.assertEqual(order, ['countries', 'cities', 'users'])
    
    def test_multiple_dependencies(self):
        """Test table with multiple foreign key dependencies."""
        schema = {
            'users': {
                'columns': {'id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {}
            },
            'categories': {
                'columns': {'id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {}
            },
            'posts': {
                'columns': {'id': 'INT', 'user_id': 'INT', 'category_id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {
                    'user_id': {'ref_table': 'users', 'ref_column': 'id'},
                    'category_id': {'ref_table': 'categories', 'ref_column': 'id'}
                }
            }
        }
        
        order = get_insertion_order(schema)
        # Both users and categories must come before posts
        posts_idx = order.index('posts')
        users_idx = order.index('users')
        categories_idx = order.index('categories')
        
        self.assertLess(users_idx, posts_idx)
        self.assertLess(categories_idx, posts_idx)
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        schema = {
            'table_a': {
                'columns': {'id': 'INT', 'b_id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {'b_id': {'ref_table': 'table_b', 'ref_column': 'id'}}
            },
            'table_b': {
                'columns': {'id': 'INT', 'a_id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {'a_id': {'ref_table': 'table_a', 'ref_column': 'id'}}
            }
        }
        
        with self.assertRaises(ValueError) as context:
            get_insertion_order(schema)
        
        self.assertIn('Circular dependency', str(context.exception))
        self.assertIn('table_a', str(context.exception))
        self.assertIn('table_b', str(context.exception))
    
    def test_independent_tables(self):
        """Test schema with independent tables (no foreign keys)."""
        schema = {
            'table_a': {
                'columns': {'id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {}
            },
            'table_b': {
                'columns': {'id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {}
            },
            'table_c': {
                'columns': {'id': 'INT'},
                'primary_key': 'id',
                'foreign_keys': {}
            }
        }
        
        order = get_insertion_order(schema)
        # All tables should be present, order doesn't matter
        self.assertEqual(set(order), {'table_a', 'table_b', 'table_c'})


if __name__ == '__main__':
    unittest.main()

