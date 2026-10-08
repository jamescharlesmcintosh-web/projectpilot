"""Persistent local store. No database daemon or hosted subscription needed."""
import json
import sqlite3
import threading
from pathlib import Path

class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL,id TEXT NOT NULL,project_id TEXT,body TEXT NOT NULL,PRIMARY KEY(kind,id))')
        self.conn.execute('CREATE INDEX IF NOT EXISTS records_project ON records(kind,project_id)')
        self.lock = threading.RLock()

    def get(self, kind, id):
        with self.lock:
            row = self.conn.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind,id)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, kind, project_id=None):
        with self.lock:
            rows = self.conn.execute('SELECT body FROM records WHERE kind=?' + (' AND project_id=?' if project_id is not None else ''), (kind, project_id) if project_id is not None else (kind,)).fetchall()
        return [json.loads(x[0]) for x in rows]

    def save(self, kind, doc):
        self.save_many([(kind,doc)])
        return doc

    def save_many(self, items):
        with self.lock, self.conn:
            for kind, doc in items:
                self.conn.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET project_id=excluded.project_id,body=excluded.body', (kind,doc['id'],doc.get('project_id'),json.dumps(doc)))

    def backup(self, target):
        with self.lock, sqlite3.connect(target) as dest: self.conn.backup(dest)

    def close(self): self.conn.close()
