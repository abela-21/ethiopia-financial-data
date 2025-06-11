#!/usr/bin/env python3
"""
Test script to verify admin data management functionality
"""

from app import create_app
from models import User, Company, Financial, Bank, ResearchDocument, MacroIndicators
import logging

def test_data_management():
    """Test data management functionality"""
    app = create_app()
    
    with app.app_context():
        print("📊 ADMIN DATA MANAGEMENT - LIVE DATA STATISTICS:")
        print("=" * 60)
        
        # Get actual data counts
        companies_count = Company.query.count()
        financial_count = Financial.query.count()
        banks_count = Bank.query.count()
        research_count = ResearchDocument.query.count()
        indicators_count = MacroIndicators.query.count()
        users_count = User.query.count()
        
        print(f"   Companies: {companies_count}")
        print(f"   Financial Records: {financial_count}")
        print(f"   Banks: {banks_count}")
        print(f"   Research Documents: {research_count}")
        print(f"   Economic Indicators: {indicators_count}")
        print(f"   Users: {users_count}")
        print()
        
        # Sample recent data
        print("🏢 RECENT COMPANIES (Top 5):")
        recent_companies = Company.query.order_by(Company.id.desc()).limit(5).all()
        for i, company in enumerate(recent_companies, 1):
            print(f"   {i}. {company.name} ({company.ticker}) - {company.industry}")
        print()
        
        print("📈 RECENT FINANCIAL DATA (Top 5):")
        recent_financial = Financial.query.order_by(Financial.year.desc()).limit(5).all()
        for i, financial in enumerate(recent_financial, 1):
            company_name = financial.company.name if financial.company else 'Unknown Company'
            revenue_str = f"${financial.revenue:,.0f}" if financial.revenue else 'N/A'
            print(f"   {i}. {company_name} ({financial.year}) - Revenue: {revenue_str}")
        print()
        
        print("📚 RECENT RESEARCH (Top 5):")
        recent_research = ResearchDocument.query.order_by(ResearchDocument.publication_date.desc()).limit(5).all()
        for i, research in enumerate(recent_research, 1):
            date_str = research.publication_date.strftime('%B %Y') if research.publication_date else 'N/A'
            title_short = research.title[:50] + '...' if len(research.title) > 50 else research.title
            print(f"   {i}. {title_short} ({date_str})")

if __name__ == '__main__':
    test_data_management()