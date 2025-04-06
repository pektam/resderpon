# ui/status.py
import asyncio
import logging
from datetime import datetime

from aioconsole import ainput
from prettytable import PrettyTable

class StatusMenu:  # Pastikan nama kelasnya StatusMenu
    def __init__(self, db_manager, client_manager):
        self.db_manager = db_manager
        self.client_manager = client_manager
        self.start_time = datetime.now()

    async def status_and_stats_menu(self):
        """UI for status and statistics menu"""
        while True:
            print("\nStatus and Statistics Menu")
            print("1. View System Status")
            print("2. View Account Statistics")
            print("3. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.view_system_status()
            elif choice == '2':
                await self.view_account_statistics()
            elif choice == '3':
                break
            else:
                print("Pilihan tidak valid!")

    async def view_system_status(self):
        """Display system status including uptime and active components"""
        uptime = datetime.now() - self.start_time
        total_accounts = len(self.db_manager.get_all_accounts())
        active_clients = len(self.client_manager.active_clients)
        print("\n--- System Status ---")
        print(f"Uptime: {str(uptime).split('.')[0]}")
        print(f"Total Accounts: {total_accounts}")
        print(f"Active Clients: {active_clients}")

    async def view_account_statistics(self):
        """Display account statistics using a table"""
        accounts = self.db_manager.get_all_accounts()
        if not accounts:
            print("Tidak ada data akun untuk ditampilkan.")
            return
        table = PrettyTable()
        table.field_names = ["API ID", "Phone", "User ID", "Username", "Name"]
        for row in accounts:
            table.add_row([row[0], row[2], row[4], row[5], row[6]])
        print("\n--- Account Statistics ---")
        print(table)