"""
Custom exceptions for the Mendax project.
"""


class MendaxException(Exception):
    """Base exception for all Mendax-related errors."""
    pass


class SchemaParsingError(MendaxException):
    """Raised when SQL schema parsing fails."""
    pass


class CircularDependencyError(MendaxException):
    """Raised when circular dependencies are detected in schema."""
    
    def __init__(self, tables: list[str], message: str = None):
        self.tables = tables
        if message is None:
            message = f"Circular dependency detected involving tables: {', '.join(sorted(tables))}"
        super().__init__(message)


class InvalidSchemaError(MendaxException):
    """Raised when schema is invalid or empty."""
    pass


class DataGenerationError(MendaxException):
    """Raised when data generation fails."""
    pass

