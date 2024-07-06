import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("financial_data.db")
cursor = conn.cursor()

# Check if the financial_results table exists
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='financial_results'"
)
table_exists = cursor.fetchone()
print("financial_results table exists:", bool(table_exists))

# Check if the revenue_details table exists
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='revenue_details'"
)
table_exists = cursor.fetchone()
print("revenue_details table exists:", bool(table_exists))

# Fetch some rows from the financial_results table
cursor.execute("SELECT * FROM financial_results LIMIT 5")
financial_results = cursor.fetchall()
print("financial_results data:", financial_results)

# Fetch some rows from the revenue_details table
cursor.execute("SELECT * FROM revenue_details LIMIT 5")
revenue_details = cursor.fetchall()
print("revenue_details data:", revenue_details)

# Close the connection
conn.close()
