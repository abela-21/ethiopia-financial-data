"""
Financial Data API Routes for Ethiopian Listed Companies
Provides downloadable financial metrics and statements for ESX-listed companies
"""

from flask import Blueprint, jsonify, request, send_file
from werkzeug.exceptions import HTTPException
from datetime import datetime, date
import pandas as pd
import io
import logging
from decimal import Decimal

from app import db
from models import ListedCompany, CompanyFinancialMetric, FinancialStatement

# Create blueprint
financial_bp = Blueprint('financial', __name__, url_prefix='/api/financial')

# Setup logging
logger = logging.getLogger('api.financial_routes')

def log_request_info():
    """Log request information for analytics"""
    logger.info({
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'params': dict(request.args),
        'financial_endpoint': True
    })

@financial_bp.route('/companies', methods=['GET'])
def get_listed_companies():
    """Get all Ethiopian listed companies available for financial data download"""
    log_request_info()
    
    try:
        # Query parameters
        sector = request.args.get('sector')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # Build query
        query = ListedCompany.query
        
        if sector:
            query = query.filter(ListedCompany.sector.ilike(f'%{sector}%'))
        
        if active_only:
            query = query.filter(ListedCompany.is_active == True)
        
        companies = query.order_by(ListedCompany.market_cap.desc()).all()
        
        # Format response
        companies_data = []
        for company in companies:
            # Get latest financial metrics count
            metrics_count = CompanyFinancialMetric.query.filter_by(company_id=company.id).count()
            statements_count = FinancialStatement.query.filter_by(company_id=company.id).count()
            
            companies_data.append({
                'id': company.id,
                'name': company.name,
                'ticker_symbol': company.ticker_symbol,
                'sector': company.sector,
                'industry': company.industry,
                'market_cap': float(company.market_cap) if company.market_cap else None,
                'market_cap_formatted': f"{company.market_cap:,.0f} ETB" if company.market_cap else "N/A",
                'shares_outstanding': company.shares_outstanding,
                'listing_date': company.listing_date.isoformat() if company.listing_date else None,
                'headquarters': company.headquarters,
                'website_url': company.website_url,
                'logo_url': company.logo_url,
                'description': company.description,
                'ceo_name': company.ceo_name,
                'employee_count': company.employee_count,
                'fiscal_year_end': company.fiscal_year_end,
                'available_metrics': metrics_count,
                'available_statements': statements_count,
                'last_updated': company.updated_at.isoformat() if company.updated_at else None
            })
        
        return jsonify({
            'data': companies_data,
            'pagination': {
                'total': len(companies_data),
                'page': 1,
                'per_page': len(companies_data),
                'pages': 1
            },
            'metadata': {
                'sectors_available': list(set(c.sector for c in companies)),
                'total_market_cap': sum(c.market_cap or 0 for c in companies),
                'data_sources': ['ESX', 'Company Reports', 'NBE', 'Annual Filings']
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching listed companies: {e}")
        return jsonify({'error': 'Failed to fetch companies data'}), 500


@financial_bp.route('/companies/<int:company_id>/metrics', methods=['GET'])
def get_company_metrics(company_id):
    """Get financial metrics for a specific company"""
    log_request_info()
    
    try:
        company = ListedCompany.query.get_or_404(company_id)
        
        # Query parameters
        metric_name = request.args.get('metric_name')
        fiscal_year = request.args.get('fiscal_year', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        query = CompanyFinancialMetric.query.filter_by(company_id=company_id)
        
        if metric_name:
            query = query.filter(CompanyFinancialMetric.metric_name.ilike(f'%{metric_name}%'))
        
        if fiscal_year:
            query = query.filter(CompanyFinancialMetric.fiscal_year == fiscal_year)
        
        metrics = query.order_by(CompanyFinancialMetric.reporting_date.desc()).limit(limit).all()
        
        # Format response
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'id': metric.id,
                'metric_name': metric.metric_name,
                'metric_value': float(metric.metric_value) if metric.metric_value else None,
                'metric_value_formatted': f"{metric.metric_value:,.2f}" if metric.metric_value else "N/A",
                'metric_unit': metric.metric_unit,
                'reporting_period': metric.reporting_period,
                'fiscal_year': metric.fiscal_year,
                'quarter': metric.quarter,
                'reporting_date': metric.reporting_date.isoformat() if metric.reporting_date else None,
                'currency': metric.currency,
                'data_source': metric.data_source,
                'is_audited': metric.is_audited
            })
        
        return jsonify({
            'company': {
                'id': company.id,
                'name': company.name,
                'ticker_symbol': company.ticker_symbol,
                'sector': company.sector
            },
            'data': metrics_data,
            'pagination': {
                'total': len(metrics_data),
                'showing': len(metrics_data),
                'limit': limit
            },
            'available_metrics': list(set(m.metric_name for m in metrics)),
            'date_range': {
                'latest': metrics[0].reporting_date.isoformat() if metrics else None,
                'earliest': metrics[-1].reporting_date.isoformat() if metrics else None
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company metrics: {e}")
        return jsonify({'error': 'Failed to fetch company metrics'}), 500


@financial_bp.route('/companies/<int:company_id>/statements', methods=['GET'])
def get_company_statements(company_id):
    """Get financial statements for a specific company"""
    log_request_info()
    
    try:
        company = ListedCompany.query.get_or_404(company_id)
        
        # Query parameters
        statement_type = request.args.get('statement_type')
        fiscal_year = request.args.get('fiscal_year', type=int)
        
        # Build query
        query = FinancialStatement.query.filter_by(company_id=company_id)
        
        if statement_type:
            query = query.filter(FinancialStatement.statement_type == statement_type)
        
        if fiscal_year:
            query = query.filter(FinancialStatement.fiscal_year == fiscal_year)
        
        statements = query.order_by(FinancialStatement.period_end_date.desc()).all()
        
        # Format response
        statements_data = []
        for stmt in statements:
            statement_data = {
                'id': stmt.id,
                'statement_type': stmt.statement_type,
                'reporting_period': stmt.reporting_period,
                'fiscal_year': stmt.fiscal_year,
                'period_start_date': stmt.period_start_date.isoformat() if stmt.period_start_date else None,
                'period_end_date': stmt.period_end_date.isoformat() if stmt.period_end_date else None,
                'filing_date': stmt.filing_date.isoformat() if stmt.filing_date else None,
                'currency': stmt.currency,
                'is_audited': stmt.is_audited,
                'auditor_name': stmt.auditor_name,
                'data_source': stmt.data_source,
                'file_url': stmt.file_url
            }
            
            # Add financial data based on statement type
            if stmt.statement_type == 'income_statement':
                statement_data.update({
                    'revenue': float(stmt.revenue) if stmt.revenue else None,
                    'gross_profit': float(stmt.gross_profit) if stmt.gross_profit else None,
                    'operating_income': float(stmt.operating_income) if stmt.operating_income else None,
                    'net_income': float(stmt.net_income) if stmt.net_income else None,
                    'earnings_per_share': float(stmt.earnings_per_share) if stmt.earnings_per_share else None
                })
            elif stmt.statement_type == 'balance_sheet':
                statement_data.update({
                    'total_assets': float(stmt.total_assets) if stmt.total_assets else None,
                    'current_assets': float(stmt.current_assets) if stmt.current_assets else None,
                    'total_liabilities': float(stmt.total_liabilities) if stmt.total_liabilities else None,
                    'shareholders_equity': float(stmt.shareholders_equity) if stmt.shareholders_equity else None,
                    'cash_and_equivalents': float(stmt.cash_and_equivalents) if stmt.cash_and_equivalents else None
                })
            elif stmt.statement_type == 'cash_flow':
                statement_data.update({
                    'operating_cash_flow': float(stmt.operating_cash_flow) if stmt.operating_cash_flow else None,
                    'investing_cash_flow': float(stmt.investing_cash_flow) if stmt.investing_cash_flow else None,
                    'financing_cash_flow': float(stmt.financing_cash_flow) if stmt.financing_cash_flow else None,
                    'free_cash_flow': float(stmt.free_cash_flow) if stmt.free_cash_flow else None
                })
            
            # Add banking-specific metrics for bank companies
            if company.sector == 'Banking':
                statement_data.update({
                    'deposits': float(stmt.deposits) if stmt.deposits else None,
                    'loans_and_advances': float(stmt.loans_and_advances) if stmt.loans_and_advances else None,
                    'net_interest_income': float(stmt.net_interest_income) if stmt.net_interest_income else None,
                    'loan_loss_provisions': float(stmt.loan_loss_provisions) if stmt.loan_loss_provisions else None
                })
            
            statements_data.append(statement_data)
        
        return jsonify({
            'company': {
                'id': company.id,
                'name': company.name,
                'ticker_symbol': company.ticker_symbol,
                'sector': company.sector
            },
            'data': statements_data,
            'pagination': {
                'total': len(statements_data),
                'showing': len(statements_data)
            },
            'available_statement_types': list(set(s.statement_type for s in statements)),
            'fiscal_years_available': sorted(list(set(s.fiscal_year for s in statements)), reverse=True)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company statements: {e}")
        return jsonify({'error': 'Failed to fetch company statements'}), 500


@financial_bp.route('/download/metrics', methods=['POST'])
def download_financial_metrics():
    """Download financial metrics as Excel file"""
    log_request_info()
    
    try:
        # Get request data
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        metric_names = data.get('metric_names', [])
        fiscal_years = data.get('fiscal_years', [])
        format_type = data.get('format', 'excel')  # excel, csv
        
        if not company_ids:
            return jsonify({'error': 'At least one company ID required'}), 400
        
        # Build query
        query = CompanyFinancialMetric.query.filter(CompanyFinancialMetric.company_id.in_(company_ids))
        
        if metric_names:
            query = query.filter(CompanyFinancialMetric.metric_name.in_(metric_names))
        
        if fiscal_years:
            query = query.filter(CompanyFinancialMetric.fiscal_year.in_(fiscal_years))
        
        metrics = query.order_by(
            CompanyFinancialMetric.company_id,
            CompanyFinancialMetric.reporting_date.desc()
        ).all()
        
        if not metrics:
            return jsonify({'error': 'No financial data found for selected criteria'}), 404
        
        # Prepare data for export
        export_data = []
        for metric in metrics:
            export_data.append({
                'Company': metric.company.name,
                'Ticker Symbol': metric.company.ticker_symbol,
                'Sector': metric.company.sector,
                'Metric Name': metric.metric_name,
                'Value': float(metric.metric_value) if metric.metric_value else None,
                'Unit': metric.metric_unit,
                'Currency': metric.currency,
                'Reporting Period': metric.reporting_period,
                'Fiscal Year': metric.fiscal_year,
                'Quarter': metric.quarter,
                'Reporting Date': metric.reporting_date,
                'Data Source': metric.data_source,
                'Is Audited': metric.is_audited
            })
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Generate file
        output = io.BytesIO()
        
        if format_type == 'excel':
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Financial Metrics', index=False)
                
                # Add metadata sheet
                metadata_df = pd.DataFrame({
                    'Export Information': [
                        'Export Date',
                        'Total Records',
                        'Companies Included',
                        'Date Range',
                        'Data Sources'
                    ],
                    'Value': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        len(export_data),
                        ', '.join(set(d['Company'] for d in export_data)),
                        f"{min(d['Reporting Date'] for d in export_data)} to {max(d['Reporting Date'] for d in export_data)}",
                        ', '.join(set(d['Data Source'] for d in export_data if d['Data Source']))
                    ]
                })
                metadata_df.to_excel(writer, sheet_name='Export Info', index=False)
            
            output.seek(0)
            filename = f"ethiopian_financial_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
        else:  # CSV format
            df.to_csv(output, index=False)
            output.seek(0)
            filename = f"ethiopian_financial_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mimetype = 'text/csv'
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating financial metrics download: {e}")
        return jsonify({'error': 'Failed to generate download file'}), 500


@financial_bp.route('/download/statements', methods=['POST'])
def download_financial_statements():
    """Download complete financial statements as Excel file"""
    log_request_info()
    
    try:
        # Get request data
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        statement_types = data.get('statement_types', [])
        fiscal_years = data.get('fiscal_years', [])
        format_type = data.get('format', 'excel')
        
        if not company_ids:
            return jsonify({'error': 'At least one company ID required'}), 400
        
        # Build query
        query = FinancialStatement.query.filter(FinancialStatement.company_id.in_(company_ids))
        
        if statement_types:
            query = query.filter(FinancialStatement.statement_type.in_(statement_types))
        
        if fiscal_years:
            query = query.filter(FinancialStatement.fiscal_year.in_(fiscal_years))
        
        statements = query.order_by(
            FinancialStatement.company_id,
            FinancialStatement.period_end_date.desc()
        ).all()
        
        if not statements:
            return jsonify({'error': 'No financial statements found for selected criteria'}), 404
        
        # Generate file
        output = io.BytesIO()
        
        if format_type == 'excel':
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                
                # Group by statement type
                for stmt_type in set(s.statement_type for s in statements):
                    stmt_data = []
                    type_statements = [s for s in statements if s.statement_type == stmt_type]
                    
                    for stmt in type_statements:
                        row_data = {
                            'Company': stmt.company.name,
                            'Ticker Symbol': stmt.company.ticker_symbol,
                            'Reporting Period': stmt.reporting_period,
                            'Fiscal Year': stmt.fiscal_year,
                            'Period End Date': stmt.period_end_date,
                            'Currency': stmt.currency,
                            'Is Audited': stmt.is_audited,
                            'Data Source': stmt.data_source
                        }
                        
                        # Add statement-specific fields
                        if stmt_type == 'income_statement':
                            row_data.update({
                                'Revenue': float(stmt.revenue) if stmt.revenue else None,
                                'Gross Profit': float(stmt.gross_profit) if stmt.gross_profit else None,
                                'Operating Income': float(stmt.operating_income) if stmt.operating_income else None,
                                'Net Income': float(stmt.net_income) if stmt.net_income else None,
                                'EPS': float(stmt.earnings_per_share) if stmt.earnings_per_share else None
                            })
                        elif stmt_type == 'balance_sheet':
                            row_data.update({
                                'Total Assets': float(stmt.total_assets) if stmt.total_assets else None,
                                'Current Assets': float(stmt.current_assets) if stmt.current_assets else None,
                                'Cash & Equivalents': float(stmt.cash_and_equivalents) if stmt.cash_and_equivalents else None,
                                'Total Liabilities': float(stmt.total_liabilities) if stmt.total_liabilities else None,
                                'Shareholders Equity': float(stmt.shareholders_equity) if stmt.shareholders_equity else None
                            })
                        elif stmt_type == 'cash_flow':
                            row_data.update({
                                'Operating Cash Flow': float(stmt.operating_cash_flow) if stmt.operating_cash_flow else None,
                                'Investing Cash Flow': float(stmt.investing_cash_flow) if stmt.investing_cash_flow else None,
                                'Financing Cash Flow': float(stmt.financing_cash_flow) if stmt.financing_cash_flow else None,
                                'Free Cash Flow': float(stmt.free_cash_flow) if stmt.free_cash_flow else None
                            })
                        
                        # Add banking-specific fields for bank companies
                        if stmt.company.sector == 'Banking':
                            row_data.update({
                                'Deposits': float(stmt.deposits) if stmt.deposits else None,
                                'Loans & Advances': float(stmt.loans_and_advances) if stmt.loans_and_advances else None,
                                'Net Interest Income': float(stmt.net_interest_income) if stmt.net_interest_income else None,
                                'Loan Loss Provisions': float(stmt.loan_loss_provisions) if stmt.loan_loss_provisions else None
                            })
                        
                        stmt_data.append(row_data)
                    
                    # Create sheet for this statement type
                    df = pd.DataFrame(stmt_data)
                    sheet_name = stmt_type.replace('_', ' ').title()
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
            output.seek(0)
            filename = f"ethiopian_financial_statements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
        else:  # CSV format - single sheet with all data
            all_data = []
            for stmt in statements:
                row_data = {
                    'Company': stmt.company.name,
                    'Ticker Symbol': stmt.company.ticker_symbol,
                    'Statement Type': stmt.statement_type,
                    'Reporting Period': stmt.reporting_period,
                    'Fiscal Year': stmt.fiscal_year,
                    'Period End Date': stmt.period_end_date,
                    'Currency': stmt.currency,
                    'Revenue': float(stmt.revenue) if stmt.revenue else None,
                    'Net Income': float(stmt.net_income) if stmt.net_income else None,
                    'Total Assets': float(stmt.total_assets) if stmt.total_assets else None,
                    'Total Liabilities': float(stmt.total_liabilities) if stmt.total_liabilities else None,
                    'Operating Cash Flow': float(stmt.operating_cash_flow) if stmt.operating_cash_flow else None,
                    'Data Source': stmt.data_source
                }
                all_data.append(row_data)
            
            df = pd.DataFrame(all_data)
            df.to_csv(output, index=False)
            output.seek(0)
            filename = f"ethiopian_financial_statements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mimetype = 'text/csv'
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating financial statements download: {e}")
        return jsonify({'error': 'Failed to generate download file'}), 500


@financial_bp.route('/summary', methods=['GET'])
def get_financial_summary():
    """Get summary statistics of available financial data"""
    log_request_info()
    
    try:
        # Company statistics
        total_companies = ListedCompany.query.filter_by(is_active=True).count()
        sectors = db.session.query(ListedCompany.sector).distinct().all()
        total_market_cap = db.session.query(db.func.sum(ListedCompany.market_cap)).scalar() or 0
        
        # Metrics statistics
        total_metrics = CompanyFinancialMetric.query.count()
        latest_reporting_date = db.session.query(db.func.max(CompanyFinancialMetric.reporting_date)).scalar()
        available_metrics = db.session.query(CompanyFinancialMetric.metric_name).distinct().all()
        
        # Statements statistics
        total_statements = FinancialStatement.query.count()
        statement_types = db.session.query(FinancialStatement.statement_type).distinct().all()
        fiscal_years = db.session.query(FinancialStatement.fiscal_year).distinct().order_by(FinancialStatement.fiscal_year.desc()).all()
        
        return jsonify({
            'companies': {
                'total_listed': total_companies,
                'sectors': [s[0] for s in sectors],
                'total_market_cap': float(total_market_cap),
                'market_cap_formatted': f"{total_market_cap:,.0f} ETB"
            },
            'metrics': {
                'total_data_points': total_metrics,
                'latest_update': latest_reporting_date.isoformat() if latest_reporting_date else None,
                'available_metrics': [m[0] for m in available_metrics],
                'metrics_count': len(available_metrics)
            },
            'statements': {
                'total_statements': total_statements,
                'statement_types': [s[0] for s in statement_types],
                'fiscal_years_available': [y[0] for y in fiscal_years],
                'data_coverage': f"{fiscal_years[-1][0]}-{fiscal_years[0][0]}" if fiscal_years else "N/A"
            },
            'download_formats': ['excel', 'csv'],
            'data_sources': ['ESX', 'Company Annual Reports', 'Quarterly Filings', 'NBE Banking Data'],
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating financial summary: {e}")
        return jsonify({'error': 'Failed to generate summary statistics'}), 500