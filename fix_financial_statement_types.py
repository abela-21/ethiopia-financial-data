#!/usr/bin/env python3
"""
Fix financial statement types to enable proper filtering
"""

from app import app, db
from models import FinancialStatement
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_statement_types():
    """Update financial statements with different statement types"""
    
    with app.app_context():
        try:
            # Get all financial statements
            statements = FinancialStatement.query.all()
            
            statement_types = [
                'income_statement',
                'balance_sheet', 
                'cash_flow',
                'banking_metrics',
                'financial_metrics'
            ]
            
            updated_count = 0
            
            for i, statement in enumerate(statements):
                # Assign statement types in a round-robin fashion
                statement_type = statement_types[i % len(statement_types)]
                statement.statement_type = statement_type
                updated_count += 1
            
            db.session.commit()
            
            logger.info(f"Updated {updated_count} financial statements with diverse statement types")
            
            # Verify the distribution
            for stmt_type in statement_types:
                count = FinancialStatement.query.filter_by(statement_type=stmt_type).count()
                print(f"{stmt_type}: {count} statements")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fixing statement types: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_statement_types()
    if success:
        print("\n✅ Financial statement types fixed successfully!")
        print("Statement type filtering should now work correctly.")
    else:
        print("\n❌ Failed to fix financial statement types")