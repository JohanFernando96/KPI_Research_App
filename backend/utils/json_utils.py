import json
from bson import ObjectId
from datetime import datetime


class MongoJSONEncoder(json.JSONEncoder):
    """JSON encoder that can handle MongoDB ObjectId and datetime objects."""

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(MongoJSONEncoder, self).default(obj)


def serialize_mongo(data):
    """
    Serialize MongoDB data to JSON-compatible format.

    Args:
        data: MongoDB data to serialize.

    Returns:
        JSON-compatible data.
    """
    return json.loads(json.dumps(data, cls=MongoJSONEncoder))


def safe_parse_json(json_string, default=None):
    """
    Safely parse JSON string with fallback.

    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def extract_json_from_text(text):
    """
    Extract JSON object from text that may contain other content.

    Args:
        text: Text containing JSON

    Returns:
        Extracted JSON object or None
    """
    import re

    # Try to find JSON object in text
    json_patterns = [
        r'({[\s\S]*})',  # Object
        r'(\[[\s\S]*\])'  # Array
    ]

    for pattern in json_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    return None


def merge_json_objects(base, updates, deep=True):
    """
    Merge two JSON objects.

    Args:
        base: Base object
        updates: Updates to apply
        deep: Whether to do deep merge

    Returns:
        Merged object
    """
    if not deep:
        result = base.copy()
        result.update(updates)
        return result

    # Deep merge
    result = json.loads(json.dumps(base))  # Deep copy

    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                deep_update(d[k], v)
            else:
                d[k] = v

    deep_update(result, updates)
    return result


def filter_json_fields(data, allowed_fields=None, excluded_fields=None):
    """
    Filter JSON object to include/exclude specific fields.

    Args:
        data: JSON object
        allowed_fields: Set of fields to include (if specified, only these are included)
        excluded_fields: Set of fields to exclude

    Returns:
        Filtered JSON object
    """
    if allowed_fields:
        return {k: v for k, v in data.items() if k in allowed_fields}
    elif excluded_fields:
        return {k: v for k, v in data.items() if k not in excluded_fields}
    else:
        return data.copy()