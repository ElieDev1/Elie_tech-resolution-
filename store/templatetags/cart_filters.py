from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # Try to fetch the key as an integer if possible, then fall back to string
    try:
        key = int(key)  # Attempt to convert to integer
    except (ValueError, TypeError):
        pass  # Keep the original key if conversion fails
    return dictionary.get(key, 0)
