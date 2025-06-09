import pandas as pd
import numpy as np
from datetime import datetime, timedelta

companies = [
    {'id': 1, 'base_price': 50.0, 'volume_range': (4000, 6000)},
    {'id': 2, 'base_price': 75.0, 'volume_range': (7000, 9000)},
    {'id': 3, 'base_price': 40.0, 'volume_range': (3000, 5000)},
    {'id': 4, 'base_price': 60.0, 'volume_range': (5000, 7000)},
    {'id': 5, 'base_price': 30.0, 'volume_range': (2000, 4000)},
]

start_date = datetime(2025, 4, 1)
dates = [start_date + timedelta(days=i) for i in range(10)]

stock_data = []
id_counter = 1

for company in companies:
    company_id = company['id']
    price = company['base_price']
    
    for date in dates:
        fluctuation = np.random.uniform(-0.05, 0.05)
        close = price * (1 + fluctuation)
        open_price = price
        high = max(open_price, close) * np.random.uniform(1.0, 1.02)
        low = min(open_price, close) * np.random.uniform(0.98, 1.0)
        volume = np.random.randint(*company['volume_range'])
        
        stock_data.append({
            'id': id_counter,
            'company_id': company_id,
            'date': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
        
        price = close
        id_counter += 1

stocks_df = pd.DataFrame(stock_data)
stocks_df.to_csv('stocks.csv', index=False)
print("stocks.csv generated with 50 rows.")