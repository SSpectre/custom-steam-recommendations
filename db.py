import sqlite3

from flask import current_app, g

def init_db():
    with current_app.app_context():
        db = get_db()
        with current_app.open_resource("schema.sql") as schema:
            db.cursor().executescript(schema.read().decode("utf8"))

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("user_ratings.db")
    
    db.row_factory = sqlite3.Row
    
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one else result
            
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()