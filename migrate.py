# migrate.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, inspect
import os

# Import your models
from app import app, db, User, AirdropClaim, Referral, Achievement, Notification, \
                IPRestriction, PresaleContribution, WithdrawalAttempt, \
                PresaleTransaction, Task, UserTask, TaskVerification, DailyStreak

def migrate_to_postgresql():
    """Migrate from SQLite to PostgreSQL"""
    print("🚀 Starting database migration...")
    
    # Source (SQLite) and target (PostgreSQL) databases
    sqlite_url = 'sqlite:///airdrop.db'
    postgres_url = os.getenv('DATABASE_URL')
    
    if not postgres_url:
        print("❌ DATABASE_URL not set. Please set your PostgreSQL connection string.")
        return
    
    # Convert postgres:// to postgresql://
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
    
    # Create engines
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)
    
    # Check if SQLite database exists
    if not os.path.exists('airdrop.db'):
        print("❌ SQLite database not found. Starting fresh on PostgreSQL.")
        return
    
    with app.app_context():
        # Create tables in PostgreSQL
        print("🔄 Creating tables in PostgreSQL...")
        db.create_all(bind=postgres_engine)
        
        # Get list of models
        models = [
            User, AirdropClaim, Referral, Achievement, 
            Notification, IPRestriction, PresaleContribution,
            WithdrawalAttempt, PresaleTransaction, Task,
            UserTask, TaskVerification, DailyStreak
        ]
        
        for model in models:
            print(f"📦 Migrating {model.__tablename__}...")
            
            try:
                # Get data from SQLite
                with sqlite_engine.connect() as conn:
                    result = conn.execute(f"SELECT * FROM {model.__tablename__}")
                    rows = result.fetchall()
                    columns = result.keys()
                
                if rows:
                    # Insert into PostgreSQL
                    with postgres_engine.connect() as conn:
                        for row in rows:
                            data = dict(zip(columns, row))
                            
                            # Clean data for PostgreSQL
                            for key, value in list(data.items()):
                                if value is None:
                                    data[key] = None
                            
                            # Build insert statement
                            columns_str = ', '.join(data.keys())
                            values_str = ', '.join([f':{key}' for key in data.keys()])
                            insert_sql = f"INSERT INTO {model.__tablename__} ({columns_str}) VALUES ({values_str}) ON CONFLICT DO NOTHING"
                            
                            conn.execute(insert_sql, data)
                    
                    print(f"  ✅ Migrated {len(rows)} rows")
                else:
                    print(f"  ⏭️  No data to migrate")
                    
            except Exception as e:
                print(f"  ⚠️  Error migrating {model.__tablename__}: {e}")
        
        print("=" * 60)
        print("✅ Migration completed!")
        print(f"📊 Summary:")
        for model in models:
            with postgres_engine.connect() as conn:
                count = conn.execute(f"SELECT COUNT(*) FROM {model.__tablename__}").scalar()
                print(f"  {model.__tablename__}: {count} rows")
        print("=" * 60)

if __name__ == '__main__':
    migrate_to_postgresql()
