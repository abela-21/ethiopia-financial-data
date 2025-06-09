import sqlite3
conn = sqlite3.connect('market.db')
conn.close()
print("market.db created.")
