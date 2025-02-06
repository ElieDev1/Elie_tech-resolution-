from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retrieve an item from a dictionary using a key."""
    if isinstance(dictionary, dict):  # Ensure it's a dictionary
        return dictionary.get(key, 0)  # Default to 0 if key not found
    return 0  # Return 0 if dictionary is invalid
