import re


def resolve_variables(config, value):
    if isinstance(value, str):
        # Find all ${base_dirs.xxx} patterns
        pattern = r'\${([^}]+)}'
        matches = re.findall(pattern, value)
        
        resolved_value = value
        for match in matches:
            # Split by dot to navigate nested config
            parts = match.split('.')
            # Get the referenced value
            ref_value = config
            for part in parts:
                ref_value = ref_value[part]
            # Replace the variable reference with its value
            resolved_value = resolved_value.replace(f"${{{match}}}", ref_value)
        
        return resolved_value
    return value