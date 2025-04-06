# ui/analytics.py
import asyncio
import logging
import json
from datetime import datetime

from aioconsole import ainput

class AnalyticsMenu:
    def __init__(self, db_manager, client_manager):
        self.db_manager = db_manager
        self.client_manager = client_manager

    async def export_analytics_menu(self):
        """UI for export analytics menu"""
        while True:
            print("\nExport Analytics Menu")
            print("1. Export Daily Analytics")
            print("2. Export Weekly Analytics")
            print("3. Export Monthly Analytics")
            print("4. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.export_daily_analytics()
            elif choice == '2':
                await self.export_weekly_analytics()
            elif choice == '3':
                await self.export_monthly_analytics()
            elif choice == '4':
                break
            else:
                print("Pilihan tidak valid!")

    async def export_daily_analytics(self):
        """Export daily analytics data to a JSON file"""
        today = datetime.now().strftime('%Y-%m-%d')
        analytics = {
            "date": today,
            "total_accounts": len(self.db_manager.get_all_accounts()),
            "active_clients": len(self.client_manager.active_clients)
        }
        filename = await ainput("Masukkan nama file untuk daily analytics (default: daily_analytics.json): ")
        if not filename.strip():
            filename = "daily_analytics.json"
        try:
            with open(filename, 'w') as f:
                json.dump(analytics, f, indent=4)
            print(f"Daily analytics berhasil diekspor ke {filename}.")
        except Exception as e:
            logging.error(f"Gagal mengekspor daily analytics: {str(e)}")
            print(f"Gagal mengekspor daily analytics: {str(e)}")

    async def export_weekly_analytics(self):
        """Export weekly analytics data to a JSON file"""
        current_week = datetime.now().isocalendar()[1]
        analytics = {
            "week": current_week,
            "total_accounts": len(self.db_manager.get_all_accounts()),
            "active_clients": len(self.client_manager.active_clients)
        }
        filename = await ainput("Masukkan nama file untuk weekly analytics (default: weekly_analytics.json): ")
        if not filename.strip():
            filename = "weekly_analytics.json"
        try:
            with open(filename, 'w') as f:
                json.dump(analytics, f, indent=4)
            print(f"Weekly analytics berhasil diekspor ke {filename}.")
        except Exception as e:
            logging.error(f"Gagal mengekspor weekly analytics: {str(e)}")
            print(f"Gagal mengekspor weekly analytics: {str(e)}")

    async def export_monthly_analytics(self):
        """Export monthly analytics data to a JSON file"""
        current_month = datetime.now().strftime('%Y-%m')
        analytics = {
            "month": current_month,
            "total_accounts": len(self.db_manager.get_all_accounts()),
            "active_clients": len(self.client_manager.active_clients)
        }
        filename = await ainput("Masukkan nama file untuk monthly analytics (default: monthly_analytics.json): ")
        if not filename.strip():
            filename = "monthly_analytics.json"
        try:
            with open(filename, 'w') as f:
                json.dump(analytics, f, indent=4)
            print(f"Monthly analytics berhasil diekspor ke {filename}.")
        except Exception as e:
            logging.error(f"Gagal mengekspor monthly analytics: {str(e)}")
            print(f"Gagal mengekspor monthly analytics: {str(e)}")