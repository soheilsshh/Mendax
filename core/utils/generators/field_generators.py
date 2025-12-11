"""
Field generators using Strategy Pattern.

Each field type has its own generator strategy.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Optional
from faker import Faker

from core.utils.generators.config import GeneratorConfig


class FieldGenerator(ABC):
    """Base class for field value generators."""
    
    def __init__(self, faker: Faker):
        self.faker = faker
    
    @abstractmethod
    def can_handle(self, col_name: str, col_type: str) -> bool:
        """Check if this generator can handle the given column."""
        pass
    
    @abstractmethod
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        """Generate a value for the column."""
        pass


class PrimaryKeyGenerator(FieldGenerator):
    """Generator for primary key fields."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        return False  # Handled separately
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        if not is_primary_key:
            return None
        
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        
        if base_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'MEDIUMINT']:
            return record_num + 1  # Auto-increment
        elif base_type in ['VARCHAR', 'CHAR', 'TEXT']:
            return self.faker.uuid4()
        else:
            return record_num + 1


class SmartFieldGenerator(FieldGenerator):
    """Generator that detects field type from column name."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        col_name_lower = col_name.lower()
        smart_keywords = [
            'email', 'username', 'name', 'phone', 'url', 'address',
            'city', 'country', 'password', 'hash', 'created_at', 'updated_at',
            'date', 'time', 'description', 'content', 'text', 'title',
            'slug', 'code'
        ]
        return any(keyword in col_name_lower for keyword in smart_keywords)
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        col_name_lower = col_name.lower()
        
        if 'email' in col_name_lower:
            return self.faker.email()
        elif 'username' in col_name_lower:
            return self.faker.user_name()
        elif 'name' in col_name_lower and 'user' not in col_name_lower:
            return self.faker.name()
        elif 'phone' in col_name_lower:
            return self.faker.phone_number()
        elif 'url' in col_name_lower or 'link' in col_name_lower:
            return self.faker.url()
        elif 'address' in col_name_lower:
            return self.faker.address()
        elif 'city' in col_name_lower and 'id' not in col_name_lower:
            return self.faker.city()
        elif 'country' in col_name_lower and 'id' not in col_name_lower:
            return self.faker.country()
        elif 'password' in col_name_lower or 'hash' in col_name_lower:
            return self.faker.password(length=20)
        elif 'created_at' in col_name_lower or 'updated_at' in col_name_lower:
            return self.faker.date_time_between(start_date='-1y', end_date='now')
        elif 'date' in col_name_lower and 'id' not in col_name_lower:
            return self.faker.date()
        elif 'time' in col_name_lower and 'id' not in col_name_lower:
            return self.faker.time()
        elif 'description' in col_name_lower or 'content' in col_name_lower or 'text' in col_name_lower:
            return self.faker.text(max_nb_chars=200)
        elif 'title' in col_name_lower:
            return self.faker.sentence(nb_words=3)
        elif 'slug' in col_name_lower:
            return self.faker.slug()
        elif 'code' in col_name_lower and 'id' not in col_name_lower:
            return self.faker.country_code()
        
        return None  # Fallback to type-based generator


class IntegerFieldGenerator(FieldGenerator):
    """Generator for integer types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'MEDIUMINT']
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        if 'unsigned' in col_type.upper():
            return self.faker.random_int(min=0, max=2147483647)
        return self.faker.random_int(min=-2147483648, max=2147483647)


