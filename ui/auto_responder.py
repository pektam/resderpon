# ui/auto_responder.py
import asyncio
import logging
import random

from aioconsole import ainput

class AutoResponderMenu:
    def __init__(self, rules_manager, client_manager, message_handler, db_manager):
        self.rules_manager = rules_manager
        self.client_manager = client_manager
        self.message_handler = message_handler
        self.db_manager = db_manager

    async def auto_responder_menu(self):
        """UI for auto responder menu"""
        while True:
            print("\nAuto Responder Menu")
            print("1. Lihat Semua Aturan")
            print("2. Tambah Aturan Baru")
            print("3. Hapus Aturan")
            print("4. Edit Aturan")
            print("5. Tambah Respons Alternatif")
            print("6. Hapus Respons Alternatif")
            print("7. Mulai Auto Responder")
            print("8. Hentikan Auto Responder")
            print("9. Export Aturan")
            print("10. Import Aturan")
            print("11. Kembali ke Menu Utama")

            choice = await ainput("Pilih menu: ")

            if choice == '1':
                self.list_rules()
            elif choice == '2':
                await self.add_rule()
            elif choice == '3':
                await self.delete_rule()
            elif choice == '4':
                await self.edit_rule()
            elif choice == '5':
                await self.add_alternative_response()
            elif choice == '6':
                await self.delete_alternative_response()
            elif choice == '7':
                await self.start_responder()
            elif choice == '8':
                await self.stop_responder()
            elif choice == '9':
                await self.export_rules()
            elif choice == '10':
                await self.import_rules()
            elif choice == '11':
                break  # Keluar dari loop menu auto responder
            else:
                print("Pilihan tidak valid!")

    def list_rules(self):
        """List all rules with responses"""
        rules = self.rules_manager.get_all_rules()
        if not rules:
            print("Tidak ada aturan auto responder yang tersimpan.")
            return
        print("\nDaftar Aturan Auto Responder:")
        for rule_id, rule in rules.items():
            print(f"ID: {rule_id}")
            print(f"  Kata Kunci: {rule['keyword']}")
            responses = rule.get('responses', [])
            if not responses and 'response' in rule:
                responses = [rule['response']]
            print(f"  Jumlah Respons: {len(responses)}")
            for i, response in enumerate(responses):
                print(f"    [{i}] {response}")
            print(f"  Hanya Private Chat: {'Ya' if rule.get('private_only', False) else 'Tidak'}")
            print()

    async def add_rule(self):
        """UI for adding a new rule"""
        keyword = await ainput("Masukkan kata kunci/pola: ")
        response = await ainput("Masukkan pesan balasan: ")
        private_only = await ainput("Hanya untuk private chat? (y/n): ")
        success, message = self.rules_manager.add_rule(
            keyword, response, private_only.lower() == 'y'
        )
        print(message)

    async def delete_rule(self):
        """UI for deleting a rule"""
        self.list_rules()
        rule_id = await ainput("Masukkan ID aturan yang akan dihapus: ")
        success, message = self.rules_manager.delete_rule(rule_id)
        print(message)

    async def edit_rule(self):
        """UI for editing a rule"""
        self.list_rules()
        rule_id = await ainput("Masukkan ID aturan yang akan diedit: ")
        rule = self.rules_manager.get_rule(rule_id)
        if not rule:
            print(f"Aturan dengan ID {rule_id} tidak ditemukan!")
            return
        print(f"\nNilai saat ini:")
        print(f"Kata Kunci: {rule['keyword']}")
        responses = rule.get('responses', [])
        if not responses and 'response' in rule:
            response_main = rule['response']
        else:
            response_main = responses[0] if responses else ""
        print(f"Pesan Balasan Utama: {response_main}")
        print(f"Hanya Private Chat: {'Ya' if rule.get('private_only', False) else 'Tidak'}")
        print("\nMasukkan nilai baru (kosongkan untuk menggunakan nilai saat ini):")
        new_keyword = await ainput("Kata kunci baru: ")
        new_private_only = await ainput("Hanya private chat? (y/n): ")
        private_only = None
        if new_private_only.strip():
            private_only = new_private_only.lower() == 'y'
        success, message = self.rules_manager.update_rule(
            rule_id,
            keyword=new_keyword if new_keyword.strip() else None,
            private_only=private_only
        )
        print(message)

    async def add_alternative_response(self):
        """UI for adding alternative response to existing rule"""
        self.list_rules()
        rule_id = await ainput("Masukkan ID aturan yang akan ditambah respons alternatif: ")
        rule = self.rules_manager.get_rule(rule_id)
        if not rule:
            print(f"Aturan dengan ID {rule_id} tidak ditemukan!")
            return
        new_response = await ainput("Masukkan respons alternatif baru: ")
        if not new_response.strip():
            print("Respons tidak boleh kosong!")
            return
        success, message = self.rules_manager.update_rule(
            rule_id,
            response=new_response
        )
        print(message)

    async def delete_alternative_response(self):
        """UI for deleting an alternative response"""
        self.list_rules()
        rule_id = await ainput("Masukkan ID aturan: ")
        rule = self.rules_manager.get_rule(rule_id)
        if not rule:
            print(f"Aturan dengan ID {rule_id} tidak ditemukan!")
            return
        responses = rule.get('responses', [])
        if not responses and 'response' in rule:
            print("Aturan ini menggunakan format lama dan tidak mendukung multiple responses.")
            return
        if len(responses) <= 1:
            print("Aturan harus memiliki minimal satu respons! Hapus aturan jika tidak diperlukan.")
            return
        try:
            response_index = int(await ainput(f"Masukkan indeks respons yang akan dihapus (0-{len(responses)-1}): "))
            success, message = self.rules_manager.delete_response(rule_id, response_index)
            print(message)
        except ValueError:
            print("Indeks respons harus berupa angka!")

    async def start_responder(self):
        """UI for starting an auto responder with various options"""
        if not self.rules_manager.get_all_rules():
            print("Tidak ada aturan auto responder yang tersimpan. Tambahkan aturan terlebih dahulu.")
            return
        accounts = self.db_manager.get_all_accounts()
        if not accounts:
            print("Tidak ada akun yang tersimpan.")
            return
        print("\nPilih opsi untuk auto responder:")
        print("1. Pilih akun spesifik")
        print("2. Mulai semua akun")
        print("3. Random 5 akun")
        print("4. Random 10 akun")
        print("5. Random 20 akun")
        print("6. Masukkan jumlah akun random")
        option_choice = await ainput("Pilih opsi: ")
        selected_accounts = []
        try:
            option = int(option_choice)
            if option == 1:
                print("\nPilih akun untuk auto responder:")
                for i, account in enumerate(accounts, 1):
                    print(f"{i}. {account[2]} ({account[6] if account[6] else 'Tidak ada nama'})")
                account_choice = await ainput("Pilih nomor akun: ")
                try:  # Tambahkan blok try-except
                    account_index = int(account_choice) - 1
                    if account_index < 0 or account_index >= len(accounts):
                        print("Pilihan tidak valid!")
                        return
                    selected_accounts = [accounts[account_index]]
                except ValueError:  # Tangkap kesalahan ValueError
                    print("Input harus berupa angka!")
                    return
            elif option == 2:
                selected_accounts = accounts
            elif option in [3, 4, 5]:
                num_accounts = {3: 5, 4: 10, 5: 20}.get(option)
                if len(accounts) <= num_accounts:
                    selected_accounts = accounts
                else:
                    selected_accounts = random.sample(accounts, num_accounts)
            elif option == 6:
                num_random = await ainput("Masukkan jumlah akun random: ")
                try:
                    num_random = int(num_random)
                    if num_random <= 0:
                        print("Jumlah akun harus lebih dari 0!")
                        return
                    if len(accounts) <= num_random:
                        selected_accounts = accounts
                    else:
                        selected_accounts = random.sample(accounts, num_random)
                except ValueError:
                    print("Input harus berupa angka!")
                    return
            else:
                print("Pilihan tidak valid!")
                return
            print("\nPengaturan waktu respons:")
            delay_config = await ainput("Total waktu respons (dalam menit, misalnya 120 untuk 2 jam): ")
            try:
                delay_minutes = float(delay_config)
                if delay_minutes <= 0:
                    print("Waktu respons minimal 1 menit!")
                    return
                total_delay_seconds = delay_minutes * 60
                print(f"\nMenyiapkan {len(selected_accounts)} akun dengan estimasi waktu respons {delay_minutes} menit")
                activated_count = 0
                for account in selected_accounts:
                    api_id, api_hash, phone = account[0], account[1], account[2]
                    if phone in self.client_manager.active_clients:
                        print(f"Auto responder untuk {phone} sudah berjalan!")
                        continue
                    client = await self.client_manager.create_client(api_id, api_hash, phone)
                    if not await client.is_user_authorized():
                        print(f"Akun {phone} belum diotorisasi. Silakan login terlebih dahulu.")
                        await client.disconnect()
                        continue
                    variation = random.uniform(0.8, 1.2)
                    account_delay = total_delay_seconds / len(selected_accounts) * variation
                    self.message_handler.setup_handler(client, phone, account_delay)
                    self.client_manager.add_active_client(phone, client)
                    activated_count += 1
                    await asyncio.sleep(0.2)
                if activated_count > 0:
                    print(f"\n{activated_count} akun berhasil diaktifkan!")
                    print(f"Estimasi waktu respons: {delay_minutes} menit ({delay_minutes/60:.1f} jam)")
                    print("Setiap akun akan merespons dengan delay yang berbeda untuk pola lebih natural")
                else:
                    print("Tidak ada akun yang berhasil diaktifkan.")
            except ValueError:
                print("Input waktu harus berupa angka!")
                return
        except ValueError:
            print("Input harus berupa angka!")
        except Exception as e:
            logging.error(f"Gagal memulai auto responder: {str(e)}")
            print(f"Gagal memulai auto responder: {str(e)}")

    async def stop_responder(self):
        """UI for stopping an auto responder"""
        active_clients = self.client_manager.active_clients
        if not active_clients:
            print("Tidak ada auto responder yang aktif!")
            return
        print("\nDaftar auto responder yang aktif:")
        for i, phone in enumerate(active_clients.keys(), 1):
            print(f"{i}. {phone}")
        choice = await ainput("Pilih nomor auto responder yang akan dihentikan (0 untuk semua): ")
        try:
            if choice == '0':
                for phone in list(active_clients.keys()):
                    await self.client_manager.disconnect_client(phone)
                    self.message_handler.remove_handler(phone)
                print("Semua auto responder berhasil dihentikan!")
            else:
                choice_idx = int(choice) - 1
                if choice_idx < 0 or choice_idx >= len(active_clients):
                    print("Pilihan tidak valid!")
                    return
                phone = list(active_clients.keys())[choice_idx]
                await self.client_manager.disconnect_client(phone)
                self.message_handler.remove_handler(phone)
                print(f"Auto responder untuk {phone} berhasil dihentikan!")
        except ValueError:
            print("Input harus berupa angka!")
        except Exception as e:
            logging.error(f"Gagal menghentikan auto responder: {str(e)}")
            print(f"Gagal menghentikan auto responder: {str(e)}")

    async def export_rules(self):
        """UI for exporting rules"""
        filename = await ainput("Masukkan nama file (default: responder_rules_export.json): ")
        if not filename.strip():
            filename = "responder_rules_export.json"
        success, message = self.rules_manager.export_rules(filename)
        print(message)

    async def import_rules(self):
        """UI for importing rules"""
        filename = await ainput("Masukkan nama file (default: responder_rules_export.json): ")
        if not filename.strip():
            filename = "responder_rules_export.json"
        action = await ainput("Ganti aturan yang ada atau gabungkan? (g/m): ")
        replace = action.lower() == 'g'
        success, message = self.rules_manager.import_rules(filename, replace)
        print(message)