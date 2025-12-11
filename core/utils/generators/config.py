"""
Configuration for data generators.
"""

from dataclasses import dataclass
from typing import Optional
from faker import Faker


@dataclass
class GeneratorConfig:
    """
    Configuration for data generation.
    
    Attributes:
        locale: Faker locale (e.g., 'en_US', 'fa_IR')
        seed: Random seed for reproducible data generation
        nullable_fk_probability: Probability (0.0-1.0) of setting nullable foreign keys to None
        faker: Faker instance (auto-created if not provided)
    """
    locale: str = 'en_US'
    seed: Optional[int] = None
    nullable_fk_probability: float = 0.3
    faker: Optional[Faker] = None
    
    def __post_init__(self):
        """Initialize Faker instance if not provided."""
        if self.faker is None:
            self.faker = Faker(self.locale)
            if self.seed is not None:
                Faker.seed(self.seed)
        
        # Validate nullable_fk_probability
        if not 0.0 <= self.nullable_fk_probability <= 1.0:
            raise ValueError("nullable_fk_probability must be between 0.0 and 1.0")

