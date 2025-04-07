# ui/task_scheduling.py
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta

from aioconsole import ainput
from prettytable import PrettyTable

class TaskSchedulingMenu:
    def __init__(self):
        self.scheduled_tasks = {}  # task_id -> task_info dict
        self.task_id_counter = 1
        self.tasks_file = 'tasks_data.json'
        self._load_tasks()

    def _load_tasks(self):
        """Load saved tasks from file"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    
                    # Reconstruct tasks with datetime objects
                    for task_id, task_info in tasks_data.items():
                        if isinstance(task_info['execute_at'], str):
                            try:
                                task_info['execute_at'] = datetime.fromisoformat(task_info['execute_at'])
                            except ValueError:
                                # Skip invalid tasks
                                continue
                        
                        # Reschedule non-executed tasks
                        if not task_info.get('executed', False):
                            # Convert to int as JSON keys are strings
                            task_id = int(task_id)
                            if task_id >= self.task_id_counter:
                                self.task_id_counter = task_id + 1
                            
                            # Create new asyncio task
                            task_future = asyncio.create_task(self._run_task(task_id))
                            task_info['future'] = task_future
                            self.scheduled_tasks[task_id] = task_info
                
                print(f"Loaded {len(self.scheduled_tasks)} scheduled tasks from {self.tasks_file}")
        except Exception as e:
            logging.error(f"Error loading tasks: {str(e)}")
            self.scheduled_tasks = {}

    def _save_tasks(self):
        """Save tasks to file for persistence"""
        try:
            # Prepare data for JSON serialization
            tasks_data = {}
            for task_id, task_info in self.scheduled_tasks.items():
                # Create a copy without the future field
                task_data = task_info.copy()
                if 'future' in task_data:
                    del task_data['future']
                
                # Convert datetime to string
                if isinstance(task_data['execute_at'], datetime):
                    task_data['execute_at'] = task_data['execute_at'].isoformat()
                
                tasks_data[str(task_id)] = task_data
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=4)
            
            return True
        except Exception as e:
            logging.error(f"Error saving tasks: {str(e)}")
            return False

    async def task_scheduling_menu(self):
        """UI for task scheduling menu"""
        while True:
            print("\nTask Scheduling Menu")
            print("1. Add Task")
            print("2. List Tasks")
            print("3. Delete Task")
            print("4. Execute Task Now")
            print("5. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.add_task()
            elif choice == '2':
                await self.list_tasks()
            elif choice == '3':
                await self.delete_task()
            elif choice == '4':
                await self.execute_task_now()
            elif choice == '5':
                break
            else:
                print("Pilihan tidak valid!")

    async def add_task(self):
        """Add a new task with scheduled execution"""
        task_name = await ainput("Masukkan nama tugas: ")
        print("\nJenis tugas:")
        print("1. Command/Perintah Sistem")
        print("2. Python Script")
        print("3. Pengingat")
        task_type = await ainput("Pilih jenis tugas (1-3): ")
        
        task_command = ""
        if task_type == '1':
            task_command = await ainput("Masukkan perintah sistem yang akan dijalankan: ")
        elif task_type == '2':
            script_path = await ainput("Masukkan path ke file Python: ")
            args = await ainput("Masukkan argumen (opsional): ")
            task_command = f"python {script_path} {args}"
        elif task_type == '3':
            task_message = await ainput("Masukkan pesan pengingat: ")
            task_command = f"REMINDER: {task_message}"
        else:
            print("Jenis tugas tidak valid!")
            return
        
        delay_minutes = await ainput("Jadwalkan tugas dalam berapa menit dari sekarang: ")
        try:
            delay = float(delay_minutes) * 60  # convert to seconds
            execute_at = datetime.now() + timedelta(seconds=delay)
            task_id = self.task_id_counter
            self.task_id_counter += 1

            task_future = asyncio.create_task(self._run_task(task_id))
            self.scheduled_tasks[task_id] = {
                "name": task_name,
                "type": int(task_type) if task_type in ['1', '2', '3'] else 3,
                "command": task_command,
                "execute_at": execute_at,
                "future": task_future,
                "executed": False
            }
            
            # Save tasks for persistence
            if self._save_tasks():
                print(f"Tugas '{task_name}' dijadwalkan pada {execute_at.strftime('%Y-%m-%d %H:%M:%S')} dengan ID {task_id}.")
            else:
                print(f"Tugas '{task_name}' dijadwalkan tetapi gagal disimpan ke file.")
        except ValueError:
            print("Input waktu tidak valid!")

    async def _run_task(self, task_id):
        """Internal: Wait until the task's scheduled time, then execute the task"""
        task_info = self.scheduled_tasks.get(task_id)
        if not task_info:
            return
        
        try:
            now = datetime.now()
            delay = (task_info["execute_at"] - now).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Execute the task based on its type
            task_type = task_info.get("type", 3)  # Default to reminder
            result = "Executed"
            
            if task_type == 1:  # System command
                try:
                    cmd = task_info["command"]
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        result = f"Success: {stdout.decode().strip()}"
                    else:
                        result = f"Error: {stderr.decode().strip()}"
                except Exception as e:
                    result = f"Execution error: {str(e)}"
            
            elif task_type == 2:  # Python script
                try:
                    cmd = task_info["command"]
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        result = f"Script executed: {stdout.decode().strip()}"
                    else:
                        result = f"Script error: {stderr.decode().strip()}"
                except Exception as e:
                    result = f"Script execution error: {str(e)}"
            
            elif task_type == 3:  # Reminder
                result = task_info["command"]
            
            print(f"\n[TASK EXECUTED] Tugas '{task_info['name']}': {result}")
            print(f"Waktu eksekusi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            task_info["executed"] = True
            task_info["result"] = result
            self._save_tasks()
        except Exception as e:
            logging.error(f"Error executing task {task_id}: {str(e)}")
            print(f"\n[TASK ERROR] Tugas '{task_info['name']}' gagal: {str(e)}")
            task_info["executed"] = True
            task_info["result"] = f"Error: {str(e)}"
            self._save_tasks()

    async def list_tasks(self):
        """List all scheduled tasks"""
        if not self.scheduled_tasks:
            print("Tidak ada tugas yang dijadwalkan.")
            return
        
        table = PrettyTable()
        table.field_names = ["Task ID", "Nama Tugas", "Jenis", "Execute At", "Status"]
        
        # Classify tasks by status
        current_tasks = []
        completed_tasks = []
        
        for task_id, info in self.scheduled_tasks.items():
            task_type_name = {1: "Command", 2: "Script", 3: "Reminder"}.get(info.get("type", 3), "Unknown")
            status = "Sudah dieksekusi" if info.get("executed", False) else "Belum dieksekusi"
            execute_time = info["execute_at"].strftime('%Y-%m-%d %H:%M:%S') if isinstance(info["execute_at"], datetime) else info["execute_at"]
            
            row = [task_id, info["name"], task_type_name, execute_time, status]
            
            if info.get("executed", False):
                completed_tasks.append(row)
            else:
                current_tasks.append(row)
        
        # Show active tasks first
        for row in current_tasks:
            table.add_row(row)
        
        # Then show completed tasks
        for row in completed_tasks:
            table.add_row(row)
        
        print("\nDaftar Tugas Terjadwal:")
        print(table)
        
        # Show details of tasks if requested
        show_details = await ainput("Tampilkan detail tugas? (y/n): ")
        if show_details.lower() == 'y':
            task_id_str = await ainput("Masukkan ID tugas: ")
            try:
                task_id = int(task_id_str)
                if task_id in self.scheduled_tasks:
                    task_info = self.scheduled_tasks[task_id]
                    print(f"\nDetail Tugas {task_id}:")
                    print(f"Nama: {task_info['name']}")
                    task_type_name = {1: "Command", 2: "Script", 3: "Reminder"}.get(task_info.get("type", 3), "Unknown")
                    print(f"Jenis: {task_type_name}")
                    print(f"Command/Pesan: {task_info['command']}")
                    print(f"Jadwal: {task_info['execute_at'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task_info['execute_at'], datetime) else task_info['execute_at']}")
                    print(f"Status: {'Sudah dieksekusi' if task_info.get('executed', False) else 'Belum dieksekusi'}")
                    if task_info.get("executed", False) and "result" in task_info:
                        print(f"Hasil: {task_info['result']}")
                else:
                    print(f"Tugas dengan ID {task_id} tidak ditemukan.")
            except ValueError:
                print("Input harus berupa angka!")

    async def delete_task(self):
        """Delete a scheduled task"""
        await self.list_tasks()
        task_id_input = await ainput("Masukkan ID tugas yang akan dihapus: ")
        try:
            task_id = int(task_id_input)
            if task_id in self.scheduled_tasks:
                task_info = self.scheduled_tasks.pop(task_id)
                future = task_info.get("future")
                if future and not future.done():
                    future.cancel()
                
                if self._save_tasks():
                    print(f"Tugas dengan ID {task_id} berhasil dihapus.")
                else:
                    print(f"Tugas dengan ID {task_id} dihapus dari memori tetapi gagal menyimpan perubahan.")
            else:
                print("Tugas tidak ditemukan.")
        except ValueError:
            print("Input harus berupa angka!")

    async def execute_task_now(self):
        """Immediately execute a scheduled task"""
        await self.list_tasks()
        task_id_input = await ainput("Masukkan ID tugas yang akan dijalankan sekarang: ")
        try:
            task_id = int(task_id_input)
            if task_id in self.scheduled_tasks:
                task_info = self.scheduled_tasks[task_id]
                
                if task_info.get("executed", False):
                    confirm = await ainput("Tugas ini sudah dieksekusi sebelumnya. Jalankan lagi? (y/n): ")
                    if confirm.lower() != 'y':
                        return
                
                # Cancel existing future if it exists and not done
                future = task_info.get("future")
                if future and not future.done():
                    future.cancel()
                
                # Set execution time to now
                task_info["execute_at"] = datetime.now()
                
                # Create a new future for immediate execution
                new_future = asyncio.create_task(self._run_task(task_id))
                task_info["future"] = new_future
                
                print(f"Tugas '{task_info['name']}' akan segera dijalankan...")
            else:
                print("Tugas tidak ditemukan.")
        except ValueError:
            print("Input harus berupa angka!")