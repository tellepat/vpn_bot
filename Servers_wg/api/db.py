from app import app, db, Client, ServerConfig
import sys
from sqlalchemy import inspect


def init_db():
    """
    Initialize the database
    :return: None
    """
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        print("Database initialized")
        print("Tables:", inspector.get_table_names())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python db.py <init>")
        sys.exit(1)

    if sys.argv[1] == 'init':
        init_db()
    else:
        print("Unknown command")
        sys.exit(1)
