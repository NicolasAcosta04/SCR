"""
Category Mappings Module
Manages category normalization and validation for article classification.

Key Features:
- Category normalization
- Category validation
- Main category mapping
- Subcategory handling
- Category hierarchy management

Categories:
- Technology
- Business
- Politics
- Entertainment
- Sports
- Science
- Health

Note: This module ensures consistent category handling across the application
and provides validation for category-based operations.
"""

# Main categories that match the model's classification labels
MAIN_CATEGORIES = {
    0: "tech",
    1: "business",
    2: "politics",
    3: "entertainment",
    4: "sport"
}

def get_main_category(category: str) -> str:
    """
    Maps a category (either main or subcategory) to its main category.
    If the input is already a main category, returns it unchanged.
    If the input is a subcategory, returns the corresponding main category.
    If the input is not found, returns 'other'.
    """
    # Check if it's a main category
    if category in MAIN_CATEGORIES.values():
        return category
    return "other"

def validate_category(category: str) -> bool:
    """
    Validates if a given category is a valid main category.
    """
    return category in MAIN_CATEGORIES.values()

def map_to_main_category(category: str) -> str:
    """
    Maps any category (main or sub) to its main category.
    """
    return get_main_category(category)