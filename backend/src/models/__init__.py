# backend/src/models/__init__.py

# Re-export key model functions for cleaner imports
from .representative import get_representatives, get_representative_detail, get_representative_bio
from .bill import get_bills, get_bill_detail, get_all_congresses
from .tag import get_all_tags
from .analytics import (
    get_bills_by_status,
    get_passage_time_analytics,
    get_bills_per_congress
)

# This allows other modules to import directly from the models package:
# from models import get_representatives
# Instead of:
# from models.representative import get_representatives