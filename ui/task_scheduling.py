# ui/task_scheduling.py
import asyncio
import logging
from datetime import datetime

from aioconsole import ainput
from prettytable import PrettyTable

class TaskSchedulingMenu:
    def __init__(self):
        self.scheduled_tasks = {}  # task_id -> task_info dict
        self.task_id_counter = 1

    async def task_scheduling_menu(self):
        """UI for task scheduling menu"""
        while True:
            print("\nTask Scheduling Menu")
            print("1. Add Task")
            print("2. List Tasks")
            print("3. Delete Task")
            print("4. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.add_task()
            elif choice == '2':
                await self.list_tasks()
            elif choice == '3':
                await self.delete_task()
            elif choice == '4':
                break
            else:
                print("Pilihan tidak valid!")

    async def add_task(self):
        """Add a new task with scheduled execution"""
        task_name = await ainput("Masukkan nama tugas: ")
        task_command = await ainput("Masukkan deskripsi/command tugas: ")
        delay_minutes = await ainput("Jadwalkan tugas dalam berapa menit dari sekarang: ")
        try:
            delay = float(delay_minutes) * 60  # convert to seconds
            execute_at = datetime.now() + datetime.timedelta(seconds=delay)
            task_id = self.task_id_counter
            self.task_id_counter += 1

            task_future = asyncio.create_task(self._run_task(task_id))
            self.scheduled_tasks[task_id] = {
                "name": task_name,
                "command": task_command,
                "execute_at": execute_at,
                "future": task_future,
                "executed": False
            }
            print(f"Tugas '{task_name}' dijadwalkan pada {execute_at.strftime('%Y-%m-%d %H:%M:%S')} dengan ID {task_id}.")
        except ValueError:
            print("Input waktu tidak valid!")

    async def _run_task(self, task_id):
        """Internal: Wait until the task's scheduled time, then execute the task"""
        task_info = self.scheduled_tasks.get(task_id)
        if not task_info:
            return
        now = datetime.now()
        delay = (task_info["execute_at"] - now).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
        print(f"\n[TASK EXECUTED] Tugas '{task_info['name']}' dengan command: {task_info['command']} telah dijalankan pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        task_info["executed"] = True

    async def list_tasks(self):
        """List all scheduled tasks"""
        if not self.scheduled_tasks:
            print("Tidak ada tugas yang dijadwalkan.")
            return
        table = PrettyTable()
        table.field_names = ["Task ID", "Nama Tugas", "Execute At", "Status"]
        for task_id, info in self.scheduled_tasks.items():
            status = "Sudah dieksekusi" if info.get("executed", False) else "Belum dieksekusi"
            table.add_row([task_id, info["name"], info["execute_at"].strftime('%Y-%m-%d %H:%M:%S'), status])
        print(table)

    async def delete_task(self):
        """Delete a scheduled task"""
        task_id_input = await ainput("Masukkan ID tugas yang akan dihapus: ")
        try:
            task_id = int(task_id_input)
            if task_id in self.scheduled_tasks:
                task_info = self.scheduled_tasks.pop(task_id)
                future = task_info.get("future")
                if future and not future.done():
                    future.cancel()
                print(f"Tugas dengan ID {task_id} berhasil dihapus.")
            else:
                print("Tugas tidak ditemukan.")
        except ValueError:
            print("Input harus berupa angka!")