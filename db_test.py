import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Database Connection Parameters
DB_HOST = "dpg-cv21qj0gph6c73bbq1lg-a.oregon-postgres.render.com"
DB_NAME = "carrent_ak7c"
DB_USER = "carrent_user"
DB_PASS = "WfBNpgfvZEcSoUTruafyT8wE9MFEYyhs"

def test_psycopg2_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            sslmode='require'
        )
        print("psycopg2 Connection successful!")
        conn.close()
    except Exception as e:
        print(f"psycopg2 Connection Error: {e}")

def test_sqlalchemy_connection():
    connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?sslmode=require"
    try:
        engine = create_engine(connection_string)
        with engine.connect() as connection:
            print("SQLAlchemy Connection successful!")
    except SQLAlchemyError as e:
        print(f"SQLAlchemy Connection Error: {e}")

if __name__ == "__main__":
    print("Testing Database Connections...")
    test_psycopg2_connection()
    test_sqlalchemy_connection()
