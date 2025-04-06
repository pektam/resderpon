# ui/main_menu.py
import asyncio
import logging

from aioconsole import ainput

class MainMenu:
    def __init__(self, account_manager, auto_responder_menu, task_scheduling_menu,
                 work_cycle_menu, analytics_menu, status_menu):
        self.account_manager = account_manager
        self.auto_responder_menu = auto_responder_menu
        self.task_scheduling_menu = task_scheduling_menu
        self.work_cycle_menu = work_cycle_menu
        self.analytics_menu = analytics_menu
        self.status_menu = status_menu

    async def display_main_menu(self):
        """Display main menu and handle user choices"""
        while True:
            print("\nTelethon Unlimited Login System")
            print("1. Tambah Akun")
            print("2. Lihat Semua Akun")
            print("3. Uji Koneksi")
            print("4. Hapus Akun")
            print("5. Auto Responder")
            print("6. Update Akun")
            print("7. Export Akun")
            print("8. Import Akun")
            print("9. Task Scheduling Menu")
            print("10. Daily Work Cycle Menu")
            print("11. Export Analytics Menu")
            print("12. Status and Statistics Menu")
            print("13. Keluar")

            choice = await ainput("Pilih menu: ")

            if choice == '1':
                await self.account_manager.add_account()
            elif choice == '2':
                self.account_manager.list_accounts()
            elif choice == '3':
                await self.account_manager.test_connection()
            elif choice == '4':
                await self.account_manager.delete_account()
            elif choice == '5':
                await self.auto_responder_menu.auto_responder_menu()
            elif choice == '6':
                await self.account_manager.update_account()
            elif choice == '7':
                await self.account_manager.export_accounts()
            elif choice == '8':
                await self.account_manager.import_accounts()
            elif choice == '9':
                await self.task_scheduling_menu.task_scheduling_menu()
            elif choice == '10':
                await self.work_cycle_menu.daily_work_cycle_menu()
            elif choice == '11':
                await self.analytics_menu.export_analytics_menu()
            elif choice == '12':
                await self.status_menu.status_and_stats_menu()
            elif choice == '13':
                break
            else:
                print("Pilihan tidak valid!")