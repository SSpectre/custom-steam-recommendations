import sqlite3

from flask import current_app, g

SCHEMA_FILE = "schema.sql"
DATABASE_FILE = "user_ratings.db"

def init_db():
    """Creates database from schema file."""
    with current_app.app_context():
        db = get_db()
        with current_app.open_resource(SCHEMA_FILE) as schema:
            db.cursor().executescript(schema.read().decode("utf8"))

def get_db():
    """Connects to database. Returns Connection object."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
    
    #treat database rows as dictionaries
    db.row_factory = sqlite3.Row
    
    return db

def query_db(query, args=(), one=False):
    """Queries the database and returns the result."""
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one else result
            
def close_db(exception):
    """Closes database connection."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()