import streamlit as st
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime

# Database Configuration
def get_db_connection():
    """Establish and return a connection to the database."""
    try:
        return pymysql.connect(
            host="localhost",
            user="root",
            password="nihal@22",
            database="attendance_system",
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=True
        )
    except pymysql.Error as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def get_registered_students():
    """Fetch all registered students from the userDetails table."""
    connection = get_db_connection()
    if connection is None:
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM userDetails")
            students = [row['name'] for row in cursor.fetchall()]
        return students
    except pymysql.Error as e:
        st.error(f"Error fetching registered students: {e}")
        return []
    finally:
        connection.close()

def insert_default_attendance():
    """Insert default 'Absent' records for all registered students for the day."""
    connection = get_db_connection()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            today = datetime.now().strftime("%Y-%m-%d")

            # Ensure all registered students have an attendance entry for today
            cursor.execute("""
                INSERT INTO attendance (name, date, status)
                SELECT name, %s, 'Absent'
                FROM userDetails
                WHERE name NOT IN (
                    SELECT name FROM attendance WHERE date = %s
                )
            """, (today, today))

            st.info("Daily attendance initialized successfully.")
            return True
    except pymysql.Error as e:
        st.error(f"Failed to insert default attendance: {e}")
        return False
    finally:
        connection.close()
