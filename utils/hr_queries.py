import sqlite3
from db_config import get_db_path

def query_vacation_days(emp_id):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("SELECT name, vacation_days FROM employees WHERE id=?", (emp_id,))
    result = cur.fetchone()
    conn.close()
    return result
