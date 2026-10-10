"""
Refresh macro indicators from external (World Bank) data without ever
deleting existing records.

Steps:
1. Optionally fetch fresh values and upsert them into external_economic_data.
2. Read the latest cached value for each tracked indicator.
3. Merge those values into today's MacroIndicators row (created if missing),
   touching only the fields we have values for.

Everything happens in one transaction: on any error nothing is written.
"""
import logging
from datetime import date, datetime

from app import db
from models import ExternalEconomicData, MacroIndicators

logger = logging.getLogger(__name__)

# MacroIndicators field -> World Bank indicator code
INDICATOR_CODES = {
    'gdp_growth': 'NY.GDP.MKTP.KD.ZG',
    'gdp_per_capita': 'NY.GDP.PCAP.CD',
    'inflation_rate': 'FP.CPI.TOTL.ZG',
    'unemployment_rate': 'SL.UEM.TOTL.ZS',
    'exports': 'NE.EXP.GNFS.CD',
    'imports': 'NE.IMP.GNFS.CD',
    'fdi_inflow': 'BX.KLT.DINV.CD.WD',
    'etb_usd': 'PA.NUS.FCRF',
}


def store_external_records(records):
    """Upsert fetched records into external_economic_data. Returns (new, updated)."""
    new = updated = 0
    now = datetime.utcnow()
    for record in records:
        record_date = record['date']
        if isinstance(record_date, str):
            record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
        existing = ExternalEconomicData.query.filter_by(
            indicator_code=record['indicator_code'], date=record_date, source=record.get('source')
        ).first()
        if existing:
            existing.indicator_name = record.get('indicator_name')
            existing.value = record.get('value')
            existing.unit = record.get('unit', '')
            existing.last_updated = now
            updated += 1
        else:
            db.session.add(ExternalEconomicData(
                indicator_code=record['indicator_code'],
                indicator_name=record.get('indicator_name'),
                date=record_date,
                value=record.get('value'),
                country=record.get('country'),
                source=record.get('source'),
                unit=record.get('unit', ''),
                created_at=now,
                last_updated=now,
            ))
            new += 1
    db.session.flush()
    return new, updated


def fetch_world_bank_records(integrator=None):
    """Fetch the tracked indicators from the World Bank. Network errors yield []."""
    if integrator is None:
        from Data.enhanced_external_apis import EnhancedExternalDataIntegrator
        integrator = EnhancedExternalDataIntegrator()
    try:
        return integrator.get_world_bank_ethiopia_data(only=set(INDICATOR_CODES.values()))
    except Exception as e:
        logger.warning(f"World Bank fetch failed: {e}")
        return []


def latest_external_values():
    """Latest cached value for each tracked indicator, keyed by MacroIndicators field."""
    values = {}
    for field, code in INDICATOR_CODES.items():
        row = (ExternalEconomicData.query
               .filter(ExternalEconomicData.indicator_code == code,
                       ExternalEconomicData.value.isnot(None))
               .order_by(ExternalEconomicData.date.desc())
               .first())
        if row is not None:
            values[field] = float(row.value)
    return values


def refresh_macro_indicators(fetch=True, integrator=None, today=None):
    """
    Refresh today's macro indicator row from external data.

    Returns a dict with 'success', 'message' and counts. Existing indicator
    rows are never deleted; if no external data is available nothing changes.
    """
    today = today or date.today()
    try:
        fetched = fetch_world_bank_records(integrator) if fetch else []
        new, updated = store_external_records(fetched) if fetched else (0, 0)

        values = latest_external_values()
        if not values:
            db.session.rollback()
            return {
                'success': False,
                'message': 'No external data is available (fetch failed and nothing is cached). '
                           'Existing indicators were left unchanged.',
                'fetched': 0,
            }

        if 'exports' in values and 'imports' in values:
            values['trade_balance'] = values['exports'] - values['imports']

        indicator = MacroIndicators.query.filter_by(date=today).first()
        created = indicator is None
        if created:
            indicator = MacroIndicators(date=today)
            db.session.add(indicator)
        for field, value in values.items():
            setattr(indicator, field, value)
        indicator.updated_at = datetime.utcnow()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    source = (f'fetched {len(fetched)} fresh records ({new} new, {updated} updated)'
              if fetched else 'using cached external data (fresh fetch unavailable)')
    return {
        'success': True,
        'message': f"{'Created' if created else 'Updated'} indicators for {today.isoformat()}, {source}.",
        'fetched': len(fetched),
        'fields_updated': sorted(values),
        'used_cache': not fetched,
    }
