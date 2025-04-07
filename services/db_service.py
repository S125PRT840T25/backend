import sqlite3
import time
from werkzeug.utils import secure_filename


class DBService:
    def __init__(self, db_file="file_records.db"):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        """Setup the database and table"""
        conn = sqlite3.connect(self.db_file)
        self.conn = conn
        # check version
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),  -- Ensure only one row
                version INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            "INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, 0)"
        )
        conn.commit()
        version = self.get_current_version()
        if version < 1:
            self.migrate_to_v1()
        if version < 2:
            self.migrate_to_v2()

    def migrate_to_v1(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_records (
                u_id TEXT PRIMARY KEY,
                filename TEXT,
                upload_time REAL
            )
            """
        )
        cursor.execute("UPDATE schema_version SET version = 1 WHERE id = 1")
        self.conn.commit()

    def migrate_to_v2(self):
        cursor = self.conn.cursor()
        cursor.executescript(
            """
            -- create the lookup table
            CREATE TABLE states (
                state_id INTEGER PRIMARY KEY,
                state_name TEXT UNIQUE
            );
            
            -- insert allowed values
            INSERT INTO states (state_name) VALUES ('pending');
            INSERT INTO states (state_name) VALUES ('processing');
            INSERT INTO states (state_name) VALUES ('success');
            
            -- create new temporary main table
            CREATE TABLE file_records_new (
                u_id TEXT PRIMARY KEY,
                filename TEXT,
                upload_time REAL,
                state_id INTEGER,
                FOREIGN KEY state_id REFERENCES states(state_id)
            );
            -- copy data from old table
            INSERT INTO file_records_new (u_id, filename, upload_time, state_id)
            SELECT u_id, filename, upload_time, 3 from file_records;
            -- drop old table
            DROP TABLE file_records;
            -- rename temp table
            ALTER TABLE file_records_new RENAME TO file_records;
            """
        )
        cursor.execute("ALTER TABLE file_records ADD COLUMN size INTEGER")
        cursor.execute("UPDATE schema_version SET version = 2 WHERE id = 1")
        self.conn.commit()
        cursor.close()

    def get_current_version(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT version FROM schema_version WHERE id = 1")
        version = cursor.fetchone()[0]
        cursor.close()
        return version

    def save_file_record(self, u_id, filename, size):
        """Save a file's metadata in the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO file_records (u_id, filename, upload_time, size)
            VALUES (?, ?, ?, ?)
            """,
            (u_id, filename, time.time(), size),
        )
        self.conn.commit()

    def get_filename(self, u_id):
        """Retrieve the filename from the database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT filename FROM file_records WHERE u_id = ?",
            (u_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_file_state(self, u_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT state_id FROM file_records WHERE u_id = ?",
            (u_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def update_file_state(self, u_id, state):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE file_records (u_id, state_id) VALUE (?, ?)",
            (u_id, state),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
