from flask import Blueprint, jsonify, request
from models import ResearchDocument, DocumentCategory, EconomicDataSource, EconomicForecast, EconomicEvent, db
from utils.cache import cache
from utils.limiter import limiter
from utils.errors import APIError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

research_api = Blueprint('research_api', __name__)

@research_api.before_request
def before_request():
    """Request logging for research API"""
    logger.info({
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'research_endpoint': True
    })

def serialize_document(doc):
    """Serialize research document data"""
    return {
        "id": doc.id,
        "entity_id": doc.entity_id,
        "entity_type": doc.entity_type,
        "title": doc.title,
        "document_type": doc.document_type,
        "publication_date": doc.publication_date.strftime('%Y-%m-%d') if doc.publication_date else None,
        "file_url": doc.file_url,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "language": doc.language,
        "file_size": doc.file_size,
        "download_count": doc.download_count,
        "created_at": doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else None
    }

@research_api.route('/documents')
@limiter.limit("50/minute")
def get_research_documents():
    """Get research documents with filtering and search"""
    try:
        # Query parameters
        entity_type = request.args.get('entity_type')
        document_type = request.args.get('document_type')
        search_query = request.args.get('search')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        query = ResearchDocument.query

        # Apply filters
        if entity_type:
            query = query.filter(ResearchDocument.entity_type == entity_type)
        if document_type:
            query = query.filter(ResearchDocument.document_type == document_type)
        if date_from:
            query = query.filter(ResearchDocument.publication_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(ResearchDocument.publication_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        
        # Search functionality
        if search_query:
            search_filter = db.or_(
                ResearchDocument.title.ilike(f'%{search_query}%'),
                ResearchDocument.summary.ilike(f'%{search_query}%'),
                ResearchDocument.keywords.cast(db.String).ilike(f'%{search_query}%')
            )
            query = query.filter(search_filter)

        # Order by publication date (newest first)
        query = query.order_by(ResearchDocument.publication_date.desc())

        # Pagination
        documents = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "data": [serialize_document(doc) for doc in documents.items],
            "pagination": {
                "page": documents.page,
                "pages": documents.pages,
                "per_page": documents.per_page,
                "total": documents.total
            },
            "filters_applied": {
                "entity_type": entity_type,
                "document_type": document_type,
                "search_query": search_query,
                "date_range": f"{date_from} to {date_to}" if date_from or date_to else None
            }
        })

    except Exception as e:
        logger.error(f"Error in get_research_documents: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@research_api.route('/documents/<int:document_id>')
@limiter.limit("100/minute")
def get_document_by_id(document_id):
    """Get detailed document information"""
    document = db.session.get(ResearchDocument, document_id)
    if document is None:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(serialize_document(document))

@research_api.route('/documents/<int:document_id>/download', methods=['POST'])
@limiter.limit("100/minute")
def track_document_download(document_id):
    """Record a download of a research document and return its file URL"""
    document = db.session.get(ResearchDocument, document_id)
    if document is None:
        return jsonify({"error": "Document not found"}), 404
    try:
        document.download_count = (document.download_count or 0) + 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error tracking download for document {document_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    return jsonify({"success": True, "download_count": document.download_count,
                    "file_url": document.file_url})

@research_api.route('/documents/entity/<int:entity_id>/<entity_type>')
@limiter.limit("50/minute")

def get_documents_by_entity(entity_id, entity_type):
    """Get all documents for a specific entity (bank, government, etc.)"""
    try:
        documents = ResearchDocument.query.filter_by(
            entity_id=entity_id,
            entity_type=entity_type
        ).order_by(ResearchDocument.publication_date.desc()).all()

        return jsonify({
            "entity_id": entity_id,
            "entity_type": entity_type,
            "document_count": len(documents),
            "documents": [serialize_document(doc) for doc in documents]
        })

    except Exception as e:
        logger.error(f"Error in get_documents_by_entity: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@research_api.route('/categories')
@limiter.limit("30/minute")
def get_document_categories():
    """Get document categories for filtering"""
    try:
        categories = DocumentCategory.query.filter_by(is_active=True).order_by(
            DocumentCategory.sort_order, DocumentCategory.name
        ).all()
        
        return jsonify([{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "parent_category_id": cat.parent_category_id,
            "sort_order": cat.sort_order
        } for cat in categories])
        
    except Exception as e:
        logger.error(f"Error in get_document_categories: {str(e)}")
        return jsonify([])

@research_api.route('/data-sources')
@limiter.limit("50/minute")
def get_data_sources():
    """Get all economic data sources with reliability metrics"""
    try:
        sources = EconomicDataSource.query.order_by(
            EconomicDataSource.reliability_score.desc()
        ).all()

        return jsonify({
            "data_sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "abbreviation": source.abbreviation,
                    "website": source.website,
                    "data_types": source.data_types,
                    "update_frequency": source.update_frequency,
                    "reliability_score": source.reliability_score,
                    "last_updated": source.last_updated.strftime('%Y-%m-%d') if source.last_updated else None
                } for source in sources
            ]
        })

    except Exception as e:
        logger.error(f"Error in get_data_sources: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@research_api.route('/forecasts')
@limiter.limit("50/minute")

def get_economic_forecasts():
    """Get economic forecasts and projections"""
    try:
        indicator = request.args.get('indicator')
        source_org = request.args.get('source_organization')
        
        query = EconomicForecast.query
        
        if indicator:
            query = query.filter(EconomicForecast.indicator_name.ilike(f'%{indicator}%'))
        if source_org:
            query = query.filter(EconomicForecast.source_organization == source_org)
            
        forecasts = query.order_by(EconomicForecast.created_date.desc()).all()

        return jsonify({
            "forecasts": [
                {
                    "id": forecast.id,
                    "indicator_name": forecast.indicator_name,
                    "forecast_period": forecast.forecast_period,
                    "forecast_value": forecast.forecast_value,
                    "confidence_interval": {
                        "lower": forecast.confidence_interval_lower,
                        "upper": forecast.confidence_interval_upper
                    },
                    "forecasting_method": forecast.forecasting_method,
                    "source_organization": forecast.source_organization,
                    "created_date": forecast.created_date.strftime('%Y-%m-%d')
                } for forecast in forecasts
            ],
            "filters_applied": {
                "indicator": indicator,
                "source_organization": source_org
            }
        })

    except Exception as e:
        logger.error(f"Error in get_economic_forecasts: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@research_api.route('/economic-calendar')
@limiter.limit("50/minute")

def get_economic_calendar():
    """Get economic events and calendar"""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        importance = request.args.get('importance')
        event_type = request.args.get('event_type')
        
        query = EconomicEvent.query
        
        if date_from:
            query = query.filter(EconomicEvent.event_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(EconomicEvent.event_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        if importance:
            query = query.filter(EconomicEvent.importance == importance)
        if event_type:
            query = query.filter(EconomicEvent.event_type == event_type)
            
        events = query.order_by(EconomicEvent.event_date.desc()).all()

        return jsonify({
            "events": [
                {
                    "id": event.id,
                    "event_name": event.event_name,
                    "event_type": event.event_type,
                    "event_date": event.event_date.strftime('%Y-%m-%d'),
                    "importance": event.importance,
                    "actual_value": event.actual_value,
                    "forecast_value": event.forecast_value,
                    "previous_value": event.previous_value,
                    "description": event.description,
                    "source_organization": event.source_organization,
                    "market_impact": event.market_impact
                } for event in events
            ],
            "filters_applied": {
                "date_range": f"{date_from} to {date_to}" if date_from or date_to else None,
                "importance": importance,
                "event_type": event_type
            }
        })

    except Exception as e:
        logger.error(f"Error in get_economic_calendar: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@research_api.route('/document-types')
@limiter.limit("30/minute")

def get_document_types():
    """Get available document types and categories"""
    try:
        # Get unique document types
        document_types = db.session.query(
            ResearchDocument.document_type,
            db.func.count(ResearchDocument.id).label('count')
        ).group_by(ResearchDocument.document_type).all()
        
        # Get unique entity types
        entity_types = db.session.query(
            ResearchDocument.entity_type,
            db.func.count(ResearchDocument.id).label('count')
        ).group_by(ResearchDocument.entity_type).all()

        return jsonify({
            "document_types": [
                {"type": doc_type, "count": count} 
                for doc_type, count in document_types
            ],
            "entity_types": [
                {"type": entity_type, "count": count}
                for entity_type, count in entity_types
            ]
        })

    except Exception as e:
        logger.error(f"Error in get_document_types: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500