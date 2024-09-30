import re


def _camel_to_snake(name):
    """
    Converts a single camelCase string to snake_case.
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def recursive_camel_to_snake(data):
    """
    Recursively converts all camelCase keys in a dictionary to snake_case.
    """
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = _camel_to_snake(key)
            new_data[new_key] = recursive_camel_to_snake(
                value
            )  # Recursively apply to values
        return new_data
    elif isinstance(data, list):
        return [
            recursive_camel_to_snake(item) for item in data
        ]  # Handle lists of dicts
    else:
        return data  # If it's neither dict nor list, return it as is


def _snake_to_camel(name):
    """
    Converts a single snake_case string to lowerCamelCase.
    """
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def recursive_snake_to_camel(data):
    """
    Recursively converts all snake_case keys in a dictionary to lowerCamelCase.
    """
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = _snake_to_camel(key)
            new_data[new_key] = recursive_snake_to_camel(
                value
            )  # Recursively apply to values
        return new_data
    elif isinstance(data, list):
        return [
            recursive_snake_to_camel(item) for item in data
        ]  # Handle lists of dicts
    else:
        return data  # If it's neither dict nor list, return it as is
