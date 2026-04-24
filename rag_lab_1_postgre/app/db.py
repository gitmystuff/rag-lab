import psycopg
from psycopg.rows import dict_row

# Edit only YOUR_PASSWORD for class.
# If your Postgres username is not "postgres", update "user".
# If you changed the default port, update "port".
DB_CONFIG = {
    "dbname": "rag_lab",
    "user": "postgres",
    "password": "YOUR_PASSWORD",
    "host": "localhost",
    "port": 5432,
}

def get_conn():
    return psycopg.connect(**DB_CONFIG, row_factory=dict_row)
