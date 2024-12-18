# hubspot_integration/hubspot_utils.py

def validate_object_type(object_type):
    """Validate if the object type is supported."""
    valid_object_types = ['contacts', 'companies', 'deals']
    return object_type in valid_object_types
