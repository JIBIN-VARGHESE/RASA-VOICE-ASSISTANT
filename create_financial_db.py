import sqlite3
import json

# Load the JSON data
json_data = """{
  "results": {
    "2023": {
      "q1": {
        "netProfit": 511,
        "ebita": 1251,
        "availableCash": 595,
        "NetDebt": 19755,
        "revenue": {
          "LargeEnterprise": 911,
          "MidMarketEnterprise": 523,
          "PublicSector": 432,
          "Wholesale": 823,
          "InternationalAndOther": 279,
          "BusinessSegmentRevenue": 2968,
          "MassMarketsSegmentRevenue": 770
        }
      },
      "q2": {
        "netProfit": -8736,
        "ebita": 1229,
        "availableCash": -100,
        "NetDebt": 19955,
        "revenue": {
          "LargeEnterprise": 899,
          "MidMarketEnterprise": 514,
          "PublicSector": 415,
          "Wholesale": 803,
          "InternationalAndOther": 277,
          "BusinessSegmentRevenue": 2908,
          "MassMarketsSegmentRevenue": 753
        }
      },
      "q3": {
        "netProfit": -78,
        "ebita": 1049,
        "availableCash": 881,
        "NetDebt": 19759,
        "revenue": {
          "LargeEnterprise": 914,
          "MidMarketEnterprise": 506,
          "PublicSector": 445,
          "Wholesale": 776,
          "InternationalAndOther": 264,
          "BusinessSegmentRevenue": 2905,
          "MassMarketsSegmentRevenue": 736
        }
      },
      "q4": {
        "netProfit": -1995,
        "ebita": 1099,
        "availableCash": 784,
        "NetDebt": 19852,
        "revenue": {
          "LargeEnterprise": 894,
          "MidMarketEnterprise": 501,
          "PublicSector": 497,
          "Wholesale": 776,
          "InternationalAndOther": 264,
          "BusinessSegmentRevenue": 2905,
          "MassMarketsSegmentRevenue": 736
        }
      }
    },
    "2024": {
      "q1": {
        "netProfit": 57,
        "ebita": 977,
        "availableCash": 1102,
        "NetDebt": 19831,
        "revenue": {
          "LargeEnterprise": 858,
          "MidMarketEnterprise": 486,
          "PublicSector": 420,
          "Wholesale": 730,
          "InternationalAndOther": 97,
          "BusinessSegmentRevenue": 2591,
          "MassMarketsSegmentRevenue": 699
        }
      }
    }
  }
}"""

data = json.loads(json_data)

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("financial_data.db")
cursor = conn.cursor()

# Create the tables
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS financial_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        quarter TEXT NOT NULL,
        netProfit REAL,
        ebita REAL,
        availableCash REAL,
        netDebt REAL
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS revenue_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        financial_result_id INTEGER,
        largeEnterprise REAL,
        midMarketEnterprise REAL,
        publicSector REAL,
        wholesale REAL,
        internationalAndOther REAL,
        businessSegmentRevenue REAL,
        massMarketsSegmentRevenue REAL,
        FOREIGN KEY (financial_result_id) REFERENCES financial_results(id)
    )
"""
)

# Insert data into the tables
for year, quarters in data["results"].items():
    for quarter, details in quarters.items():
        # Insert into financial_results
        cursor.execute(
            """
            INSERT INTO financial_results (year, quarter, netProfit, ebita, availableCash, netDebt)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                year,
                quarter,
                details["netProfit"],
                details["ebita"],
                details["availableCash"],
                details["NetDebt"],
            ),
        )

        # Get the last inserted id
        financial_result_id = cursor.lastrowid

        # Insert into revenue_details
        revenue = details["revenue"]
        cursor.execute(
            """
            INSERT INTO revenue_details (financial_result_id, largeEnterprise, midMarketEnterprise, publicSector, wholesale, internationalAndOther, businessSegmentRevenue, massMarketsSegmentRevenue)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                financial_result_id,
                revenue["LargeEnterprise"],
                revenue["MidMarketEnterprise"],
                revenue["PublicSector"],
                revenue["Wholesale"],
                revenue["InternationalAndOther"],
                revenue["BusinessSegmentRevenue"],
                revenue["MassMarketsSegmentRevenue"],
            ),
        )

# Commit the transaction
conn.commit()

# Close the connection
conn.close()
