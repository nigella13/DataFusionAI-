import streamlit as st
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MySQL database
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "ntm"),
        password=os.getenv("MYSQL_PASSWORD", "Texas2025@1234567"),
        database=os.getenv("MYSQL_DATABASE", "Genai")
    )

# Validate login using employee ID and surname
def validate_employee(emp_id: str, surname: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE id = %s AND surname = %s", (emp_id, surname))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] > 0
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# Handle registration logic (optional, based on existing employee list)
def register_employee(emp_id: str, surname: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (id, surname) VALUES (%s, %s)", (emp_id, surname))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.IntegrityError:
        st.warning("Employee already exists.")
        return False
    except Exception as e:
        st.error(f"Registration error: {e}")
        return False

# Display login or registration interface
def show_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        emp_id = st.text_input("Employee ID")
        surname = st.text_input("Surname")
        if st.button("Login"):
            if validate_employee(emp_id, surname):
                st.session_state.logged_in = True
                st.session_state.emp_id = emp_id
                st.success("Login successful")
            else:
                st.error("Invalid credentials")

    with tab2:
        st.subheader("Register")
        new_emp_id = st.text_input("New Employee ID")
        new_surname = st.text_input("Surname")
        if st.button("Register"):
            if register_employee(new_emp_id, new_surname):
                st.success("Registration successful. Please login.")

    if not st.session_state.logged_in:
        st.stop()
