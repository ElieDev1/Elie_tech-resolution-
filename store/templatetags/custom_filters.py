from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return the value for the given key from the dictionary."""
    return dictionary.get(key)
