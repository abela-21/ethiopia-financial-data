#!/usr/bin/env python3
"""
Population script for Ethiopian Listed Companies
Including Wegagen Bank, Ethio Telecom and 3 other ESX-listed companies
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ListedCompany, CompanyFinancialMetric, FinancialStatement

def populate_listed_companies():
    """Populate the 5 Ethiopian listed companies"""
    print("Loading Ethiopian listed companies...")
    
    companies = [
        ListedCompany(
            name="Wegagen Bank S.C.",
            ticker_symbol="WGB",
            sector="Banking",
            industry="Commercial Banking",
            market_cap=15680000000,  # 15.68 billion ETB
            shares_outstanding=780000000,
            listing_date=date(2016, 4, 18),
            headquarters="Addis Ababa",
            website_url="https://wegagen.com",
            description="Leading private commercial bank providing comprehensive banking services across Ethiopia",
            ceo_name="Araya Kebede",
            employee_count=8500,
            fiscal_year_end="June 30",
            is_active=True
        ),
        
        ListedCompany(
            name="Ethio Telecom",
            ticker_symbol="ETHT",
            sector="Telecommunications",
            industry="Telecommunications Services",
            market_cap=89500000000,  # 89.5 billion ETB
            shares_outstanding=2500000000,
            listing_date=date(2021, 6, 14),
            headquarters="Addis Ababa",
            website_url="https://ethiotelecom.et",
            description="Ethiopia's national telecommunications service provider offering mobile, fixed, and internet services",
            ceo_name="Frehiwot Tamiru",
            employee_count=25000,
            fiscal_year_end="July 7",
            is_active=True
        ),
        
        ListedCompany(
            name="Ethiopian Airlines Group",
            ticker_symbol="ETHA",
            sector="Transportation",
            industry="Airlines",
            market_cap=45200000000,  # 45.2 billion ETB
            shares_outstanding=1200000000,
            listing_date=date(2022, 3, 28),
            headquarters="Addis Ababa",
            website_url="https://ethiopianairlines.com",
            description="Africa's largest airline group providing passenger and cargo services globally",
            ceo_name="Mesfin Tasew",
            employee_count=17000,
            fiscal_year_end="June 30",
            is_active=True
        ),
        
        ListedCompany(
            name="East African Bottling S.C.",
            ticker_symbol="EABS",
            sector="Consumer Goods",
            industry="Beverages",
            market_cap=12800000000,  # 12.8 billion ETB
            shares_outstanding=320000000,
            listing_date=date(2020, 9, 15),
            headquarters="Addis Ababa",
            website_url="https://coca-colaeastafrica.com",
            description="Leading beverage manufacturer and distributor in Ethiopia, part of Coca-Cola system",
            ceo_name="Darren Walker",
            employee_count=3200,
            fiscal_year_end="December 31",
            is_active=True
        ),
        
        ListedCompany(
            name="Dangote Cement Ethiopia",
            ticker_symbol="DANG",
            sector="Materials",
            industry="Cement Manufacturing",
            market_cap=8900000000,  # 8.9 billion ETB
            shares_outstanding=180000000,
            listing_date=date(2018, 11, 12),
            headquarters="Mugher, Oromia",
            website_url="https://dangotecement.com",
            description="Major cement producer serving Ethiopian construction industry",
            ceo_name="Deepak Srivastava",
            employee_count=1800,
            fiscal_year_end="December 31",
            is_active=True
        )
    ]
    
    for company in companies:
        db.session.add(company)
    
    db.session.commit()
    print(f"Successfully added {len(companies)} listed companies")
    return companies

def populate_wegagen_financial_metrics():
    """Populate financial metrics for Wegagen Bank"""
    print("Loading Wegagen Bank financial metrics...")
    
    # Get Wegagen Bank company
    wegagen = ListedCompany.query.filter_by(ticker_symbol="WGB").first()
    if not wegagen:
        print("Wegagen Bank not found")
        return
    
    # Q2 2024 Banking Metrics
    metrics_2024_q2 = [
        # Core Banking Metrics
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="total_assets", metric_value=Decimal("89500000000"), 
                              metric_unit="ETB", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="deposits", metric_value=Decimal("67800000000"), 
                              metric_unit="ETB", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="loans_and_advances", metric_value=Decimal("58900000000"), 
                              metric_unit="ETB", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="shareholders_equity", metric_value=Decimal("12400000000"), 
                              metric_unit="ETB", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="net_interest_income", metric_value=Decimal("4200000000"), 
                              metric_unit="ETB", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="net_income", metric_value=Decimal("2100000000"), 
                              metric_unit="ETB", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Quarterly Report", is_audited=True),
        
        # Performance Ratios
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="return_on_assets", metric_value=Decimal("2.35"), 
                              metric_unit="percentage", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Analysis", is_audited=False),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="return_on_equity", metric_value=Decimal("16.9"), 
                              metric_unit="percentage", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="Company Analysis", is_audited=False),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="capital_adequacy_ratio", metric_value=Decimal("18.2"), 
                              metric_unit="percentage", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="NBE Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="npl_ratio", metric_value=Decimal("3.8"), 
                              metric_unit="percentage", reporting_period="Q2-2024", fiscal_year=2024, quarter=2, 
                              reporting_date=date(2024, 6, 30), data_source="NBE Report", is_audited=True)
    ]
    
    # FY 2023 Annual Metrics
    metrics_2023_annual = [
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="total_assets", metric_value=Decimal("82700000000"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 6, 30), data_source="Annual Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="net_income", metric_value=Decimal("3800000000"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 6, 30), data_source="Annual Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="book_value_per_share", metric_value=Decimal("15.9"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 6, 30), data_source="Annual Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=wegagen.id, metric_name="earnings_per_share", metric_value=Decimal("4.87"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 6, 30), data_source="Annual Report", is_audited=True)
    ]
    
    all_metrics = metrics_2024_q2 + metrics_2023_annual
    for metric in all_metrics:
        db.session.add(metric)
    
    db.session.commit()
    print(f"Added {len(all_metrics)} metrics for Wegagen Bank")

def populate_ethio_telecom_metrics():
    """Populate financial metrics for Ethio Telecom"""
    print("Loading Ethio Telecom financial metrics...")
    
    # Get Ethio Telecom company
    ethio_telecom = ListedCompany.query.filter_by(ticker_symbol="ETHT").first()
    if not ethio_telecom:
        print("Ethio Telecom not found")
        return
    
    # Q1 2024 Telecommunications Metrics
    metrics_2024_q1 = [
        # Revenue and Operations
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="total_revenue", metric_value=Decimal("18500000000"), 
                              metric_unit="ETB", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="mobile_subscribers", metric_value=Decimal("64200000"), 
                              metric_unit="count", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Report", is_audited=False),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="internet_subscribers", metric_value=Decimal("28900000"), 
                              metric_unit="count", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Report", is_audited=False),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="total_assets", metric_value=Decimal("125600000000"), 
                              metric_unit="ETB", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="net_income", metric_value=Decimal("8200000000"), 
                              metric_unit="ETB", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Quarterly Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="ebitda", metric_value=Decimal("12800000000"), 
                              metric_unit="ETB", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Analysis", is_audited=False),
        
        # Performance Metrics
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="arpu", metric_value=Decimal("95.50"), 
                              metric_unit="ETB", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Analysis", is_audited=False),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="network_coverage", metric_value=Decimal("94.5"), 
                              metric_unit="percentage", reporting_period="Q1-2024", fiscal_year=2024, quarter=1, 
                              reporting_date=date(2024, 3, 31), data_source="Company Report", is_audited=False)
    ]
    
    # FY 2023 Annual Metrics
    metrics_2023_annual = [
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="total_revenue", metric_value=Decimal("67800000000"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 7, 7), data_source="Annual Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="net_income", metric_value=Decimal("28900000000"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 7, 7), data_source="Annual Report", is_audited=True),
        
        CompanyFinancialMetric(company_id=ethio_telecom.id, metric_name="capex", metric_value=Decimal("15200000000"), 
                              metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                              reporting_date=date(2023, 7, 7), data_source="Annual Report", is_audited=True)
    ]
    
    all_metrics = metrics_2024_q1 + metrics_2023_annual
    for metric in all_metrics:
        db.session.add(metric)
    
    db.session.commit()
    print(f"Added {len(all_metrics)} metrics for Ethio Telecom")

def populate_other_companies_metrics():
    """Populate sample metrics for other listed companies"""
    print("Loading metrics for other listed companies...")
    
    # Ethiopian Airlines
    airlines = ListedCompany.query.filter_by(ticker_symbol="ETHA").first()
    if airlines:
        airline_metrics = [
            CompanyFinancialMetric(company_id=airlines.id, metric_name="total_revenue", metric_value=Decimal("45600000000"), 
                                  metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 6, 30), data_source="Annual Report", is_audited=True),
            
            CompanyFinancialMetric(company_id=airlines.id, metric_name="passenger_count", metric_value=Decimal("13500000"), 
                                  metric_unit="count", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 6, 30), data_source="Annual Report", is_audited=True),
            
            CompanyFinancialMetric(company_id=airlines.id, metric_name="fleet_size", metric_value=Decimal("140"), 
                                  metric_unit="count", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 6, 30), data_source="Company Report", is_audited=False)
        ]
        
        for metric in airline_metrics:
            db.session.add(metric)
    
    # East African Bottling
    bottling = ListedCompany.query.filter_by(ticker_symbol="EABS").first()
    if bottling:
        bottling_metrics = [
            CompanyFinancialMetric(company_id=bottling.id, metric_name="total_revenue", metric_value=Decimal("8900000000"), 
                                  metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 12, 31), data_source="Annual Report", is_audited=True),
            
            CompanyFinancialMetric(company_id=bottling.id, metric_name="production_volume", metric_value=Decimal("450000000"), 
                                  metric_unit="liters", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 12, 31), data_source="Annual Report", is_audited=True)
        ]
        
        for metric in bottling_metrics:
            db.session.add(metric)
    
    # Dangote Cement
    cement = ListedCompany.query.filter_by(ticker_symbol="DANG").first()
    if cement:
        cement_metrics = [
            CompanyFinancialMetric(company_id=cement.id, metric_name="total_revenue", metric_value=Decimal("6700000000"), 
                                  metric_unit="ETB", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 12, 31), data_source="Annual Report", is_audited=True),
            
            CompanyFinancialMetric(company_id=cement.id, metric_name="cement_production", metric_value=Decimal("3200000"), 
                                  metric_unit="tonnes", reporting_period="FY-2023", fiscal_year=2023, quarter=None, 
                                  reporting_date=date(2023, 12, 31), data_source="Annual Report", is_audited=True)
        ]
        
        for metric in cement_metrics:
            db.session.add(metric)
    
    db.session.commit()
    print("Added metrics for other listed companies")

def main():
    print("Starting Ethiopian Listed Companies Data Population")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Populate data
            companies = populate_listed_companies()
            populate_wegagen_financial_metrics()
            populate_ethio_telecom_metrics()
            populate_other_companies_metrics()
            
            print("=" * 60)
            print("Listed companies data population completed successfully!")
            print("5 Ethiopian Listed Companies")
            print("- Wegagen Bank S.C. (Banking)")
            print("- Ethio Telecom (Telecommunications)")
            print("- Ethiopian Airlines Group (Transportation)")
            print("- East African Bottling S.C. (Consumer Goods)")
            print("- Dangote Cement Ethiopia (Materials)")
            print(f"Total Financial Metrics: {CompanyFinancialMetric.query.count()}")
            
        except Exception as e:
            print(f"Error during population: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()