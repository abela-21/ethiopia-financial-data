from flask import Blueprint, jsonify, request, send_file, make_response
from models import db, Company, Stock, Financial, Bank, BankFinancialMetric, EconomicSector, ResearchDocument
from datetime import datetime, timedelta
import pandas as pd
import io
import json
import csv
import xlsxwriter
import logging

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)

@export_bp.route('/formats')
def get_export_formats():
    """Get available export formats and their capabilities"""
    formats = {
        'excel': {
            'name': 'Microsoft Excel',
            'extension': '.xlsx',
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'supports_multiple_sheets': True,
            'supports_formatting': True,
            'supports_charts': True,
            'max_rows': 1048576
        },
        'csv': {
            'name': 'Comma Separated Values',
            'extension': '.csv',
            'mime_type': 'text/csv',
            'supports_multiple_sheets': False,
            'supports_formatting': False,
            'supports_charts': False,
            'max_rows': None
        },
        'json': {
            'name': 'JavaScript Object Notation',
            'extension': '.json',
            'mime_type': 'application/json',
            'supports_multiple_sheets': False,
            'supports_formatting': False,
            'supports_charts': False,
            'max_rows': None
        },
        'pdf': {
            'name': 'Portable Document Format',
            'extension': '.pdf',
            'mime_type': 'application/pdf',
            'supports_multiple_sheets': False,
            'supports_formatting': True,
            'supports_charts': True,
            'max_rows': None
        }
    }
    
    return jsonify(formats)

@export_bp.route('/companies', methods=['POST'])
def export_companies():
    """Export company data with advanced filtering and formatting"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'excel')
        filters = data.get('filters', {})
        columns = data.get('columns', [])
        
        # Build query with filters
        query = Company.query
        
        if filters.get('industry'):
            query = query.filter(Company.industry.in_(filters['industry']))
        
        if filters.get('market_cap_min'):
            query = query.filter(Company.market_cap >= filters['market_cap_min'])
        
        if filters.get('market_cap_max'):
            query = query.filter(Company.market_cap <= filters['market_cap_max'])
        
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                Company.name.ilike(search_term) | Company.ticker.ilike(search_term)
            )
        
        companies = query.all()
        
        if export_format == 'excel':
            return _export_companies_excel(companies, columns, filters)
        elif export_format == 'csv':
            return _export_companies_csv(companies, columns)
        elif export_format == 'json':
            return _export_companies_json(companies, columns)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting companies: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

@export_bp.route('/financial-data', methods=['POST'])
def export_financial_data():
    """Export financial data with comprehensive analysis"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'excel')
        company_ids = data.get('company_ids', [])
        date_range = data.get('date_range', {})
        metrics = data.get('metrics', [])
        
        # Build financial data query
        query = Financial.query
        
        if company_ids:
            query = query.filter(Financial.company_id.in_(company_ids))
        
        if date_range.get('start'):
            start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
            query = query.filter(Financial.year >= start_date.year)
        
        if date_range.get('end'):
            end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')
            query = query.filter(Financial.year <= end_date.year)
        
        financial_data = query.all()
        
        if export_format == 'excel':
            return _export_financial_excel(financial_data, metrics, company_ids)
        elif export_format == 'csv':
            return _export_financial_csv(financial_data, metrics)
        elif export_format == 'json':
            return _export_financial_json(financial_data, metrics)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting financial data: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

