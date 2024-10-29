import sqlite3
from database import get_db_connection, create_table 

def reset_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")  
    create_table()  
    conn.close()
    print("Таблица пользователей успешно сброшена и создана заново.")

if __name__ == "__main__":
    reset_users_table()
