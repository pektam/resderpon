# ui/work_cycle.py
import asyncio
import logging
from datetime import datetime

from aioconsole import ainput

class WorkCycleMenu:
    def __init__(self):
        self.work_cycle_task = None
        self.work_cycle_iteration = 0

    async def daily_work_cycle_menu(self):
        """UI for daily work cycle menu"""
        while True:
            print("\nDaily Work Cycle Menu")
            print("1. Start Work Cycle")
            print("2. Stop Work Cycle")
            print("3. View Cycle Status")
            print("4. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.start_work_cycle()
            elif choice == '2':
                await self.stop_work_cycle()
            elif choice == '3':
                await self.view_cycle_status()
            elif choice == '4':
                break
            else:
                print("Pilihan tidak valid!")

    async def start_work_cycle(self):
        """Start daily work cycle with periodic task execution"""
        if self.work_cycle_task and not self.work_cycle_task.done():
            print("Daily work cycle sudah berjalan.")
            return
        async def work_cycle():
            while True:
                self.work_cycle_iteration += 1
                print(f"[WORK CYCLE] Iterasi {self.work_cycle_iteration} pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await asyncio.sleep(10)
        self.work_cycle_task = asyncio.create_task(work_cycle())
        print("Daily work cycle dimulai.")

    async def stop_work_cycle(self):
        """Stop the daily work cycle if running"""
        if self.work_cycle_task and not self.work_cycle_task.done():
            self.work_cycle_task.cancel()
            try:
                await self.work_cycle_task
            except asyncio.CancelledError:
                pass
            print("Daily work cycle dihentikan.")
        else:
            print("Daily work cycle tidak berjalan.")

    async def view_cycle_status(self):
        """Display current status of the daily work cycle"""
        if self.work_cycle_task and not self.work_cycle_task.done():
            print(f"Daily work cycle berjalan. Iterasi terakhir: {self.work_cycle_iteration}")
        else:
            print("Daily work cycle tidak berjalan.")