"""Create the PostgreSQL schema: python create_schema.py"""
import logging

import db

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    db.create_schema()
