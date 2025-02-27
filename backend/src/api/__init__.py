from flask import Blueprint

bp = Blueprint('api', __name__)

# Import routes to register them with the blueprint
from api.representatives import *
from api.bills import *
from api.tags import *
from api.analytics import *