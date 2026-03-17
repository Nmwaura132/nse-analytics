import sqlite3
import os
import sys

# Setup Django environment
sys.path.append('/app/nse_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.models import Trade

SQLITE_DB_PATH = '/app/portfolio.db'

def migrate_data():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite DB not found at {SQLITE_DB_PATH}. Skipping migration.")
        return

    print(f"Connecting to {SQLITE_DB_PATH}...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id, ticker, quantity, avg_cost FROM portfolio")
        rows = cursor.fetchall()
        
        Trade.objects.all().delete() # Clear existing data in MySQL just in case
        
        migrated_count = 0
        for row in rows:
            user_id, ticker, qty, avg_cost = row
            Trade.objects.create(
                user_id=str(user_id),
                ticker=ticker,
                qty=float(qty),
                avg_cost=float(avg_cost)
            )
            migrated_count += 1
            
        print(f"Successfully migrated {migrated_count} trades from SQLite to MySQL.")
        
    except sqlite3.OperationalError as e:
        print(f"OperationalError (maybe table doesn't exist?): {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_data()
