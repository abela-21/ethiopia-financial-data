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

@export_bp.route('/macro-indicators', methods=['POST'])
def export_macro_data():
    """Export macro indicators data with multi-variable selection support"""
    try:
        from models import MacroIndicators
        
        data = request.get_json()
        export_format = data.get('format', 'excel')
        variables = data.get('variables', [])  # List of selected macro variables
        date_range = data.get('date_range', {})
        
        # Build query for macro indicators
        query = MacroIndicators.query
        
        if date_range.get('start'):
            start_date = datetime.strptime(date_range['start'], '%Y-%m-%d').date()
            query = query.filter(MacroIndicators.date >= start_date)
        
        if date_range.get('end'):
            end_date = datetime.strptime(date_range['end'], '%Y-%m-%d').date()
            query = query.filter(MacroIndicators.date <= end_date)
        
        macro_data = query.order_by(MacroIndicators.date.desc()).all()
        
        if export_format == 'excel':
            return _export_macro_excel(macro_data, variables)
        elif export_format == 'csv':
            return _export_macro_csv(macro_data, variables)
        elif export_format == 'json':
            return _export_macro_json(macro_data, variables)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting macro data: {str(e)}")
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

def _export_macro_excel(macro_data, variables):
    """Export macro indicators to Excel with multi-variable support"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Create main data sheet
    worksheet = workbook.add_worksheet('Macro Indicators')
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    percent_format = workbook.add_format({'num_format': '0.00%'})
    
    # Define all available variables and their display names
    all_variables = {
        'gdp_growth': ('GDP Growth (%)', percent_format),
        'gdp_per_capita': ('GDP Per Capita (ETB)', money_format),
        'inflation_rate': ('Inflation Rate (%)', percent_format),
        'interest_rate': ('Interest Rate (%)', percent_format),
        'unemployment_rate': ('Unemployment Rate (%)', percent_format),
        'etb_usd': ('ETB/USD Exchange Rate', None),
        'etb_eur': ('ETB/EUR Exchange Rate', None),
        'etb_gbp': ('ETB/GBP Exchange Rate', None),
        'etb_jpy': ('ETB/JPY Exchange Rate', None),
        'fx_reserves': ('FX Reserves (USD)', money_format),
        'trade_balance': ('Trade Balance (ETB)', money_format),
        'current_account_balance': ('Current Account Balance (ETB)', money_format),
        'total_deposits': ('Total Bank Deposits (ETB)', money_format),
        'total_loans': ('Total Bank Loans (ETB)', money_format),
        'npl_ratio': ('NPL Ratio (%)', percent_format)
    }
    
    # Use selected variables or all if none specified
    if not variables:
        variables = list(all_variables.keys())
    
    # Write headers
    headers = ['Date'] + [all_variables[var][0] for var in variables if var in all_variables]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Write data
    for row, indicator in enumerate(macro_data, 1):
        worksheet.write(row, 0, indicator.date.strftime('%Y-%m-%d'))
        
        for col, variable in enumerate(variables, 1):
            if variable in all_variables:
                value = getattr(indicator, variable, None)
                if value is not None:
                    format_type = all_variables[variable][1]
                    if format_type:
                        worksheet.write(row, col, float(value), format_type)
                    else:
                        worksheet.write(row, col, float(value))
                else:
                    worksheet.write(row, col, '')
    
    # Add summary sheet
    summary_sheet = workbook.add_worksheet('Export Summary')
    summary_sheet.write(0, 0, 'Macro Indicators Export Summary', header_format)
    summary_sheet.write(1, 0, 'Total Records:')
    summary_sheet.write(1, 1, len(macro_data))
    summary_sheet.write(2, 0, 'Variables Exported:')
    summary_sheet.write(2, 1, len(variables))
    summary_sheet.write(3, 0, 'Export Date:')
    summary_sheet.write(3, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # List exported variables
    summary_sheet.write(4, 0, 'Selected Variables:', header_format)
    for i, var in enumerate(variables):
        if var in all_variables:
            summary_sheet.write(5 + i, 0, all_variables[var][0])
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'macro_indicators_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def _export_macro_csv(macro_data, variables):
    """Export macro indicators to CSV with multi-variable support"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Define variable mappings
    all_variables = {
        'gdp_growth': 'GDP Growth (%)',
        'gdp_per_capita': 'GDP Per Capita (ETB)',
        'inflation_rate': 'Inflation Rate (%)',
        'interest_rate': 'Interest Rate (%)',
        'unemployment_rate': 'Unemployment Rate (%)',
        'etb_usd': 'ETB/USD Exchange Rate',
        'etb_eur': 'ETB/EUR Exchange Rate',
        'etb_gbp': 'ETB/GBP Exchange Rate',
        'etb_jpy': 'ETB/JPY Exchange Rate',
        'fx_reserves': 'FX Reserves (USD)',
        'trade_balance': 'Trade Balance (ETB)',
        'current_account_balance': 'Current Account Balance (ETB)',
        'total_deposits': 'Total Bank Deposits (ETB)',
        'total_loans': 'Total Bank Loans (ETB)',
        'npl_ratio': 'NPL Ratio (%)'
    }
    
    # Use selected variables or all if none specified
    if not variables:
        variables = list(all_variables.keys())
    
    # Write header
    headers = ['Date'] + [all_variables[var] for var in variables if var in all_variables]
    writer.writerow(headers)
    
    # Write data
    for indicator in macro_data:
        row = [indicator.date.strftime('%Y-%m-%d')]
        for variable in variables:
            if variable in all_variables:
                value = getattr(indicator, variable, None)
                row.append(value if value is not None else '')
        writer.writerow(row)
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=macro_indicators_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def _export_macro_json(macro_data, variables):
    """Export macro indicators to JSON with multi-variable support"""
    # Define variable mappings
    all_variables = {
        'gdp_growth': 'GDP Growth (%)',
        'gdp_per_capita': 'GDP Per Capita (ETB)',
        'inflation_rate': 'Inflation Rate (%)',
        'interest_rate': 'Interest Rate (%)',
        'unemployment_rate': 'Unemployment Rate (%)',
        'etb_usd': 'ETB/USD Exchange Rate',
        'etb_eur': 'ETB/EUR Exchange Rate',
        'etb_gbp': 'ETB/GBP Exchange Rate',
        'etb_jpy': 'ETB/JPY Exchange Rate',
        'fx_reserves': 'FX Reserves (USD)',
        'trade_balance': 'Trade Balance (ETB)',
        'current_account_balance': 'Current Account Balance (ETB)',
        'total_deposits': 'Total Bank Deposits (ETB)',
        'total_loans': 'Total Bank Loans (ETB)',
        'npl_ratio': 'NPL Ratio (%)'
    }
    
    # Use selected variables or all if none specified
    if not variables:
        variables = list(all_variables.keys())
    
    data = []
    for indicator in macro_data:
        indicator_data = {'date': indicator.date.strftime('%Y-%m-%d')}
        for variable in variables:
            if variable in all_variables and hasattr(indicator, variable):
                value = getattr(indicator, variable, None)
                indicator_data[variable] = float(value) if value is not None else None
        data.append(indicator_data)
    
    export_data = {
        'export_info': {
            'export_date': datetime.now().isoformat(),
            'total_records': len(data),
            'variables_exported': [all_variables[var] for var in variables if var in all_variables],
            'selected_variables': variables
        },
        'data': data
    }
    
    response = make_response(json.dumps(export_data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=macro_indicators_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
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
    bank_headers = ['License Number', 'Bank Name', 'Type', 'Ownership', 'Branches', 'NBE Rating', 'Establishment Date', 'Headquarters']
    for col, header in enumerate(bank_headers):
        banks_sheet.write(0, col, header, header_format)
    
    for row, bank in enumerate(banks, 1):
        banks_sheet.write(row, 0, bank.license_number or '')
        banks_sheet.write(row, 1, bank.name)
        banks_sheet.write(row, 2, bank.bank_type or '')
        banks_sheet.write(row, 3, bank.ownership_type or '')
        banks_sheet.write(row, 4, bank.branch_count or 0)
        banks_sheet.write(row, 5, bank.nbe_rating or '')
        banks_sheet.write(row, 6, bank.establishment_date.strftime('%Y-%m-%d') if bank.establishment_date else '')
        banks_sheet.write(row, 7, bank.headquarters_location or '')
    
    # Write financial metrics data
    metric_headers = ['Bank ID', 'Bank Name', 'Reporting Date', 'Total Assets', 'Total Deposits', 'Total Loans', 'Net Profit', 'CAR', 'NPL Ratio']
    for col, header in enumerate(metric_headers):
        metrics_sheet.write(0, col, header, header_format)
    
    for row, metric in enumerate(bank_metrics, 1):
        metrics_sheet.write(row, 0, metric.bank_id)
        metrics_sheet.write(row, 1, metric.bank.name if metric.bank else '')
        metrics_sheet.write(row, 2, metric.reporting_date.strftime('%Y-%m-%d') if metric.reporting_date else '')
        metrics_sheet.write(row, 3, float(metric.total_assets) if metric.total_assets else 0, money_format)
        metrics_sheet.write(row, 4, float(metric.total_deposits) if metric.total_deposits else 0, money_format)
        metrics_sheet.write(row, 5, float(metric.total_loans) if metric.total_loans else 0, money_format)
        metrics_sheet.write(row, 6, float(metric.net_profit) if metric.net_profit else 0, money_format)
        metrics_sheet.write(row, 7, float(metric.capital_adequacy_ratio) if metric.capital_adequacy_ratio else 0, percent_format)
        metrics_sheet.write(row, 8, float(metric.npl_ratio) if metric.npl_ratio else 0, percent_format)
    
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
    writer.writerow(['License Number', 'Bank Name', 'Type', 'Ownership', 'Branches', 'NBE Rating', 'Establishment Date', 'Headquarters'])
    
    for bank in banks:
        writer.writerow([
            bank.license_number or '',
            bank.name,
            bank.bank_type or '',
            bank.ownership_type or '',
            bank.branch_count or 0,
            bank.nbe_rating or '',
            bank.establishment_date.strftime('%Y-%m-%d') if bank.establishment_date else '',
            bank.headquarters_location or ''
        ])
    
    # Write metrics section
    writer.writerow([])
    writer.writerow(['=== FINANCIAL METRICS ==='])
    writer.writerow(['Bank ID', 'Bank Name', 'Reporting Date', 'Total Assets', 'Total Deposits', 'Total Loans', 'Net Profit'])
    
    for metric in bank_metrics:
        writer.writerow([
            metric.bank_id,
            metric.bank.name if metric.bank else '',
            metric.reporting_date.strftime('%Y-%m-%d') if metric.reporting_date else '',
            metric.total_assets or 0,
            metric.total_deposits or 0,
            metric.total_loans or 0,
            metric.net_profit or 0
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