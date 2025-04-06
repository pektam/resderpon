# ui/account_management.py
import asyncio
import logging
import json  # Tambahkan baris ini

from aioconsole import ainput
from prettytable import PrettyTable

class AccountManagement:
    def __init__(self, db_manager, client_manager):
        self.db_manager = db_manager
        self.client_manager = client_manager

    async def add_account(self):
        """UI for adding a new account"""
        try:
            api_id = await ainput("Masukkan API ID: ")
            api_hash = await ainput("Masukkan API HASH: ")
            phone = await ainput("Masukkan nomor telepon: ")

            if not api_id.strip() or not api_hash.strip() or not phone.strip():
                print("Semua field harus diisi!")
                return

            client = await self.client_manager.create_client(int(api_id), api_hash, phone)

            async def code_callback():
                return await ainput("Masukkan kode yang diterima: ")

            me = await self.client_manager.authorize_client(client, phone,
                                                            default_2fa="Dgvt61zwe@",
                                                            code_callback=code_callback)

            self.db_manager.add_account(api_id, api_hash, phone, "Dgvt61zwe@",
                                     me.id, me.username, me.first_name)

            print(f"Akun {phone} berhasil ditambahkan!")
            await client.disconnect()
        except Exception as e:
            logging.error(f"Gagal menambahkan akun: {str(e)}")
            print(f"Gagal menambahkan akun: {str(e)}")

    def list_accounts(self):
        """UI for listing all accounts with pagination support"""
        table = PrettyTable()
        table.field_names = ["API ID", "Phone", "User ID", "Username", "Name"]

        try:
            accounts = self.db_manager.get_all_accounts()
            if not accounts:
                print("Tidak ada akun yang tersimpan.")
                return
            for row in accounts:
                table.add_row([row[0], row[2], row[4], row[5], row[6]])
            print(table)
        except Exception as e:
            logging.error(f"Gagal menampilkan tabel: {str(e)}")
            print(f"Gagal menampilkan tabel: {str(e)}")

    async def test_connection(self):
        """UI for testing account connections with auto-fix for failed accounts"""
        try:
            api_id = await ainput("Masukkan API ID (kosongkan untuk semua): ")
            accounts = []
            if api_id.strip():
                account = self.db_manager.get_account_by_api_id(api_id)
                if account:
                    accounts = [account]
            else:
                accounts = self.db_manager.get_all_accounts()
            if not accounts:
                print("Tidak ada akun yang ditemukan!")
                return
            results = {}
            failed_accounts = []
            for account in accounts:
                api_id, api_hash, phone = account[0], account[1], account[2]
                client = await self.client_manager.create_client(api_id, api_hash, phone)
                result = await self.client_manager.test_connection(client, phone)
                results[api_id] = result
                if result['status'] != 'Berhasil':
                    failed_accounts.append(account)
                else:
                    await client.disconnect()
            print("Hasil uji koneksi:")
            for api_id, info in results.items():
                status = info['status']
                phone = info['phone']
                error = info['error']
                print(f"- {phone} (API ID: {api_id}): {status}")
                if error:
                    print(f"  Error: {error}")
            if failed_accounts:
                fix_all = await ainput("\nAda akun yang gagal. Perbaiki semua? (y/n): ")
                if fix_all.lower() == 'y':
                    for account in failed_accounts:
                        await self._fix_failed_account(account)
                else:
                    for i, account in enumerate(failed_accounts, 1):
                        print(f"{i}. {account[2]} (API ID: {account[0]})")
                    choice = await ainput("Pilih nomor akun yang akan diperbaiki (0 untuk batal): ")
                    if choice != '0':
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(failed_accounts):
                                await self._fix_failed_account(failed_accounts[idx])
                            else:
                                print("Pilihan tidak valid!")
                        except ValueError:
                            print("Input harus berupa angka!")
        except Exception as e:
            logging.error(f"Error during connection test: {str(e)}")
            print(f"Gagal melakukan uji koneksi: {str(e)}")

    async def _fix_failed_account(self, account):
        """Fix a failed account by requesting new code and saving session"""
        try:
            from telethon.errors import SessionPasswordNeededError
            api_id, api_hash, phone, twofa = account[0], account[1], account[2], account[3]
            print(f"\nMemperbaiki akun {phone}...")
            client = await self.client_manager.create_client(int(api_id), api_hash, phone)
            if not await client.is_user_authorized():
                try:
                    await client.send_code_request(phone)
                    code = await ainput("Masukkan kode Telegram yang diterima: ")
                    try:
                        await client.sign_in(phone, code)
                    except SessionPasswordNeededError:
                        if twofa:
                            await client.sign_in(password=twofa)
                        else:
                            password = await ainput("Masukkan password 2FA: ")
                            await client.sign_in(password=password)
                            self.db_manager.execute_query(
                                "UPDATE accounts SET twofa=? WHERE api_id=?",
                                (password, api_id),
                                commit=True
                            )
                    me = await client.get_me()
                    self.db_manager.update_account(api_id, me.id, me.username, me.first_name)
                    print(f"Akun {phone} berhasil diperbaiki dan diperbarui!")
                except Exception as e:
                    logging.error(f"Gagal memperbaiki akun {phone}: {str(e)}")
                    print(f"Gagal memperbaiki akun {phone}: {str(e)}")
            else:
                print(f"Akun {phone} sudah terotorisasi.")
                me = await client.get_me()
                self.db_manager.update_account(api_id, me.id, me.username, me.first_name)
                print(f"Info akun {phone} berhasil diperbarui!")
            await client.disconnect()
        except Exception as e:
            logging.error(f"Gagal memperbaiki akun: {str(e)}")
            print(f"Gagal memperbaiki akun: {str(e)}")

    async def delete_account(self):
        """UI for deleting an account"""
        try:
            api_id = await ainput("Masukkan API ID: ")
            if not api_id.strip():
                print("API ID tidak boleh kosong!")
                return
            result = self.db_manager.delete_account(api_id)
            if result:
                print(f"Akun {api_id} berhasil dihapus!")
            else:
                print(f"Gagal menghapus akun {api_id}!")
        except Exception as e:
            logging.error(f"Gagal menghapus akun: {str(e)}")
            print(f"Gagal menghapus akun: {str(e)}")

    async def update_account(self):
        """UI for updating account information"""
        try:
            api_id = await ainput("Masukkan API ID yang akan diupdate: ")
            if not api_id.strip():
                print("API ID tidak boleh kosong!")
                return
            account = self.db_manager.get_account_by_api_id(api_id)
            if not account:
                print(f"Akun dengan API ID {api_id} tidak ditemukan!")
                return
            api_id, api_hash, phone = account[0], account[1], account[2]
            client = await self.client_manager.create_client(int(api_id), api_hash, phone)
            me = await self.client_manager.authorize_client(client, phone, default_2fa="Dgvt61zwe@")
            self.db_manager.update_account(api_id, me.id, me.username, me.first_name)
            await client.disconnect()
            print(f"Akun {phone} berhasil diperbarui!")
        except Exception as e:
            logging.error(f"Gagal memperbarui akun: {str(e)}")
            print(f"Gagal memperbarui akun: {str(e)}")

    async def export_accounts(self):
        """UI for exporting accounts with verification"""
        try:
            filename = await ainput("Masukkan nama file (default: accounts_export.json): ")
            if not filename.strip():
                filename = "accounts_export.json"

            accounts = self.db_manager.get_all_accounts()
            if not accounts:
                print("Tidak ada akun untuk diekspor.")
                return

            account_list = []
            for row in accounts:
                api_id, api_hash, phone, twofa, user_id, username, name = row
                account_list.append({
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "phone": phone,
                    "twofa": twofa,
                    "user_id": user_id,
                    "username": username,
                    "name": name
                })

            total_accounts = self.db_manager.count_accounts()
            if len(account_list) != total_accounts:
                print(f"PERINGATAN: Jumlah akun yang diekspor ({len(account_list)}) tidak sesuai dengan jumlah akun di database ({total_accounts})")
                proceed = await ainput("Tetap lanjutkan ekspor? (y/n): ")
                if proceed.lower() != 'y':
                    print("Export dibatalkan.")
                    return

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(account_list, f, indent=4)

            print(f"Berhasil mengekspor {len(account_list)} akun ke {filename}")

            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    verified_accounts = json.load(f)
                if len(verified_accounts) == len(account_list):
                    print("Verifikasi file berhasil: Jumlah akun yang diekspor sesuai.")
                else:
                    print(f"PERINGATAN: Verifikasi file gagal! File berisi {len(verified_accounts)} akun, seharusnya {len(account_list)}.")
            except Exception as e:
                print(f"Gagal memverifikasi file ekspor: {str(e)}")

        except Exception as e:
            logging.error(f"Gagal mengekspor akun: {str(e)}")
            print(f"Gagal mengekspor akun: {str(e)}")

    async def import_accounts(self):
        """UI for importing accounts with improved tracking"""
        try:
            import os
            filename = await ainput("Masukkan nama file (default: accounts_export.json): ")
            if not filename.strip():
                filename = "accounts_export.json"
            if not os.path.exists(filename):
                print(f"File {filename} tidak ditemukan!")
                return

            with open(filename, 'r', encoding='utf-8') as f:
                accounts = json.load(f)

            if not accounts:
                print("Tidak ada akun untuk diimpor.")
                return

            accounts_before = self.db_manager.count_accounts()

            success_count = 0
            fail_count = 0
            skip_count = 0

            if isinstance(accounts, dict):
                accounts_list = []
                for api_id, account_data in accounts.items():
                    account_data['api_id'] = api_id
                    accounts_list.append(account_data)
                accounts = accounts_list

            processed_phones = set()

            for account in accounts:
                try:
                    api_id = int(account["api_id"]) if isinstance(account["api_id"], str) else account["api_id"]
                    api_hash = account.get("api_hash", "")
                    phone = account.get("phone", "")

                    if not phone or phone in processed_phones:
                        skip_count += 1
                        logging.warning(f"Melewati akun dengan phone {phone} (kosong atau duplikat)")
                        continue

                    twofa = account.get("twofa", "Dgvt61zwe@")
                    user_id = account.get("user_id", 0)
                    username = account.get("username", None)
                    name = account.get("name", "auto")

                    result = self.db_manager.add_account(
                        api_id, api_hash, phone, twofa,
                        user_id, username, name
                    )

                    if result:
                        success_count += 1
                        processed_phones.add(phone)
                    else:
                        fail_count += 1
                        logging.warning(f"Gagal menambahkan akun {phone} ke database")

                except Exception as e:
                    logging.error(f"Gagal mengimpor akun {account.get('phone', 'unknown')}: {str(e)}")
                    print(f"Gagal mengimpor akun {account.get('phone', 'unknown')}: {str(e)}")
                    fail_count += 1

            accounts_after = self.db_manager.count_accounts()
            actual_added = accounts_after - accounts_before

            print(f"\nRingkasan import dari {filename}:")
            print(f"Total akun dalam file: {len(accounts)}")
            print(f"Berhasil diimpor: {success_count}")
            print(f"Gagal diimpor: {fail_count}")
            print(f"Dilewati (duplikat): {skip_count}")
            print(f"Tambahan akun di database: {actual_added}")
            print(f"\nTotal akun dalam database: {accounts_after}")

        except Exception as e:
            logging.error(f"Gagal mengimpor akun: {str(e)}")
            print(f"Gagal mengimpor akun: {str(e)}")