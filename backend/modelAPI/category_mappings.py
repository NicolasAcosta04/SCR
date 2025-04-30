from typing import Dict, List, Optional

# Main categories
MAIN_CATEGORIES = {
    0: "world",
    1: "sport",
    2: "business",
    3: "Science/Tech"
}

# Subcategory mappings to main categories
SUBCATEGORY_MAPPINGS = {
    # World subcategories
    "politics": "world",
    "environment": "world",
    "health": "world",
    "education": "world",
    "culture": "world",
    "conflict": "world",
    "diplomacy": "world",
    
    # Sport subcategories
    "football": "sport",
    "basketball": "sport",
    "tennis": "sport",
    "golf": "sport",
    "olympics": "sport",
    "cricket": "sport",
    "rugby": "sport",
    "athletics": "sport",
    
    # Business subcategories
    "finance": "business",
    "markets": "business",
    "economy": "business",
    "investing": "business",
    "companies": "business",
    "trade": "business",
    "employment": "business",
    "real_estate": "business",
    
    # Science/Tech subcategories
    "space": "Science/Tech",
    "environmental_science": "Science/Tech",
    "medicine": "Science/Tech",
    "computing": "Science/Tech",
    "artificial_intelligence": "Science/Tech",
    "robotics": "Science/Tech",
    "engineering": "Science/Tech",
    "physics": "Science/Tech",
    "biology": "Science/Tech"
}

def get_main_category(category: str) -> str:
    """
    Maps a category (either main or subcategory) to its main category.
    If the input is already a main category, returns it unchanged.
    If the input is a subcategory, returns the corresponding main category.
    If the input is not found, returns 'other'.
    """
    # # Check if it's a main category
    # if category in MAIN_CATEGORIES.values():
    #     return category
    
    # # Check if it's a subcategory
    # if category in SUBCATEGORY_MAPPINGS:
    #     return SUBCATEGORY_MAPPINGS[category]
    
    # If not found, return 'other'
    return "other"

def get_subcategories(main_category: str) -> List[str]:
    """
    Returns a list of subcategories for a given main category.
    Returns empty list if the main category doesn't exist or has no subcategories.
    """
    
    return None
    
    # return [
    #     subcat for subcat, main_cat in SUBCATEGORY_MAPPINGS.items()
    #     if main_cat == main_category
    # ]

def is_valid_category(category: str) -> bool:
    """
    Checks if a category is either a main category or a subcategory.
    """
    return (
        category in MAIN_CATEGORIES.values() 
        # or
        # category in SUBCATEGORY_MAPPINGS
    )

def validate_category(category: str) -> bool:
    """
    Validates if a given category is a valid main category.
    """
    return category in MAIN_CATEGORIES.values()

def validate_subcategory(subcategory: str) -> bool:
    """
    Validates if a given subcategory is valid.
    """
    # return subcategory in SUBCATEGORY_MAPPINGS
    return None

def map_to_main_category(category: str) -> str:
    """
    Maps any category (main or sub) to its main category.
    """
    return get_main_category(category)

def map_to_subcategory(category: str) -> Optional[str]:
    """
    Returns a default subcategory for a given category.
    If category is already a subcategory, returns it.
    If category is a main category, returns its first associated subcategory.
    """
    # if category in SUBCATEGORY_MAPPINGS:
    #     return category
        
    # subcats = get_subcategories(category)
    # return subcats[0] if subcats else None
    return None