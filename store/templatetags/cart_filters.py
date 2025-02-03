from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # Ensure the key is a string (matching the cart dictionary keys)
    return dictionary.get(str(key), 0)

@register.filter
def mul(value, arg):
    try:
        # Convert both value and arg to float before multiplication
        return float(value) * float(arg)
    except (ValueError, TypeError):
        # Return 0 if conversion fails (e.g., empty string or invalid input)
        return 0