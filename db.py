"""
DB: Handles all SQLite operations for items, revision history, and price tracking.
"""
import sqlite3
import os
import datetime

DB_PATH = "provenance.db"

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            notes TEXT,
            value TEXT,
            openai_result TEXT,
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            notes TEXT,
            value TEXT,
            timestamp TEXT,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            price TEXT,
            timestamp TEXT,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )''')
        self.conn.commit()

    def add_item(self, image_path, notes, openai_result):
        c = self.conn.cursor()
        c.execute("INSERT INTO items (image_path, notes, value, openai_result, created_at) VALUES (?, ?, ?, ?, ?)",
                  (image_path, notes, '', openai_result, datetime.datetime.now().isoformat()))
        item_id = c.lastrowid
        self.conn.commit()
        self.add_revision(item_id, notes, '')
        return item_id

    def add_revision(self, item_id, notes, value):
        c = self.conn.cursor()
        c.execute("INSERT INTO revisions (item_id, notes, value, timestamp) VALUES (?, ?, ?, ?)",
                  (item_id, notes, value, datetime.datetime.now().isoformat()))
        self.conn.commit()

    def add_price(self, item_id, price):
        c = self.conn.cursor()
        c.execute("INSERT INTO prices (item_id, price, timestamp) VALUES (?, ?, ?)",
                  (item_id, price, datetime.datetime.now().isoformat()))
        self.conn.commit()

    def get_all_items(self):
        c = self.conn.cursor()
        c.execute("SELECT id, image_path, notes, value FROM items")
        items = []
        for row in c.fetchall():
            item_id = row[0]
            history = self.get_revision_history(item_id)
            items.append({
                'id': item_id,
                'image_path': row[1],
                'notes': row[2],
                'value': row[3],
                'history': history
            })
        return items

    def get_revision_history(self, item_id):
        c = self.conn.cursor()
        c.execute("SELECT notes, value, timestamp FROM revisions WHERE item_id=? ORDER BY timestamp DESC", (item_id,))
        return c.fetchall()

    def get_analytics(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*), AVG(LENGTH(notes)) FROM items")
        count, avg_notes = c.fetchone()
        c.execute("SELECT AVG(CAST(price AS FLOAT)) FROM prices")
        avg_price = c.fetchone()[0]
        return f"Total items: {count}\nAvg notes length: {avg_notes}\nAvg price: {avg_price}"
