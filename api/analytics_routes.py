"""
Advanced Analytics API Routes
Provides sophisticated financial analysis endpoints for interactive dashboards
"""

from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, ListedCompany, CompanyFinancialMetric
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

def log_request(endpoint_type='analytics'):
    """Log API request details for monitoring"""
    logger.info({
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'params': dict(request.args),
        'analytics_endpoint': endpoint_type == 'analytics'
    })

@analytics_bp.route('/comparison', methods=['GET'])
@limiter.limit("30 per minute")
def get_comparison_data():
    """
    Advanced company comparison analytics
    Returns comparative financial metrics across selected companies
    """
    log_request('comparison')
    
    try:
        # Get query parameters
        company_ids = request.args.getlist('company_ids')
        metrics = request.args.getlist('metrics') or ['total_revenue', 'net_income', 'total_assets']
        period = request.args.get('period', '1Y')
        
        if not company_ids:
            return jsonify({'error': 'No company IDs provided'}), 400
        
        # Convert string IDs to integers
        try:
            company_ids = [int(cid) for cid in company_ids]
        except ValueError:
            return jsonify({'error': 'Invalid company ID format'}), 400
        
        # Get companies
        companies = ListedCompany.query.filter(
            ListedCompany.id.in_(company_ids),
            ListedCompany.is_active == True
        ).all()
        
        if not companies:
            return jsonify({'error': 'No valid companies found'}), 404
        
        comparison_data = {}
        
        for company in companies:
            # Get financial metrics for this company
            company_metrics = db.session.query(CompanyFinancialMetric).filter(
                CompanyFinancialMetric.company_id == company.id,
                CompanyFinancialMetric.metric_name.in_(metrics)
            ).all()
            
            # Organize metrics by name
            metrics_dict = {}
            for metric in company_metrics:
                metrics_dict[metric.metric_name] = {
                    'value': float(metric.metric_value),
                    'formatted_value': metric.metric_value_formatted,
                    'unit': metric.metric_unit,
                    'period': metric.reporting_period,
                    'data_source': metric.data_source,
                    'is_audited': metric.is_audited
                }
            
            # Calculate derived metrics
            derived_metrics = calculate_derived_metrics(metrics_dict, company)
            metrics_dict.update(derived_metrics)
            
            comparison_data[company.id] = {
                'company': {
                    'id': company.id,
                    'name': company.name,
                    'ticker_symbol': company.ticker_symbol,
                    'sector': company.sector,
                    'industry': company.industry,
                    'market_cap': company.market_cap,
                    'market_cap_formatted': format_currency(company.market_cap)
                },
                'metrics': metrics_dict,
                'performance_score': calculate_performance_score(metrics_dict, company.sector)
            }
        
        # Calculate sector benchmarks
        sector_benchmarks = calculate_sector_benchmarks(companies, metrics)
        
        # Calculate performance rankings
        rankings = calculate_performance_rankings(comparison_data, metrics)
        
        return jsonify({
            'success': True,
            'data': comparison_data,
            'sector_benchmarks': sector_benchmarks,
            'performance_rankings': rankings,
            'metadata': {
                'companies_count': len(companies),
                'metrics_count': len(metrics),
                'period': period,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in comparison analytics: {str(e)}")
        return jsonify({'error': 'Failed to generate comparison analytics'}), 500

@analytics_bp.route('/trends', methods=['GET'])
@limiter.limit("20 per minute")
def get_trend_analysis():
    """
    Historical trend analysis for financial metrics
    Generates time-series data for interactive trend charts
    """
    log_request('trends')
    
    try:
        company_ids = request.args.getlist('company_ids')
        metrics = request.args.getlist('metrics') or ['total_revenue']
        period = request.args.get('period', '2Y')
        
        if not company_ids:
            return jsonify({'error': 'No company IDs provided'}), 400
        
        company_ids = [int(cid) for cid in company_ids]
        
        # Get companies
        companies = ListedCompany.query.filter(
            ListedCompany.id.in_(company_ids),
            ListedCompany.is_active == True
        ).all()
        
        trend_data = {}
        
        for company in companies:
            # Get historical data (simulated quarterly progression)
            company_trends = {}
            
            for metric in metrics:
                # Get current metric value
                current_metric = db.session.query(CompanyFinancialMetric).filter(
                    CompanyFinancialMetric.company_id == company.id,
                    CompanyFinancialMetric.metric_name == metric
                ).first()
                
                if current_metric:
                    # Generate historical trend based on current value
                    trend_series = generate_trend_series(
                        float(current_metric.metric_value),
                        metric,
                        period,
                        company.sector
                    )
                    
                    company_trends[metric] = {
                        'data_points': trend_series,
                        'current_value': float(current_metric.metric_value),
                        'growth_rate': calculate_growth_rate(trend_series),
                        'volatility': calculate_volatility(trend_series),
                        'trend_direction': determine_trend_direction(trend_series)
                    }
            
            trend_data[company.id] = {
                'company': {
                    'id': company.id,
                    'name': company.name,
                    'ticker_symbol': company.ticker_symbol,
                    'sector': company.sector
                },
                'trends': company_trends
            }
        
        # Generate time labels
        time_labels = generate_time_labels(period)
        
        return jsonify({
            'success': True,
            'data': trend_data,
            'time_labels': time_labels,
            'metadata': {
                'companies_count': len(companies),
                'metrics_count': len(metrics),
                'period': period,
                'data_frequency': 'quarterly',
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in trend analysis: {str(e)}")
        return jsonify({'error': 'Failed to generate trend analysis'}), 500

@analytics_bp.route('/sector-analysis', methods=['GET'])
@limiter.limit("15 per minute")
def get_sector_analysis():
    """
    Comprehensive sector-level analysis and benchmarking
    Provides industry averages and competitive positioning
    """
    log_request('sector_analysis')
    
    try:
        sector = request.args.get('sector')
        include_all_sectors = request.args.get('include_all', 'false').lower() == 'true'
        
        if sector and not include_all_sectors:
            # Analysis for specific sector
            companies = ListedCompany.query.filter(
                ListedCompany.sector == sector,
                ListedCompany.is_active == True
            ).all()
            sectors_to_analyze = [sector]
        else:
            # Analysis for all sectors
            companies = ListedCompany.query.filter(ListedCompany.is_active == True).all()
            sectors_to_analyze = list(set([c.sector for c in companies]))
        
        sector_analysis = {}
        
        for sector_name in sectors_to_analyze:
            sector_companies = [c for c in companies if c.sector == sector_name]
            
            if not sector_companies:
                continue
            
            # Calculate sector metrics
            sector_metrics = calculate_sector_metrics(sector_companies)
            
            # Get top performers in sector
            top_performers = get_sector_top_performers(sector_companies, 3)
            
            # Calculate sector growth and trends
            sector_trends = calculate_sector_trends(sector_companies)
            
            sector_analysis[sector_name] = {
                'sector_name': sector_name,
                'company_count': len(sector_companies),
                'total_market_cap': sum([c.market_cap for c in sector_companies]),
                'average_metrics': sector_metrics,
                'top_performers': top_performers,
                'sector_trends': sector_trends,
                'competitive_landscape': assess_competitive_landscape(sector_companies)
            }
        
        # Cross-sector comparison
        cross_sector_comparison = generate_cross_sector_comparison(sector_analysis)
        
        return jsonify({
            'success': True,
            'data': sector_analysis,
            'cross_sector_comparison': cross_sector_comparison,
            'metadata': {
                'sectors_analyzed': len(sectors_to_analyze),
                'total_companies': len(companies),
                'analysis_date': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in sector analysis: {str(e)}")
        return jsonify({'error': 'Failed to generate sector analysis'}), 500

@analytics_bp.route('/performance-metrics', methods=['GET'])
@limiter.limit("25 per minute")
def get_performance_metrics():
    """
    Advanced performance metrics and KPI calculations
    Returns comprehensive financial health indicators
    """
    log_request('performance_metrics')
    
    try:
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'Company ID required'}), 400
        
        company = ListedCompany.query.filter(
            ListedCompany.id == int(company_id),
            ListedCompany.is_active == True
        ).first()
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get all financial metrics for the company
        metrics = db.session.query(CompanyFinancialMetric).filter(
            CompanyFinancialMetric.company_id == company.id
        ).all()
        
        metrics_dict = {m.metric_name: float(m.metric_value) for m in metrics}
        
        # Calculate comprehensive performance indicators
        performance_metrics = {
            'profitability': calculate_profitability_metrics(metrics_dict),
            'liquidity': calculate_liquidity_metrics(metrics_dict),
            'efficiency': calculate_efficiency_metrics(metrics_dict),
            'growth': calculate_growth_metrics(metrics_dict, company.sector),
            'valuation': calculate_valuation_metrics(metrics_dict, company),
            'risk_assessment': calculate_risk_metrics(metrics_dict, company.sector)
        }
        
        # Calculate overall financial health score
        health_score = calculate_financial_health_score(performance_metrics)
        
        # Industry comparison
        industry_comparison = compare_to_industry(company, metrics_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'company': {
                    'id': company.id,
                    'name': company.name,
                    'ticker_symbol': company.ticker_symbol,
                    'sector': company.sector,
                    'industry': company.industry
                },
                'performance_metrics': performance_metrics,
                'financial_health_score': health_score,
                'industry_comparison': industry_comparison,
                'recommendations': generate_performance_recommendations(performance_metrics, company.sector)
            },
            'metadata': {
                'metrics_calculated': len(performance_metrics),
                'calculation_date': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in performance metrics: {str(e)}")
        return jsonify({'error': 'Failed to calculate performance metrics'}), 500

# Helper Functions

def calculate_derived_metrics(metrics_dict, company):
    """Calculate additional derived financial metrics"""
    derived = {}
    
    # Asset turnover ratio
    if 'total_revenue' in metrics_dict and 'total_assets' in metrics_dict:
        revenue = metrics_dict['total_revenue']['value']
        assets = metrics_dict['total_assets']['value']
        if assets > 0:
            derived['asset_turnover_ratio'] = {
                'value': revenue / assets,
                'formatted_value': f"{(revenue / assets):.2f}x",
                'unit': 'times',
                'period': 'calculated',
                'data_source': 'derived',
                'is_audited': False
            }
    
    # Revenue per employee
    if 'total_revenue' in metrics_dict and company.employee_count:
        revenue = metrics_dict['total_revenue']['value']
        derived['revenue_per_employee'] = {
            'value': revenue / company.employee_count,
            'formatted_value': format_currency(revenue / company.employee_count),
            'unit': 'ETB',
            'period': 'calculated',
            'data_source': 'derived',
            'is_audited': False
        }
    
    return derived

def calculate_performance_score(metrics_dict, sector):
    """Calculate overall performance score for a company"""
    score = 0
    factors = 0
    
    # ROA scoring
    if 'return_on_assets' in metrics_dict:
        roa = metrics_dict['return_on_assets']['value']
        if roa > 15:
            score += 25
        elif roa > 10:
            score += 20
        elif roa > 5:
            score += 15
        else:
            score += 10
        factors += 1
    
    # Revenue growth scoring (simulated)
    if 'total_revenue' in metrics_dict:
        score += 20  # Assume positive revenue growth
        factors += 1
    
    # Asset efficiency
    if 'asset_turnover_ratio' in metrics_dict:
        turnover = metrics_dict['asset_turnover_ratio']['value']
        if turnover > 1.5:
            score += 25
        elif turnover > 1.0:
            score += 20
        else:
            score += 15
        factors += 1
    
    # Sector adjustment
    sector_multipliers = {
        'Banking': 0.9,
        'Telecommunications': 1.1,
        'Transportation': 1.0,
        'Consumer Goods': 1.0,
        'Materials': 0.95
    }
    
    multiplier = sector_multipliers.get(sector, 1.0)
    
    return min(100, (score / max(factors, 1)) * multiplier) if factors > 0 else 50

def calculate_sector_benchmarks(companies, metrics):
    """Calculate sector-wide benchmark metrics"""
    sector_data = {}
    
    for company in companies:
        sector = company.sector
        if sector not in sector_data:
            sector_data[sector] = {'companies': [], 'metrics': {}}
        
        sector_data[sector]['companies'].append(company)
        
        # Get company metrics
        company_metrics = db.session.query(CompanyFinancialMetric).filter(
            CompanyFinancialMetric.company_id == company.id,
            CompanyFinancialMetric.metric_name.in_(metrics)
        ).all()
        
        for metric in company_metrics:
            if metric.metric_name not in sector_data[sector]['metrics']:
                sector_data[sector]['metrics'][metric.metric_name] = []
            sector_data[sector]['metrics'][metric.metric_name].append(float(metric.metric_value))
    
    # Calculate averages
    benchmarks = {}
    for sector, data in sector_data.items():
        benchmarks[sector] = {}
        for metric_name, values in data['metrics'].items():
            if values:
                benchmarks[sector][metric_name] = {
                    'average': sum(values) / len(values),
                    'median': sorted(values)[len(values) // 2],
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
    
    return benchmarks

def calculate_performance_rankings(comparison_data, metrics):
    """Calculate performance rankings across companies"""
    rankings = {}
    
    for metric in metrics:
        metric_values = []
        for company_id, data in comparison_data.items():
            if metric in data['metrics']:
                metric_values.append({
                    'company_id': company_id,
                    'company_name': data['company']['name'],
                    'ticker_symbol': data['company']['ticker_symbol'],
                    'value': data['metrics'][metric]['value']
                })
        
        # Sort by value (descending for most metrics)
        metric_values.sort(key=lambda x: x['value'], reverse=True)
        
        rankings[metric] = metric_values
    
    return rankings

def generate_trend_series(base_value, metric_name, period, sector):
    """Generate realistic trend data based on sector and metric characteristics"""
    periods = {'1Y': 4, '2Y': 8, '5Y': 20}
    points = periods.get(period, 8)
    
    # Sector-specific growth patterns
    growth_patterns = {
        'Banking': {'revenue': 0.08, 'assets': 0.12, 'volatility': 0.15},
        'Telecommunications': {'revenue': 0.15, 'assets': 0.10, 'volatility': 0.12},
        'Transportation': {'revenue': 0.10, 'assets': 0.08, 'volatility': 0.20},
        'Consumer Goods': {'revenue': 0.12, 'assets': 0.09, 'volatility': 0.18},
        'Materials': {'revenue': 0.07, 'assets': 0.06, 'volatility': 0.25}
    }
    
    pattern = growth_patterns.get(sector, {'revenue': 0.10, 'assets': 0.08, 'volatility': 0.15})
    
    # Determine base growth rate
    if 'revenue' in metric_name:
        base_growth = pattern['revenue']
    elif 'asset' in metric_name:
        base_growth = pattern['assets']
    else:
        base_growth = 0.08
    
    volatility = pattern['volatility']
    
    # Generate trend series
    series = []
    current_value = base_value * 0.85  # Start lower for growth trend
    
    for i in range(points):
        # Add growth trend
        growth_factor = 1 + (base_growth / 4)  # Quarterly growth
        
        # Add seasonal and random variation
        import random
        random.seed(hash(f"{sector}{metric_name}{i}"))  # Consistent randomness
        variation = 1 + (random.random() - 0.5) * volatility
        
        current_value *= growth_factor * variation
        series.append(round(current_value, 2))
    
    return series

def generate_time_labels(period):
    """Generate time labels for trend charts"""
    periods = {'1Y': 4, '2Y': 8, '5Y': 20}
    points = periods.get(period, 8)
    
    labels = []
    now = datetime.now()
    
    for i in range(points):
        if period == '5Y':
            # Monthly labels for 5 years
            date = datetime(now.year, now.month, 1) - timedelta(days=30 * (points - 1 - i))
            labels.append(date.strftime('%b %Y'))
        else:
            # Quarterly labels
            quarter_back = points - 1 - i
            year_back = quarter_back // 4
            quarter = ((now.month - 1) // 3 - quarter_back % 4) % 4
            year = now.year - year_back
            quarter_names = ['Q1', 'Q2', 'Q3', 'Q4']
            labels.append(f"{quarter_names[quarter]} {year}")
    
    return labels

def calculate_growth_rate(series):
    """Calculate compound annual growth rate from trend series"""
    if len(series) < 2:
        return 0
    
    start_value = series[0]
    end_value = series[-1]
    periods = len(series) - 1
    
    if start_value <= 0:
        return 0
    
    growth_rate = ((end_value / start_value) ** (1 / periods) - 1) * 100
    return round(growth_rate, 2)

def calculate_volatility(series):
    """Calculate volatility of trend series"""
    if len(series) < 2:
        return 0
    
    # Calculate period-to-period changes
    changes = []
    for i in range(1, len(series)):
        if series[i-1] > 0:
            change = (series[i] - series[i-1]) / series[i-1]
            changes.append(change)
    
    if not changes:
        return 0
    
    # Calculate standard deviation
    mean_change = sum(changes) / len(changes)
    variance = sum((x - mean_change) ** 2 for x in changes) / len(changes)
    volatility = (variance ** 0.5) * 100
    
    return round(volatility, 2)

def determine_trend_direction(series):
    """Determine overall trend direction"""
    if len(series) < 2:
        return 'flat'
    
    start_avg = sum(series[:len(series)//3]) / (len(series)//3)
    end_avg = sum(series[-len(series)//3:]) / (len(series)//3)
    
    change_pct = ((end_avg - start_avg) / start_avg) * 100 if start_avg > 0 else 0
    
    if change_pct > 5:
        return 'up'
    elif change_pct < -5:
        return 'down'
    else:
        return 'flat'

def calculate_sector_metrics(companies):
    """Calculate average metrics for a sector"""
    if not companies:
        return {}
    
    total_market_cap = sum([c.market_cap for c in companies if c.market_cap])
    avg_market_cap = total_market_cap / len(companies) if companies else 0
    total_employees = sum([c.employee_count for c in companies if c.employee_count])
    
    return {
        'average_market_cap': avg_market_cap,
        'total_market_cap': total_market_cap,
        'average_employees': total_employees / len(companies) if companies else 0,
        'company_count': len(companies)
    }

def get_sector_top_performers(companies, limit=3):
    """Get top performing companies in a sector"""
    # Sort by market cap for simplicity
    sorted_companies = sorted(companies, key=lambda c: c.market_cap or 0, reverse=True)
    
    return [{
        'id': c.id,
        'name': c.name,
        'ticker_symbol': c.ticker_symbol,
        'market_cap': c.market_cap,
        'market_cap_formatted': format_currency(c.market_cap)
    } for c in sorted_companies[:limit]]

def calculate_sector_trends(companies):
    """Calculate sector-wide trends"""
    return {
        'revenue_growth': 12.5,  # Simulated sector average
        'market_expansion': 8.2,
        'employment_growth': 5.1,
        'innovation_index': 72
    }

def assess_competitive_landscape(companies):
    """Assess competitive dynamics within sector"""
    if len(companies) <= 1:
        return {'competition_level': 'low', 'market_concentration': 'high'}
    
    # Calculate market concentration
    total_market_cap = sum([c.market_cap for c in companies if c.market_cap])
    largest_share = max([c.market_cap for c in companies if c.market_cap]) / total_market_cap if total_market_cap > 0 else 0
    
    if largest_share > 0.5:
        concentration = 'high'
        competition = 'low'
    elif largest_share > 0.3:
        concentration = 'medium'
        competition = 'medium'
    else:
        concentration = 'low'
        competition = 'high'
    
    return {
        'competition_level': competition,
        'market_concentration': concentration,
        'market_leader_share': round(largest_share * 100, 1),
        'number_of_players': len(companies)
    }

def generate_cross_sector_comparison(sector_analysis):
    """Generate cross-sector performance comparison"""
    if not sector_analysis:
        return {}
    
    sectors = list(sector_analysis.keys())
    comparison = {
        'by_market_cap': sorted(sectors, 
            key=lambda s: sector_analysis[s]['total_market_cap'], reverse=True),
        'by_company_count': sorted(sectors, 
            key=lambda s: sector_analysis[s]['company_count'], reverse=True),
        'growth_leaders': sectors,  # Simplified
        'innovation_leaders': sectors  # Simplified
    }
    
    return comparison

def calculate_profitability_metrics(metrics_dict):
    """Calculate profitability indicators"""
    profitability = {}
    
    if 'return_on_assets' in metrics_dict:
        profitability['roa'] = metrics_dict['return_on_assets']
    
    if 'return_on_equity' in metrics_dict:
        profitability['roe'] = metrics_dict['return_on_equity']
    
    # Calculate net profit margin if revenue and income available
    if 'total_revenue' in metrics_dict and 'net_income' in metrics_dict:
        revenue = metrics_dict['total_revenue']
        income = metrics_dict['net_income']
        if revenue > 0:
            profitability['net_profit_margin'] = (income / revenue) * 100
    
    return profitability

def calculate_liquidity_metrics(metrics_dict):
    """Calculate liquidity indicators"""
    # Simplified - would need more detailed balance sheet data
    return {'current_ratio': 1.25, 'quick_ratio': 0.98}

def calculate_efficiency_metrics(metrics_dict):
    """Calculate operational efficiency indicators"""
    efficiency = {}
    
    if 'asset_turnover_ratio' in metrics_dict:
        efficiency['asset_turnover'] = metrics_dict['asset_turnover_ratio']
    
    if 'revenue_per_employee' in metrics_dict:
        efficiency['revenue_per_employee'] = metrics_dict['revenue_per_employee']
    
    return efficiency

def calculate_growth_metrics(metrics_dict, sector):
    """Calculate growth indicators"""
    # Simulated growth based on sector characteristics
    sector_growth = {
        'Banking': 8.5,
        'Telecommunications': 15.2,
        'Transportation': 10.1,
        'Consumer Goods': 12.3,
        'Materials': 7.8
    }
    
    return {
        'revenue_growth': sector_growth.get(sector, 10.0),
        'asset_growth': sector_growth.get(sector, 10.0) * 0.8
    }

def calculate_valuation_metrics(metrics_dict, company):
    """Calculate valuation indicators"""
    valuation = {}
    
    # P/E ratio simulation
    if 'net_income' in metrics_dict and company.market_cap:
        income = metrics_dict['net_income']
        if income > 0:
            valuation['pe_ratio'] = company.market_cap / income
    
    # Price to book simulation
    if 'shareholders_equity' in metrics_dict and company.market_cap:
        equity = metrics_dict['shareholders_equity']
        if equity > 0:
            valuation['pb_ratio'] = company.market_cap / equity
    
    return valuation

def calculate_risk_metrics(metrics_dict, sector):
    """Calculate risk assessment indicators"""
    # Sector-based risk assessment
    sector_risks = {
        'Banking': {'credit_risk': 'medium', 'regulatory_risk': 'high'},
        'Telecommunications': {'technology_risk': 'medium', 'regulatory_risk': 'medium'},
        'Transportation': {'operational_risk': 'high', 'fuel_risk': 'high'},
        'Consumer Goods': {'market_risk': 'medium', 'competition_risk': 'high'},
        'Materials': {'commodity_risk': 'high', 'cyclical_risk': 'high'}
    }
    
    return sector_risks.get(sector, {'overall_risk': 'medium'})

def calculate_financial_health_score(performance_metrics):
    """Calculate overall financial health score"""
    # Weighted scoring based on different metric categories
    weights = {
        'profitability': 0.3,
        'liquidity': 0.2,
        'efficiency': 0.2,
        'growth': 0.2,
        'valuation': 0.1
    }
    
    # Simplified scoring - would be more sophisticated in production
    base_score = 75  # Assume healthy companies
    
    return {
        'overall_score': base_score,
        'rating': 'B+',
        'components': {
            'profitability': 78,
            'liquidity': 72,
            'efficiency': 80,
            'growth': 75,
            'valuation': 70
        }
    }

def compare_to_industry(company, metrics_dict):
    """Compare company performance to industry averages"""
    # Simulated industry benchmarks
    industry_benchmarks = {
        'Banking': {'avg_roa': 2.5, 'avg_roe': 15.2},
        'Telecommunications': {'avg_roa': 4.1, 'avg_revenue_growth': 12.5},
        'Transportation': {'avg_roa': 3.2, 'avg_asset_turnover': 1.8},
        'Consumer Goods': {'avg_roa': 5.5, 'avg_profit_margin': 8.2},
        'Materials': {'avg_roa': 4.8, 'avg_revenue_growth': 7.5}
    }
    
    benchmarks = industry_benchmarks.get(company.sector, {})
    
    comparison = {}
    for metric, benchmark in benchmarks.items():
        metric_key = metric.replace('avg_', '')
        if metric_key in metrics_dict:
            company_value = metrics_dict[metric_key]
            comparison[metric_key] = {
                'company_value': company_value,
                'industry_average': benchmark,
                'vs_industry': 'above' if company_value > benchmark else 'below',
                'difference_pct': ((company_value - benchmark) / benchmark * 100) if benchmark > 0 else 0
            }
    
    return comparison

def generate_performance_recommendations(performance_metrics, sector):
    """Generate actionable performance recommendations"""
    recommendations = [
        {
            'category': 'Growth',
            'recommendation': 'Focus on expanding market share through strategic partnerships',
            'priority': 'high',
            'timeframe': '6-12 months'
        },
        {
            'category': 'Efficiency',
            'recommendation': 'Optimize operational processes to improve asset utilization',
            'priority': 'medium',
            'timeframe': '3-6 months'
        },
        {
            'category': 'Risk Management',
            'recommendation': 'Diversify revenue streams to reduce sector-specific risks',
            'priority': 'medium',
            'timeframe': '12-18 months'
        }
    ]
    
    return recommendations

def format_currency(value):
    """Format currency values consistently"""
    if value >= 1000000000:
        return f"{value / 1000000000:.1f}B ETB"
    elif value >= 1000000:
        return f"{value / 1000000:.1f}M ETB"
    elif value >= 1000:
        return f"{value / 1000:.1f}K ETB"
    else:
        return f"{value:.0f} ETB"