@export_bp.route('/banking-sector', methods=['POST'])
def export_banking_data():
    """Export comprehensive banking sector analysis"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'excel')
        bank_ids = data.get('bank_ids', [])
        metrics = data.get('metrics', [])
        include_analysis = data.get('include_analysis', True)
        
        # Get banking data
        banks_query = Bank.query
        if bank_ids:
            banks_query = banks_query.filter(Bank.id.in_(bank_ids))
        banks = banks_query.all()
        
        # Get bank financial metrics
        metrics_query = BankFinancialMetric.query
        if bank_ids:
            metrics_query = metrics_query.filter(BankFinancialMetric.bank_id.in_(bank_ids))
        bank_metrics = metrics_query.all()
        
        if export_format == 'excel':
            return _export_banking_excel(banks, bank_metrics, include_analysis)
        elif export_format == 'csv':
            return _export_banking_csv(banks, bank_metrics)
        elif export_format == 'json':
            return _export_banking_json(banks, bank_metrics)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting banking data: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500

def _export_companies_excel(companies, columns, filters):
    """Export companies to Excel with advanced formatting"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Create main data sheet
    worksheet = workbook.add_worksheet('Companies')
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    percent_format = workbook.add_format({'num_format': '0.00%'})
    
    # Define columns
    if not columns:
        columns = ['name', 'ticker', 'industry', 'market_cap', 'employees', 'founded_year']
    
    headers = []
    for col in columns:
        if col == 'name':
            headers.append('Company Name')
        elif col == 'ticker':
            headers.append('Ticker Symbol')
        elif col == 'industry':
            headers.append('Industry')
        elif col == 'market_cap':
            headers.append('Market Cap (ETB)')
        elif col == 'employees':
            headers.append('Employees')
        elif col == 'founded_year':
            headers.append('Founded Year')
        else:
            headers.append(col.replace('_', ' ').title())
    
    # Write headers
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Write data
    for row, company in enumerate(companies, 1):
        for col, column in enumerate(columns):
            value = getattr(company, column, '')
            if column == 'market_cap' and value:
                worksheet.write(row, col, float(value), money_format)
            else:
                worksheet.write(row, col, value or '')
    
    # Add summary sheet
    summary_sheet = workbook.add_worksheet('Summary')
    summary_sheet.write(0, 0, 'Export Summary', header_format)
    summary_sheet.write(1, 0, 'Total Companies:')
    summary_sheet.write(1, 1, len(companies))
    summary_sheet.write(2, 0, 'Export Date:')
    summary_sheet.write(2, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    if filters:
        summary_sheet.write(3, 0, 'Filters Applied:')
        row = 4
        for key, value in filters.items():
            if value:
                summary_sheet.write(row, 0, f'{key.replace("_", " ").title()}:')
                summary_sheet.write(row, 1, str(value))
                row += 1
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'companies_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def _export_companies_csv(companies, columns):
    """Export companies to CSV format"""
    output = io.StringIO()
    
    if not columns:
        columns = ['name', 'ticker', 'industry', 'market_cap', 'employees', 'founded_year']
    
    writer = csv.writer(output)
    
    # Write header
    headers = [col.replace('_', ' ').title() for col in columns]
    writer.writerow(headers)
    
    # Write data
    for company in companies:
        row = []
        for column in columns:
            value = getattr(company, column, '')
            row.append(value or '')
        writer.writerow(row)
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=companies_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def _export_companies_json(companies, columns):
    """Export companies to JSON format"""
    if not columns:
        columns = ['name', 'ticker', 'industry', 'market_cap', 'employees', 'founded_year']
    
    data = []
    for company in companies:
        company_data = {}
        for column in columns:
            value = getattr(company, column, '')
            company_data[column] = value
        data.append(company_data)
    
    export_data = {
        'export_info': {
            'export_date': datetime.now().isoformat(),
            'total_records': len(data),
            'columns': columns
        },
        'data': data
    }
    
    response = make_response(json.dumps(export_data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=companies_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    return response

def _export_financial_excel(financial_data, metrics, company_ids):
    """Export financial data to Excel with analysis"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Create sheets
    data_sheet = workbook.add_worksheet('Financial Data')
    summary_sheet = workbook.add_worksheet('Summary')
    
    # Formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    
    # Write financial data
    headers = ['Company ID', 'Year', 'Period', 'Revenue', 'Net Income', 'Total Assets', 'Total Liabilities', 'Equity']
    for col, header in enumerate(headers):
        data_sheet.write(0, col, header, header_format)
    
    for row, financial in enumerate(financial_data, 1):
        data_sheet.write(row, 0, financial.company_id)
        data_sheet.write(row, 1, financial.year)
        data_sheet.write(row, 2, financial.period or '')
        data_sheet.write(row, 3, float(financial.revenue) if financial.revenue else 0, money_format)
        data_sheet.write(row, 4, float(financial.net_income) if financial.net_income else 0, money_format)
        data_sheet.write(row, 5, float(financial.total_assets) if financial.total_assets else 0, money_format)
        data_sheet.write(row, 6, float(financial.total_liabilities) if financial.total_liabilities else 0, money_format)
        data_sheet.write(row, 7, float(financial.equity) if financial.equity else 0, money_format)
    
    # Add summary
    summary_sheet.write(0, 0, 'Financial Data Export Summary', header_format)
    summary_sheet.write(1, 0, 'Total Records:')
    summary_sheet.write(1, 1, len(financial_data))
    summary_sheet.write(2, 0, 'Export Date:')
    summary_sheet.write(2, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'financial_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def _export_financial_csv(financial_data, metrics):
    """Export financial data to CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ['Company ID', 'Year', 'Period', 'Revenue', 'Net Income', 'Total Assets', 'Total Liabilities', 'Equity']
    writer.writerow(headers)
    
    for financial in financial_data:
        row = [
            financial.company_id,
            financial.year,
            financial.period or '',
            financial.revenue or 0,
            financial.net_income or 0,
            financial.total_assets or 0,
            financial.total_liabilities or 0,
            financial.equity or 0
        ]
        writer.writerow(row)
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=financial_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def _export_financial_json(financial_data, metrics):
    """Export financial data to JSON"""
    data = []
    for financial in financial_data:
        data.append({
            'company_id': financial.company_id,
            'year': financial.year,
            'period': financial.period,
            'revenue': float(financial.revenue) if financial.revenue else 0,
            'net_income': float(financial.net_income) if financial.net_income else 0,
            'total_assets': float(financial.total_assets) if financial.total_assets else 0,
            'total_liabilities': float(financial.total_liabilities) if financial.total_liabilities else 0,
            'equity': float(financial.equity) if financial.equity else 0
        })
    
    export_data = {
        'export_info': {
            'export_date': datetime.now().isoformat(),
            'total_records': len(data)
        },
        'data': data
    }
    
    response = make_response(json.dumps(export_data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=financial_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    return response

def _export_banking_excel(banks, bank_metrics, include_analysis):
    """Export banking data to Excel with comprehensive analysis"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Create sheets
    banks_sheet = workbook.add_worksheet('Banks')
    metrics_sheet = workbook.add_worksheet('Financial Metrics')
    if include_analysis:
        analysis_sheet = workbook.add_worksheet('Analysis')
    
    # Formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    percent_format = workbook.add_format({'num_format': '0.00%'})
    
    # Write banks data
    bank_headers = ['ID', 'Name', 'Type', 'Total Assets', 'Founded Year', 'Headquarters', 'Website']
    for col, header in enumerate(bank_headers):
        banks_sheet.write(0, col, header, header_format)
    
    for row, bank in enumerate(banks, 1):
        banks_sheet.write(row, 0, bank.id)
        banks_sheet.write(row, 1, bank.name)
        banks_sheet.write(row, 2, bank.bank_type or '')
        banks_sheet.write(row, 3, float(bank.total_assets) if bank.total_assets else 0, money_format)
        banks_sheet.write(row, 4, bank.founded_year or '')
        banks_sheet.write(row, 5, bank.headquarters or '')
        banks_sheet.write(row, 6, bank.website or '')
    
    # Write metrics data
    metric_headers = ['Bank ID', 'Metric Name', 'Value', 'Period', 'Year']
    for col, header in enumerate(metric_headers):
        metrics_sheet.write(0, col, header, header_format)
    
    for row, metric in enumerate(bank_metrics, 1):
        metrics_sheet.write(row, 0, metric.bank_id)
        metrics_sheet.write(row, 1, metric.metric_name)
        metrics_sheet.write(row, 2, float(metric.metric_value) if metric.metric_value else 0)
        metrics_sheet.write(row, 3, metric.period or '')
        metrics_sheet.write(row, 4, metric.year or '')
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'banking_sector_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def _export_banking_csv(banks, bank_metrics):
    """Export banking data to CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write banks section
    writer.writerow(['=== BANKS ==='])
    writer.writerow(['ID', 'Name', 'Type', 'Total Assets', 'Founded Year', 'Headquarters', 'Website'])
    
    for bank in banks:
        writer.writerow([
            bank.id,
            bank.name,
            bank.bank_type or '',
            bank.total_assets or 0,
            bank.founded_year or '',
            bank.headquarters or '',
            bank.website or ''
        ])
    
    # Write metrics section
    writer.writerow([])
    writer.writerow(['=== FINANCIAL METRICS ==='])
    writer.writerow(['Bank ID', 'Metric Name', 'Value', 'Period', 'Year'])
    
    for metric in bank_metrics:
        writer.writerow([
            metric.bank_id,
            metric.metric_name,
            metric.metric_value or 0,
            metric.period or '',
            metric.year or ''
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=banking_sector_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def _export_banking_json(banks, bank_metrics):
    """Export banking data to JSON"""
    banks_data = []
    for bank in banks:
        banks_data.append({
            'id': bank.id,
            'name': bank.name,
            'type': bank.bank_type,
            'total_assets': float(bank.total_assets) if bank.total_assets else 0,
            'founded_year': bank.founded_year,
            'headquarters': bank.headquarters,
            'website': bank.website
        })
    
    metrics_data = []
    for metric in bank_metrics:
        metrics_data.append({
            'bank_id': metric.bank_id,
            'metric_name': metric.metric_name,
            'value': float(metric.metric_value) if metric.metric_value else 0,
            'period': metric.period,
            'year': metric.year
        })
    
    export_data = {
        'export_info': {
            'export_date': datetime.now().isoformat(),
            'banks_count': len(banks_data),
            'metrics_count': len(metrics_data)
        },
        'banks': banks_data,
        'financial_metrics': metrics_data
    }
    
    response = make_response(json.dumps(export_data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=banking_sector_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    return response