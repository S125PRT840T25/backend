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
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),  -- Ensure only one row
                version INTEGER NOT NULL
            );
            INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, 0);
            PRAGMA foreign_keys = ON;
            """
        )
        conn.commit()
        version = self.get_current_version()
        if version == 0:
            self.create_tables()
        else:
            # if version < 1:
            #     self.migrate_to_v1()
            if version < 2:
                self.migrate_to_v2()
            if version < 3:
                self.migrate_to_v3()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript(
            """
            -- create the lookup table
            CREATE TABLE IF NOT EXISTS states (
                state_id INTEGER PRIMARY KEY,
                state_name TEXT UNIQUE
            );
            
            -- insert allowed values
            INSERT OR IGNORE INTO states (state_name) VALUES 
                ('pending'),
                ('processing'),
                ('success');
            
            -- create hash table
            CREATE TABLE IF NOT EXISTS hashs (
                hash_id INTEGER PRIMARY KEY,
                hash TEXT UNIQUE,
                size INTEGER
            );
            
            -- create main table
            CREATE TABLE IF NOT EXISTS records (
                u_id TEXT PRIMARY KEY,
                filename TEXT,
                upload_time REAL,
                state_id INTEGER,
                hash_id INTEGER,
                FOREIGN KEY (state_id) REFERENCES states(state_id),
                FOREIGN KEY (hash_id) REFERENCES hashs(hash_id)
            );
            
            -- update database version
            UPDATE schema_version SET version = 3 WHERE id = 1;
            """
        )
        self.conn.commit()

    def migrate_to_v3(self):
        cursor = self.conn.cursor()
        cursor.executescript(
            """
            -- rename table
            ALTER TABLE IF EXISTS file_records RENAME TO records;
            
            -- create the file hash table
            CREATE TABLE IF NOT EXISTS hashs (
                hash_id INTEGER PRIMARY KEY,
                hash TEXT UNIQUE,
                size INTEGER
            );
            
            -- create new temporary main table
            CREATE TABLE records_new (
                u_id TEXT PRIMARY KEY,
                filename TEXT,
                upload_time REAL,
                size INTEGER,
                state_id INTEGER,
                hash_id INTEGER,
                FOREIGN KEY (state_id) REFERENCES states(state_id),
                FOREIGN KEY (hash_id) REFERENCES hashs(hash_id)
            );
            -- copy data from old table
            INSERT INTO records_new (u_id, filename, upload_time, size, state_id)
            SELECT u_id, filename, upload_time, size, 3 FROM records;
            -- drop old table
            DROP TABLE records;
            -- rename temp table
            ALTER TABLE records_new RENAME TO records;
            
            -- update database version
            UPDATE schema_version SET version = 3 WHERE id = 1;
            """
        )
        self.conn.commit()
        cursor.close()

    def migrate_to_v2(self):
        cursor = self.conn.cursor()
        cursor.executescript(
            """
            -- create the lookup table
            CREATE TABLE IF NOT EXISTS states (
                state_id INTEGER PRIMARY KEY,
                state_name TEXT UNIQUE
            );
            
            -- insert allowed values
            INSERT OR IGNORE INTO states (state_name) VALUES 
                ('pending'),
                ('processing'),
                ('success');
            
            -- create new temporary main table
            CREATE TABLE file_records_new (
                u_id TEXT PRIMARY KEY,
                filename TEXT,
                upload_time REAL,
                size INTEGER,
                state_id INTEGER,
                FOREIGN KEY (state_id) REFERENCES states(state_id)
            );
            -- copy data from old table
            INSERT INTO file_records_new (u_id, filename, upload_time, state_id)
            SELECT u_id, filename, upload_time, 3 FROM file_records;
            -- drop old table
            DROP TABLE file_records;
            -- rename temp table
            ALTER TABLE file_records_new RENAME TO file_records;
            
            -- update database version
            UPDATE schema_version SET version = 2 WHERE id = 1;
            """
        )
        self.conn.commit()
        cursor.close()

    # def migrate_to_v1(self):
    #     cursor = self.conn.cursor()
    #     cursor.execute(
    #         """
    #         CREATE TABLE IF NOT EXISTS file_records (
    #             u_id TEXT PRIMARY KEY,
    #             filename TEXT,
    #             upload_time REAL
    #         )
    #         """
    #     )
    #     cursor.execute("UPDATE schema_version SET version = 1 WHERE id = 1")
    #     self.conn.commit()

    def get_current_version(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT version FROM schema_version WHERE id = 1")
        version = cursor.fetchone()[0]
        cursor.close()
        return version

    def save_file_record(self, u_id, filename, hash_id, hash_value, size):
        """Save a file's metadata in the database."""
        cursor = self.conn.cursor()
        if hash_id:
            cursor.execute(
                """
                INSERT OR REPLACE INTO records (u_id, filename, upload_time, state_id, hash_id)
                VALUES (
                    ?, ?, ?,
                    (SELECT state_id FROM states WHERE state_name = 'success'),
                    ?
                )
                """,
                (u_id, filename, time.time(), hash_id),
            )
        else:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hashs (hash, size)
                VALUES (?, ?)
                """,
                (hash_value, size),
            )
            cursor.execute(
                """
                INSERT OR REPLACE INTO records (u_id, filename, upload_time, state_id, hash_id)
                VALUES (
                    ?, ?, ?,
                    (SELECT state_id FROM states WHERE state_name = 'pending'),
                    (SELECT hash_id FROM hashs WHERE hash = ?)
                )
                """,
                (u_id, filename, time.time(), hash_value),
            )
        self.conn.commit()

    def check_hash(self, hash_value, size):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT hash_id FROM hashs WHERE hash = ? LIMIT 1",
            (hash_value,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_filename(self, u_id):
        """Retrieve the filename from the database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT filename FROM records WHERE u_id = ?",
            (u_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_file_state(self, u_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT states.state_name FROM states INNER JOIN records 
                ON states.state_id=records.state_id AND records.u_id = ?""",
            (u_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def update_file_state(self, u_id, state):
        cursor = self.conn.cursor()
        cursor.execute("SELECT state_id FROM states WHERE state_name = ?", (state,))
        result = cursor.fetchone()
        if result:
            cursor.execute(
                "UPDATE records SET state_id = ? WHERE u_id = ?",
                (result[0], u_id),
            )
        self.conn.commit()

    def get_file_hash(self, u_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT hashs.hash FROM hashs INNER JOIN records 
                ON hashs.hash_id=records.hash_id AND records.u_id = ?""",
            (u_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_file_id(self, hash_value):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT records.u_id FROM records INNER JOIN hashs
            ON records.hash_id = hashs.hash_id AND hashs.hash = ?
            ORDER BY records.upload_time LIMIT 1
            """,
            (hash_value,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def delete_record(self, u_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM records WHERE u_id = ?", (u_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
