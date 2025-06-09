from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()

# Import models after db initialization to avoid circular imports
from api.models.models import Company, CompanyAudit

# Optional: Define what should be imported when using 'from api.models import *'
__all__ = ['db', 'bcrypt', 'Company', 'CompanyAudit']