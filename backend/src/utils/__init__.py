# backend/src/utils/__init__.py

# Database utilities
from .database import get_db_connection, get_db_cursor, transaction

# Exception classes
from .exceptions import (
    AppError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError
)

# Helper functions
from .helpers import (
    parse_json_field,
    validate_pagination_params,
    get_pagination_params,
    validate_sort_params,
    get_sort_params,
    build_pagination_result,
    serialize_dates,
    build_filter_clause,
    get_logger
)

# This enables cleaner imports like:
# from utils import get_db_cursor, ResourceNotFoundError, serialize_dates