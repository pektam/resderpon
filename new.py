import os
import sqlite3
import logging
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, RPCError
from prettytable import PrettyTable
from aioconsole import ainput  # Tambahkan library ini


class UnlimitedLoginSystem:
    def __init__(self):
        self._setup_folders()
        self._setup_database()
        self._setup_logging()
        self.default_2fa = "Dgvt61zwe@"

    def _setup_folders(self):
        os.makedirs('accounts', exist_ok=True)
        os.makedirs('session', exist_ok=True)
        os.makedirs('logs', exist_ok=True)

    def _setup_database(self):
        self.conn = sqlite3.connect('accounts/accounts.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts
                                 (api_id INTEGER PRIMARY KEY,
                                  api_hash TEXT,
                                  phone TEXT,
                                  twofa TEXT,
                                  user_id INTEGER,
                                  username TEXT,
                                  name TEXT)''')
        self.conn.commit()

    def _setup_logging(self):
        log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ])

    async def _create_client(self, api_id, api_hash, phone):
        client = TelegramClient(f'session/{phone}', api_id, api_hash)
        try:
            await client.connect()

            if not await client.is_user_authorized():
                try:
                    await client.send_code_request(phone)
                    code = await ainput("Masukkan kode yang diterima: ")
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    await client.sign_in(password=self.default_2fa)
            me = await client.get_me()
            return client, me
        except Exception as e:
            logging.error(f"Error creating client for {phone}: {e}")
            await client.disconnect()  # Ensure client disconnect on error
            raise  # Re-raise the exception to be handled in add_account

    async def add_account(self):
        try:
            api_id = await ainput("Masukkan API ID: ")
            api_hash = await ainput("Masukkan API HASH: ")
            phone = await ainput("Masukkan nomor telepon: ")

            client, me = await self._create_client(int(api_id), api_hash, phone)

            self.cursor.execute('''INSERT INTO accounts VALUES  
                                             (?,?,?,?,?,?,?)''',
                                (api_id, api_hash, phone, self.default_2fa,
                                 me.id, me.username, me.first_name))
            self.conn.commit()
            logging.info(f"Akun {phone} berhasil ditambahkan!")
            await client.disconnect() #disconnect after adding account
        except Exception as e:
            logging.error(f"Gagal menambahkan akun: {str(e)}")

    def list_accounts(self):
        table = PrettyTable()
        table.field_names = ["API ID", "Phone", "User ID", "Username", "Name"]

        rows = self.cursor.execute("SELECT * FROM accounts").fetchall()
        if not rows:
            print("Tidak ada akun yang tersimpan.")
            return

        for row in rows:
            table.add_row([row[0], row[2], row[4], row[5], row[6]])

        try:
            print(table)
        except Exception as e:
            logging.error(f"Gagal menampilkan tabel: {str(e)}")

    async def test_connection(self, api_id=None):
        if api_id:
            accounts = self.cursor.execute(
                "SELECT * FROM accounts WHERE api_id=?", (api_id,)
            ).fetchall()
        else:
            accounts = self.cursor.execute("SELECT * FROM accounts").fetchall()

        if not accounts:
            logging.error("Tidak ada akun yang ditemukan!")
            return {}

        results = {}
        for account in accounts:
            # Pastikan jumlah variabel sesuai dengan jumlah kolom dalam tabel Anda
            try:
                api_id, api_hash, phone, twofa, user_id, username, name = account
            except ValueError as ve:
                logging.error(f"Error unpacking account data: {ve}. Account data: {account}")
                continue  # Lewati akun ini dan lanjutkan ke akun berikutnya

            try:
                client = TelegramClient(f'session/{phone}', api_id, api_hash)
                await client.connect()
                is_authorized = await client.is_user_authorized()
                results[api_id] = {
                    'phone': phone,
                    'status': 'Berhasil' if is_authorized else 'Gagal',
                    'error': None
                }
                await client.disconnect()
            except RPCError as e:
                results[api_id] = {
                    'phone': phone,
                    'status': 'Gagal',
                    'error': str(e)
                }
                logging.error(f"RPC Error testing {phone}: {e}")
            except Exception as e:
                results[api_id] = {
                    'phone': phone,
                    'status': 'Error',
                    'error': str(e)
                }
                logging.error(f"Error testing connection for {phone}: {e}")

        return results

    def delete_account(self, api_id):
        try:
            self.cursor.execute("DELETE FROM accounts WHERE api_id=?", (api_id,))
            self.conn.commit()
            logging.info(f"Akun {api_id} berhasil dihapus!")
            return True
        except Exception as e:
            logging.error(f"Gagal menghapus akun: {str(e)}")
            return False


async def main():
    system = UnlimitedLoginSystem()

    while True:
        print("\nTelethon Unlimited Login System")
        print("1. Tambah Akun")
        print("2. Lihat Semua Akun")
        print("3. Uji Koneksi")
        print("4. Hapus Akun")
        print("5. Keluar")

        choice = await ainput("Pilih menu: ")

        if choice == '1':
            await system.add_account()
        elif choice == '2':
            system.list_accounts()
        elif choice == '3':
            api_id = await ainput("Masukkan API ID (kosongkan untuk semua): ")
            if api_id:
                results = await system.test_connection(int(api_id))
                if results:
                    for api_id, result in results.items():
                        print(
                            f"API ID: {api_id}, Phone: {result['phone']}, Status: {result['status']}, Error: {result['error']}")
                else:
                    print("Tidak ada akun yang ditemukan dengan API ID tersebut.")
            else:
                results = await system.test_connection()
                if results:
                    for api_id, result in results.items():
                        print(
                            f"API ID: {api_id}, Phone: {result['phone']}, Status: {result['status']}, Error: {result['error']}")
                else:
                    print("Tidak ada akun yang ditemukan.")
        elif choice == '4':
            api_id = await ainput("Masukkan API ID akun yang akan dihapus: ")
            if system.delete_account(int(api_id)):
                print("Akun berhasil dihapus!")
            else:
                print("Akun gagal dihapus.")
        elif choice == '5':
            break
        else:
            print("Pilihan tidak valid!")


if __name__ == "__main__":
    asyncio.run(main())

