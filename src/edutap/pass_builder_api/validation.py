"""Client-side input validation, run before any network call."""


def validate_pass_id(value: str) -> str:
    """Validate pass_id is not empty or blank.

    Args:
        value: The pass_id value to validate.

    Returns
    -------
        The validated pass_id value.

    Raises
    ------
        ValueError: If value is empty or contains only whitespace.
    """
    if not value or not value.strip():
        raise ValueError("pass_id must be a non-empty string")
    return value


def validate_person_uid(value: str) -> str:
    """Validate person_uid is not empty or blank.

    Args:
        value: The person_uid value to validate.

    Returns
    -------
        The validated person_uid value.

    Raises
    ------
        ValueError: If value is empty or contains only whitespace.
    """
    if not value or not value.strip():
        raise ValueError("person_uid must be a non-empty string")
    return value
