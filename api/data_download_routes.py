"""
File downloads for the Downloads page (/api/download/...).

Each endpoint returns a CSV, Excel or JSON file and records the download in
the user's download history.
"""
import io
import json
import logging
from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from flask_login import current_user, login_required

from models import Company, DownloadHistory, Financial, MacroIndicators, Stock, db
from utils.limiter import limiter

logger = logging.getLogger(__name__)

data_download_bp = Blueprint('data_download', __name__, url_prefix='/download')

FORMATS = {
    'csv': ('text/csv', 'csv'),
    'excel': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'),
    'json': ('application/json', 'json'),
}

COMPANY_COLUMNS = ['id', 'name', 'ticker', 'sector', 'industry', 'website', 'established_date',
                   'shares_outstanding', 'description']
STOCK_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']
FINANCIAL_COLUMNS = [c.name for c in Financial.__table__.columns
                     if c.name not in ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')]
MACRO_VARIABLES = [c.name for c in MacroIndicators.__table__.columns
                   if c.name not in ('id', 'date', 'created_at', 'updated_at', 'created_by', 'updated_by')]


class DownloadError(ValueError):
    pass


def _format():
    fmt = request.args.get('format', 'csv').lower()
    if fmt not in FORMATS:
        raise DownloadError(f"format must be one of: {', '.join(FORMATS)}")
    return fmt


def _date_arg(name):
    value = request.args.get(name, '').strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise DownloadError(f'{name} must be a date in YYYY-MM-DD format')


def _int_arg(name):
    value = request.args.get(name, '').strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise DownloadError(f'{name} must be a whole number')


def _rows(records, columns):
    return [{col: getattr(record, col) for col in columns} for record in records]


def _send(rows, columns, basename, fmt, download_type, resource=None):
    if not rows:
        return jsonify({'error': 'No data matches the selected filters'}), 404

    df = pd.DataFrame(rows, columns=columns)
    buffer = io.BytesIO()
    if fmt == 'csv':
        buffer.write(df.to_csv(index=False).encode('utf-8'))
    elif fmt == 'excel':
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=basename[:31])
    else:
        buffer.write(df.to_json(orient='records', date_format='iso', indent=2).encode('utf-8'))
    size = buffer.tell()
    buffer.seek(0)

    mimetype, ext = FORMATS[fmt]
    filename = f"{basename}_{datetime.now():%Y%m%d}.{ext}"
    try:
        db.session.add(DownloadHistory(
            user_id=current_user.id,
            download_type=download_type,
            resource_id=str(resource.id) if resource is not None else None,
            resource_name=getattr(resource, 'name', None) or basename,
            file_format=ext,
            file_size=size,
            parameters=json.dumps(request.args.to_dict(flat=False)),
            status='completed',
        ))
        db.session.commit()
    except Exception as e:  # history is best-effort; never block the download
        db.session.rollback()
        logger.warning(f"Could not record download history: {e}")

    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)


def _handle(fn):
    """Turn validation errors into 400 JSON responses."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DownloadError as e:
            return jsonify({'error': str(e)}), 400
    wrapper.__name__ = fn.__name__
    return wrapper


@data_download_bp.route('/companies')
@login_required
@limiter.limit("30/minute")
@_handle
def download_companies():
    fmt = _format()
    query = Company.query.order_by(Company.name)
    if request.args.get('industry'):
        query = query.filter(Company.industry == request.args['industry'])
    return _send(_rows(query.all(), COMPANY_COLUMNS), COMPANY_COLUMNS, 'companies', fmt, 'companies')


@data_download_bp.route('/macro_indicators')
@login_required
@limiter.limit("30/minute")
@_handle
def download_macro_indicators():
    fmt = _format()
    variables = [v for v in request.args.getlist('variables') if v] or MACRO_VARIABLES
    unknown = sorted(set(variables) - set(MACRO_VARIABLES))
    if unknown:
        raise DownloadError(f"Unknown variables: {', '.join(unknown)}")
    date_from, date_to = _date_arg('date_from'), _date_arg('date_to')
    if date_from and date_to and date_from > date_to:
        raise DownloadError('date_from must be on or before date_to')

    query = MacroIndicators.query.order_by(MacroIndicators.date)
    if date_from:
        query = query.filter(MacroIndicators.date >= date_from)
    if date_to:
        query = query.filter(MacroIndicators.date <= date_to)
    columns = ['date'] + variables
    return _send(_rows(query.all(), columns), columns, 'macro_indicators', fmt, 'macro_indicators')


@data_download_bp.route('/stocks/<int:company_id>')
@login_required
@limiter.limit("30/minute")
@_handle
def download_stocks(company_id):
    fmt = _format()
    company = db.session.get(Company, company_id)
    if company is None:
        return jsonify({'error': 'Company not found'}), 404
    start, end = _date_arg('start_date'), _date_arg('end_date')
    query = Stock.query.filter_by(company_id=company_id).order_by(Stock.date)
    if start:
        query = query.filter(Stock.date >= start)
    if end:
        query = query.filter(Stock.date <= end)
    return _send(_rows(query.all(), STOCK_COLUMNS), STOCK_COLUMNS, f"{company.ticker}_stock_prices", fmt,
                 'stocks', company)


@data_download_bp.route('/financials')
@data_download_bp.route('/financials/<int:company_id>')
@login_required
@limiter.limit("30/minute")
@_handle
def download_financials(company_id=None):
    fmt = _format()
    company_id = company_id or _int_arg('company_id')
    company = None
    query = Financial.query
    if company_id:
        company = db.session.get(Company, company_id)
        if company is None:
            return jsonify({'error': 'Company not found'}), 404
        query = query.filter(Financial.company_id == company_id)
    year_from, year_to = _int_arg('year_from'), _int_arg('year_to')
    if year_from:
        query = query.filter(Financial.year >= year_from)
    if year_to:
        query = query.filter(Financial.year <= year_to)
    if request.args.get('period'):
        query = query.filter(Financial.period == request.args['period'])

    variables = [v for v in request.args.getlist('variables') if v and v != 'all']
    unknown = sorted(set(variables) - set(FINANCIAL_COLUMNS))
    if unknown:
        raise DownloadError(f"Unknown variables: {', '.join(unknown)}")
    columns = ['company_id', 'year', 'period'] + [v for v in variables if v not in ('company_id', 'year', 'period')] \
        if variables else FINANCIAL_COLUMNS

    records = query.order_by(Financial.company_id, Financial.year, Financial.period).all()
    names = {c.id: c.name for c in Company.query.filter(Company.id.in_({r.company_id for r in records}))}
    rows = [{'company': names.get(r.company_id), **{col: getattr(r, col) for col in columns}} for r in records]
    basename = f"{company.ticker}_financials" if company else 'financials'
    return _send(rows, ['company'] + columns, basename, fmt, 'financials', company)
