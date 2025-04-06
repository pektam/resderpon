# db/database_manager.py
import os
import sqlite3
import logging
import time

class DatabaseManager:
    def __init__(self, db_path='accounts/accounts.db'):
        self.db_path = db_path
        self._setup_folders()
        self.conn = None
        self.cursor = None
        self._setup_database()
    
    def _setup_folders(self):
        os.makedirs('accounts', exist_ok=True)
    
    def _setup_database(self):
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                self._close_connection()
                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
                
                # Cek apakah tabel sudah ada
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
                table_exists = self.cursor.fetchone()
                
                if not table_exists:
                    # Buat tabel baru dengan id sebagai PRIMARY KEY autoincrement
                    self.cursor.execute('''CREATE TABLE accounts(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_id INTEGER NOT NULL, 
                        api_hash TEXT, 
                        phone TEXT UNIQUE, 
                        twofa TEXT, 
                        user_id INTEGER, 
                        username TEXT, 
                        name TEXT)''')
                else:
                    # Cek struktur tabel yang ada
                    self.cursor.execute("PRAGMA table_info(accounts)")
                    columns = [column[1] for column in self.cursor.fetchall()]
                    
                    # Jika tabel lama (tanpa kolom id), migrasi ke struktur baru
                    if "id" not in columns:
                        self.cursor.execute("ALTER TABLE accounts RENAME TO accounts_old")
                        self.cursor.execute('''CREATE TABLE accounts(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            api_id INTEGER NOT NULL, 
                            api_hash TEXT, 
                            phone TEXT UNIQUE, 
                            twofa TEXT, 
                            user_id INTEGER, 
                            username TEXT, 
                            name TEXT)''')
                        self.cursor.execute('''INSERT INTO accounts 
                            (api_id, api_hash, phone, twofa, user_id, username, name)
                            SELECT api_id, api_hash, phone, twofa, user_id, username, name 
                            FROM accounts_old''')
                        self.cursor.execute("DROP TABLE accounts_old")
                        logging.info("Database berhasil dimigrasi ke struktur baru")
                
                self.conn.commit()
                logging.debug("Database connection established successfully")
                return
            except sqlite3.Error as e:
                logging.error(f"Database connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logging.critical("Failed to connect to database after multiple attempts")
                    raise
    
    def _close_connection(self):
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                self.cursor = None
                logging.debug("Database connection closed")
            except sqlite3.Error as e:
                logging.error(f"Error closing database connection: {str(e)}")
    
    def get_connection(self):
        if not self.conn:
            self._setup_database()
        return self.conn, self.cursor
    
    def execute_query(self, query, params=(), fetch_all=False, commit=False):
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                if not self.conn:
                    self._setup_database()
                self.cursor.execute(query, params)
                if commit:
                    self.conn.commit()
                if fetch_all:
                    return self.cursor.fetchall()
                return True
            except sqlite3.Error as e:
                logging.error(f"Database query error (attempt {attempt+1}/{max_retries}): {str(e)}")
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    self._setup_database()
                else:
                    logging.error("Failed to execute query after retries")
                    raise
        return False
    
    def get_all_accounts(self):
        return self.execute_query("SELECT api_id, api_hash, phone, twofa, user_id, username, name FROM accounts", fetch_all=True)
    
    def get_account_by_api_id(self, api_id):
        accounts = self.execute_query("SELECT api_id, api_hash, phone, twofa, user_id, username, name FROM accounts WHERE api_id=?", (api_id,), fetch_all=True)
        return accounts[0] if accounts else None
    
    def add_account(self, api_id, api_hash, phone, twofa, user_id, username, name):
        try:
            result = self.execute_query(
                "INSERT OR IGNORE INTO accounts (api_id, api_hash, phone, twofa, user_id, username, name) VALUES (?,?,?,?,?,?,?)",
                (api_id, api_hash, phone, twofa, user_id, username, name),
                commit=True
            )
            if self.cursor.rowcount == 0:
                result = self.execute_query(
                    "UPDATE accounts SET api_id=?, api_hash=?, twofa=?, user_id=?, username=?, name=? WHERE phone=?",
                    (api_id, api_hash, twofa, user_id, username, name, phone),
                    commit=True
                )
            return result
        except sqlite3.IntegrityError as e:
            logging.warning(f"Constraint violation adding account {phone}: {str(e)}")
            return False
    
    def update_account(self, api_id, user_id, username, name):
        return self.execute_query(
            "UPDATE accounts SET user_id=?, username=?, name=? WHERE api_id=?", 
            (user_id, username, name, api_id), 
            commit=True
        )
    
    def delete_account(self, api_id):
        return self.execute_query("DELETE FROM accounts WHERE api_id=?", (api_id,), commit=True)

    def count_accounts(self):
        result = self.execute_query("SELECT COUNT(*) FROM accounts", fetch_all=True)
        return result[0][0] if result else 0