class DecimalFieldGenerator(FieldGenerator):
    """Generator for decimal/numeric types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type in ['DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL']
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        length_match = re.search(r'\((\d+)\)', col_type.upper())
        max_length = int(length_match.group(1)) if length_match else None
        
        if max_length:
            return round(self.faker.pyfloat(left_digits=max_length-2, right_digits=2), 2)
        return self.faker.pyfloat(left_digits=10, right_digits=2)


class StringFieldGenerator(FieldGenerator):
    """Generator for string types (VARCHAR, CHAR, TEXT)."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type in ['VARCHAR', 'CHAR', 'TEXT', 'TINYTEXT', 'MEDIUMTEXT', 'LONGTEXT']
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        length_match = re.search(r'\((\d+)\)', col_type.upper())
        max_length = int(length_match.group(1)) if length_match else None
        
        if base_type in ['VARCHAR', 'CHAR']:
            if max_length:
                if max_length <= 10:
                    return self.faker.word()[:max_length]
                elif max_length <= 50:
                    return self.faker.text(max_nb_chars=max_length).strip()
                else:
                    return self.faker.text(max_nb_chars=max_length).strip()
            return self.faker.text(max_nb_chars=50).strip()
        else:  # TEXT types
            return self.faker.text(max_nb_chars=500)


class DateTimeFieldGenerator(FieldGenerator):
    """Generator for date/time types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type in ['DATE', 'DATETIME', 'TIMESTAMP', 'TIME', 'YEAR']
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        
        if base_type == 'DATE':
            return self.faker.date()
        elif base_type in ['DATETIME', 'TIMESTAMP']:
            return self.faker.date_time_between(start_date='-1y', end_date='now')
        elif base_type == 'TIME':
            return self.faker.time()
        elif base_type == 'YEAR':
            return self.faker.year()
        
        return self.faker.date()


class BooleanFieldGenerator(FieldGenerator):
    """Generator for boolean types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type in ['BOOLEAN', 'BOOL', 'BIT']
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        if base_type == 'BIT':
            return self.faker.random_int(min=0, max=1)
        return self.faker.boolean()


class JSONFieldGenerator(FieldGenerator):
    """Generator for JSON types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type == 'JSON'
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        return self.faker.json()


class UUIDFieldGenerator(FieldGenerator):
    """Generator for UUID types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        base_type = re.sub(r'\([^)]*\)', '', col_type.upper()).strip()
        return base_type == 'UUID'
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        return self.faker.uuid4()


class DefaultFieldGenerator(FieldGenerator):
    """Default generator for unknown types."""
    
    def can_handle(self, col_name: str, col_type: str) -> bool:
        return True  # Always handles as fallback
    
    def generate(
        self, 
        col_name: str, 
        col_type: str, 
        is_primary_key: bool = False,
        record_num: int = 0,
        **kwargs
    ) -> Any:
        return self.faker.word()


class FieldGeneratorFactory:
    """Factory for field generators using Strategy Pattern."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.faker = config.faker
        self._generators = [
            SmartFieldGenerator(self.faker),
            IntegerFieldGenerator(self.faker),
            DecimalFieldGenerator(self.faker),
            StringFieldGenerator(self.faker),
            DateTimeFieldGenerator(self.faker),
            BooleanFieldGenerator(self.faker),
            JSONFieldGenerator(self.faker),
            UUIDFieldGenerator(self.faker),
            DefaultFieldGenerator(self.faker),  # Must be last
        ]
        self._pk_generator = PrimaryKeyGenerator(self.faker)
    
    def generate_value(
        self,
        col_name: str,
        col_type: str,
        is_primary_key: bool = False,
        record_num: int = 0
    ) -> Any:
        """
        Generate a value for a column using appropriate generator strategy.
        
        Args:
            col_name: Column name
            col_type: SQL column type
            is_primary_key: Whether this is a primary key
            record_num: Record number for auto-increment
            
        Returns:
            Generated value
        """
        # Handle primary keys separately
        if is_primary_key:
            return self._pk_generator.generate(
                col_name, col_type, is_primary_key=True, record_num=record_num
            )
        
        # Try each generator in order
        for generator in self._generators:
            if generator.can_handle(col_name, col_type):
                return generator.generate(
                    col_name, col_type, is_primary_key=False, record_num=record_num
                )
        
        # Fallback (should never reach here due to DefaultFieldGenerator)
        return self.faker.word()

