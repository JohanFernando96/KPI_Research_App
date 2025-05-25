import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.

    Args:
        filename: The filename to check.
        allowed_extensions: Set of allowed extensions. If None, uses app config.

    Returns:
        bool: True if the file is allowed, False otherwise.
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_file(file, directory=None):
    """
    Save a file with a secure filename to the specified directory.

    Args:
        file: The file object to save.
        directory: Directory to save the file. If None, uses app config upload folder.

    Returns:
        str: Path to the saved file.
    """
    if directory is None:
        directory = current_app.config['UPLOAD_FOLDER']

    # Generate a secure filename with a UUID to prevent collisions
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(directory, unique_filename)

    # Save the file
    file.save(filepath)

    return filepath


def get_file_extension(filename):
    """
    Get the extension of a file.

    Args:
        filename: The filename to check.

    Returns:
        str: The file extension.
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ""


def validate_file_size(file, max_size_mb=10):
    """
    Validate file size is within limits.

    Args:
        file: File object
        max_size_mb: Maximum size in megabytes

    Returns:
        tuple: (is_valid, error_message)
    """
    # Get file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        return False, f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)"

    return True, None


def validate_file_type(filename, allowed_extensions=None):
    """
    Validate file type against allowed extensions.

    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions

    Returns:
        tuple: (is_valid, error_message)
    """
    if not allowed_extensions:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'jpg', 'jpeg', 'png'})

    if not allowed_file(filename, allowed_extensions):
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"

    return True, None