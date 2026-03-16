import pymysql
from pymysql.cursors import DictCursor

DB_CONFIG = {
    "host": "73.166.120.244",
    "user": "inventory_user",
    "password": "StrongPasswordHere123!",
    "database": "inventory_app",
    "port": 3306,
    "cursorclass": DictCursor,
    "autocommit": False,
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)