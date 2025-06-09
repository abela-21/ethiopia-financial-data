from flask import Blueprint, jsonify, request
from api.models.models import Company, CompanyAudit
from api.models import db
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from api.utils.errors import APIError
from api.utils.validators import validate_company_data
from api.utils.cache import cache
from api.utils.limiter import limiter
from datetime import datetime
from sqlalchemy import desc, asc, or_
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

company_api = Blueprint('company_api', __name__)

@company_api.before_request
def before_request():
    """Enhanced request logging"""
    if not request.path.endswith('/health'):
        user_id = None
        try:
            # THIS IS THE CRITICAL LINE: Attempt to verify JWT optionally
            # This makes get_jwt_identity() safe to call afterward
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception as e:
            # Log specific JWT errors if needed, e.g., for debugging invalid tokens
            # but for public routes, if optional=True, this block might not even be hit
            # unless there's a malformed token.
            logger.debug(f"JWT verification failed or no JWT: {e}")
            user_id = None # Ensure user_id is None if verification failed

        logger.info({
            'path': request.path,
            'method': request.method,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'params': dict(request.args),
            # Now, get_jwt_identity() is safe to call here,
            # as verify_jwt_in_request(optional=True) has prepared the context.
            # It will return None if no JWT or invalid JWT was present.
            'user_id': user_id
        })


def serialize_company(company):
    """Helper function to serialize company data"""
    return {
        'id': company.id,
        'name': company.name,
        'ticker': company.ticker,
        'industry': company.industry,
        'sector': company.sector,
        'description': company.description,
        'website': company.website,
        'established_date': company.established_date.isoformat() if company.established_date else None,
        'created_at': company.created_at.isoformat() if company.created_at else None,
        'updated_at': company.updated_at.isoformat() if company.updated_at else None,
        'created_by': company.created_by,
        'updated_by': company.updated_by
    }

def add_audit_log(company_id, action, user_id, details=None):
    """Add audit log entry"""
    audit = CompanyAudit(
        company_id=company_id,
        action=action,
        user_id=user_id,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.session.add(audit)

# -- Routes --

@company_api.route('/companies', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
@limiter.limit("30/minute")
def get_companies():
    """Get companies with filtering, sorting, pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        industry = request.args.get('industry')
        sector = request.args.get('sector')
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        search = request.args.get('search')

        query = Company.query

        if industry:
            query = query.filter(Company.industry == industry)
        if sector:
            query = query.filter(Company.sector == sector)

        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                Company.name.ilike(search_term),
                Company.ticker.ilike(search_term),
                Company.industry.ilike(search_term),
                Company.description.ilike(search_term)
            ))

        sort_column = getattr(Company, sort_by, Company.name)
        query = query.order_by(desc(sort_column) if order == 'desc' else asc(sort_column))

        paginated = query.paginate(page=page, per_page=per_page)

        response = {
            'companies': [serialize_company(c) for c in paginated.items],
            'pagination': {
                'total_items': paginated.total,
                'total_pages': paginated.pages,
                'current_page': page,
                'per_page': per_page
            },
            'filters': {
                'industry': industry,
                'sector': sector,
                'search': search
            }
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in get_companies: {str(e)}")
        raise APIError(str(e))

@company_api.route('/companies/<int:id>', methods=['GET'])
@cache.memoize(300)
def get_company_by_id(id):
    """Get single company by ID"""
    try:
        company = Company.query.get_or_404(id)
        return jsonify(serialize_company(company)), 200
    except Exception as e:
        logger.error(f"Error in get_company_by_id: {str(e)}")
        raise APIError(str(e))

@company_api.route('/companies', methods=['POST'])
@jwt_required()
@limiter.limit("5/minute")
def create_company():
    """Create new company"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        errors = validate_company_data(data)
        if errors:
            raise APIError("; ".join(errors))

        if Company.query.filter_by(ticker=data['ticker']).first():
            raise APIError("Company with this ticker already exists", status_code=409)

        established_date = None
        if 'established_date' in data:
            try:
                established_date = datetime.strptime(data['established_date'], '%Y-%m-%d').date()
            except ValueError:
                raise APIError("Invalid established_date format. Use YYYY-MM-DD")

        new_company = Company(
            name=data['name'],
            ticker=data['ticker'],
            industry=data['industry'],
            sector=data.get('sector'),
            description=data.get('description'),
            website=data.get('website'),
            established_date=established_date,
            created_by=user_id,
            created_at=datetime.utcnow()
        )

        db.session.add(new_company)
        db.session.flush()

        add_audit_log(new_company.id, 'CREATE', user_id, data)

        db.session.commit()
        cache.delete_memoized(get_companies)

        return jsonify(serialize_company(new_company)), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in create_company: {str(e)}")
        raise APIError(str(e))

# The other route handlers remain unchanged except for improved logging consistency and cleanups.

@company_api.route('/companies/batch', methods=['POST'])
@jwt_required()
@limiter.limit("2/minute")
def batch_create_companies():
    """Batch create companies"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        if not isinstance(data, list):
            raise APIError("Expected array of companies")

        companies = []
        for item in data:
            errors = validate_company_data(item)
            if errors:
                raise APIError(f"Invalid company data: {'; '.join(errors)}")

            company = Company(
                **item,
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            companies.append(company)

        db.session.bulk_save_objects(companies)
        db.session.flush()  # get company ids

        # Add audit logs for each company
        for company, item in zip(companies, data):
            add_audit_log(company.id, 'BATCH_CREATE', user_id, item)

        db.session.commit()
        cache.delete_memoized(get_companies)

        return jsonify({
            "message": f"Created {len(companies)} companies",
            "company_ids": [c.id for c in companies]
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in batch_create_companies: {str(e)}")
        raise APIError(str(e))

# Health check remains unchanged.
