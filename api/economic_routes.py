from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException
from models import EconomicSector, MacroIndicators, EconomicForecast, EconomicDataSource, db
from utils.cache import cache
from utils.limiter import limiter
from utils.errors import APIError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

economic_api = Blueprint('economic_api', __name__)

@economic_api.before_request
def before_request():
    """Request logging for economic API"""
    logger.info({
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'economic_endpoint': True
    })

def serialize_economic_sector(sector):
    """Serialize economic sector data"""
    return {
        "id": sector.id,
        "sector_name": sector.sector_name,
        "sector_code": sector.sector_code,
        "gdp_contribution": sector.gdp_contribution,
        "employment_share": sector.employment_share,
        "growth_rate": sector.growth_rate,
        "investment_share": sector.investment_share,
        "export_contribution": sector.export_contribution,
        "last_updated": sector.last_updated.strftime('%Y-%m-%d') if sector.last_updated else None
    }

@economic_api.route('/sectors')
@limiter.limit("50/minute")
def get_economic_sectors():
    """Get Ethiopian economic sectors with GDP and employment data"""
    try:
        sectors = EconomicSector.query.order_by(
            EconomicSector.gdp_contribution.desc()
        ).all()

        # Calculate totals for validation
        total_gdp = sum(s.gdp_contribution for s in sectors if s.gdp_contribution)
        total_employment = sum(s.employment_share for s in sectors if s.employment_share)

        return jsonify({
            "sectors": [serialize_economic_sector(sector) for sector in sectors],
            "summary": {
                "total_sectors": len(sectors),
                "total_gdp_coverage": round(total_gdp, 1),
                "total_employment_coverage": round(total_employment, 1)
            }
        })

    except Exception as e:
        logger.error(f"Error in get_economic_sectors: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@economic_api.route('/sectors/<int:sector_id>')
@limiter.limit("100/minute")

def get_sector_by_id(sector_id):
    """Get detailed information for a specific economic sector"""
    try:
        sector = EconomicSector.query.get_or_404(sector_id)
        return jsonify(serialize_economic_sector(sector))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_sector_by_id: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@economic_api.route('/indicators/enhanced')
@limiter.limit("50/minute")

def get_enhanced_macro_indicators():
    """Get enhanced macroeconomic indicators with additional context"""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        indicators = request.args.get('indicators')
        frequency = request.args.get('frequency', 'all')
        
        query = MacroIndicators.query
        
        if date_from:
            query = query.filter(MacroIndicators.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(MacroIndicators.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            
        # Order by date descending
        macro_data = query.order_by(MacroIndicators.date.desc()).all()
        
        # Filter indicators if specified
        if indicators:
            selected_indicators = indicators.split(',')
        else:
            selected_indicators = None

        result_data = []
        for record in macro_data:
            row = {
                "date": record.date.strftime('%Y-%m-%d'),
                "economic_growth": {
                    "gdp_growth": record.gdp_growth,
                    "gdp_per_capita": record.gdp_per_capita,
                    "industrial_production": record.industrial_production,
                    "agricultural_production": record.agricultural_production
                },
                "inflation_interest": {
                    "inflation_rate": record.inflation_rate,
                    "food_inflation": record.food_inflation,
                    "interest_rate": record.interest_rate
                },
                "trade_external": {
                    "exports": record.exports,
                    "imports": record.imports,
                    "trade_balance": record.trade_balance,
                    "current_account_balance": record.current_account_balance,
                    "fdi_inflow": record.fdi_inflow,
                    "remittances": record.remittances
                },
                "exchange_rates": {
                    "etb_usd": record.etb_usd,
                    "etb_eur": record.etb_eur,
                    "etb_gbp": record.etb_gbp,
                    "etb_jpy": record.etb_jpy,
                    "etb_cny": record.etb_cny,
                    "fx_reserves": record.fx_reserves
                },
                "government_finance": {
                    "govt_revenue": record.govt_revenue,
                    "govt_expenditure": record.govt_expenditure,
                    "budget_deficit": record.budget_deficit,
                    "govt_debt": record.govt_debt,
                    "tax_revenue": record.tax_revenue
                },
                "banking_monetary": {
                    "total_deposits": record.total_deposits,
                    "total_loans": record.total_loans,
                    "npl_ratio": record.npl_ratio,
                    "loan_to_deposit": record.loan_to_deposit,
                    "money_supply_m1": record.money_supply_m1,
                    "money_supply_m2": record.money_supply_m2,
                    "private_sector_credit": record.private_sector_credit
                },
                "commodity_prices": {
                    "coffee_price": record.coffee_price,
                    "gold_price": record.gold_price,
                    "oil_price": record.oil_price,
                    "wheat_price": record.wheat_price
                }
            }
            
            # Filter specific indicators if requested
            if selected_indicators:
                filtered_row = {"date": row["date"]}
                for category, indicators_dict in row.items():
                    if category != "date" and isinstance(indicators_dict, dict):
                        filtered_indicators = {
                            k: v for k, v in indicators_dict.items() 
                            if k in selected_indicators
                        }
                        if filtered_indicators:
                            filtered_row[category] = filtered_indicators
                row = filtered_row
                
            result_data.append(row)

        return jsonify({
            "data": result_data,
            "metadata": {
                "total_records": len(result_data),
                "date_range": {
                    "from": date_from,
                    "to": date_to
                },
                "indicators_requested": selected_indicators,
                "frequency": frequency
            }
        })

    except Exception as e:
        logger.error(f"Error in get_enhanced_macro_indicators: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@economic_api.route('/analysis/correlation')
@limiter.limit("30/minute")

def get_economic_correlation_analysis():
    """Get correlation analysis between economic indicators"""
    try:
        indicator1 = request.args.get('indicator1', 'gdp_growth')
        indicator2 = request.args.get('indicator2', 'inflation_rate')
        period_months = request.args.get('period_months', 12, type=int)
        
        # Get recent data for correlation analysis
        recent_data = MacroIndicators.query.order_by(
            MacroIndicators.date.desc()
        ).limit(period_months).all()
        
        if len(recent_data) < 2:
            return jsonify({"error": "Insufficient data for correlation analysis"}), 400
            
        # Extract values for correlation calculation
        values1 = []
        values2 = []
        dates = []
        
        for record in recent_data:
            val1 = getattr(record, indicator1, None)
            val2 = getattr(record, indicator2, None)
            
            if val1 is not None and val2 is not None:
                values1.append(val1)
                values2.append(val2)
                dates.append(record.date.strftime('%Y-%m-%d'))
        
        # Simple correlation calculation
        if len(values1) >= 2:
            import statistics
            mean1 = statistics.mean(values1)
            mean2 = statistics.mean(values2)
            
            numerator = sum((x - mean1) * (y - mean2) for x, y in zip(values1, values2))
            denominator = (sum((x - mean1) ** 2 for x in values1) * sum((y - mean2) ** 2 for y in values2)) ** 0.5
            
            correlation = numerator / denominator if denominator != 0 else 0
        else:
            correlation = 0
            
        return jsonify({
            "correlation_analysis": {
                "indicator1": indicator1,
                "indicator2": indicator2,
                "correlation_coefficient": round(correlation, 4),
                "period_analyzed": f"{len(values1)} months",
                "data_points": len(values1),
                "interpretation": {
                    "strength": "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.4 else "Weak",
                    "direction": "Positive" if correlation > 0 else "Negative" if correlation < 0 else "No correlation"
                }
            },
            "data_series": [
                {
                    "date": date,
                    indicator1: val1,
                    indicator2: val2
                } for date, val1, val2 in zip(dates, values1, values2)
            ]
        })

    except Exception as e:
        logger.error(f"Error in get_economic_correlation_analysis: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@economic_api.route('/trends/sector-growth')
@limiter.limit("30/minute")

def get_sector_growth_trends():
    """Get economic sector growth trends and projections"""
    try:
        sectors = EconomicSector.query.order_by(
            EconomicSector.growth_rate.desc()
        ).all()
        
        # Get related forecasts
        forecasts = EconomicForecast.query.filter(
            EconomicForecast.indicator_name.ilike('%growth%')
        ).order_by(EconomicForecast.created_date.desc()).limit(10).all()
        
        return jsonify({
            "sector_growth_ranking": [
                {
                    "rank": idx + 1,
                    "sector_name": sector.sector_name,
                    "growth_rate": sector.growth_rate,
                    "gdp_contribution": sector.gdp_contribution,
                    "employment_share": sector.employment_share,
                    "growth_category": "High Growth" if sector.growth_rate and sector.growth_rate > 10 
                                    else "Moderate Growth" if sector.growth_rate and sector.growth_rate > 5 
                                    else "Slow Growth"
                } for idx, sector in enumerate(sectors) if sector.growth_rate
            ],
            "related_forecasts": [
                {
                    "indicator": forecast.indicator_name,
                    "forecast_value": forecast.forecast_value,
                    "forecast_period": forecast.forecast_period,
                    "source": forecast.source_organization
                } for forecast in forecasts
            ]
        })

    except Exception as e:
        logger.error(f"Error in get_sector_growth_trends: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@economic_api.route('/analysis/economic-health-index')
@limiter.limit("30/minute")

def get_economic_health_index():
    """Calculate composite economic health index for Ethiopia"""
    try:
        # Get latest macro indicators
        latest = MacroIndicators.query.order_by(
            MacroIndicators.date.desc()
        ).first()
        
        if not latest:
            return jsonify({"error": "No economic data available"}), 404
            
        # Calculate composite health index (simplified methodology)
        indicators = {
            "gdp_growth": latest.gdp_growth or 0,
            "inflation_rate": latest.inflation_rate or 0,
            "unemployment_rate": latest.unemployment_rate or 0,
            "current_account_balance": latest.current_account_balance or 0,
            "govt_debt": latest.govt_debt or 0,
            "fx_reserves": latest.fx_reserves or 0
        }
        
        # Scoring methodology (simplified)
        scores = {}
        scores['growth_score'] = min(100, max(0, indicators['gdp_growth'] * 10))  # 10% growth = 100 points
        scores['inflation_score'] = max(0, 100 - indicators['inflation_rate'] * 2)  # Lower inflation = higher score
        scores['employment_score'] = max(0, 100 - indicators['unemployment_rate'] * 5)  # Lower unemployment = higher score
        
        # Overall health index (average of scores)
        overall_score = sum(scores.values()) / len(scores)
        
        health_rating = "Excellent" if overall_score >= 80 else "Good" if overall_score >= 60 else "Fair" if overall_score >= 40 else "Poor"
        
        return jsonify({
            "economic_health_index": {
                "overall_score": round(overall_score, 1),
                "rating": health_rating,
                "as_of_date": latest.date.strftime('%Y-%m-%d'),
                "component_scores": {
                    "economic_growth": round(scores['growth_score'], 1),
                    "price_stability": round(scores['inflation_score'], 1),
                    "employment": round(scores['employment_score'], 1)
                },
                "key_indicators": indicators,
                "interpretation": {
                    "strengths": [k for k, v in scores.items() if v >= 70],
                    "concerns": [k for k, v in scores.items() if v < 50]
                }
            }
        })

    except Exception as e:
        logger.error(f"Error in get_economic_health_index: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500