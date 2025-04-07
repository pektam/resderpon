# ui/work_cycle.py
import asyncio
import logging
import json
import os
import random
from datetime import datetime, timedelta

from aioconsole import ainput

class WorkCycleTask:
    def __init__(self, name, interval_seconds, action_type, data=None):
        self.name = name
        self.interval_seconds = interval_seconds
        self.action_type = action_type  # 'log', 'notification', 'command', etc.
        self.data = data or {}
        self.last_run = None
        self.total_runs = 0
        self.next_run = datetime.now() + timedelta(seconds=interval_seconds)

class WorkCycleMenu:
    def __init__(self, client_manager=None, db_manager=None):
        self.work_cycle_task = None
        self.work_cycle_iteration = 0
        self.work_tasks = {}
        self.task_id_counter = 1
        self.config_file = 'work_cycle_config.json'
        self.client_manager = client_manager
        self.db_manager = db_manager
        self._load_config()

    def _load_config(self):
        """Load work cycle configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.work_cycle_iteration = config.get('iteration', 0)
                
                # Load tasks
                for task_id_str, task_data in config.get('tasks', {}).items():
                    task_id = int(task_id_str)
                    if task_id >= self.task_id_counter:
                        self.task_id_counter = task_id + 1
                    
                    task = WorkCycleTask(
                        name=task_data.get('name', 'Unknown Task'),
                        interval_seconds=task_data.get('interval_seconds', 3600),
                        action_type=task_data.get('action_type', 'log'),
                        data=task_data.get('data', {})
                    )
                    
                    # Set run statistics
                    task.total_runs = task_data.get('total_runs', 0)
                    if task_data.get('last_run'):
                        try:
                            task.last_run = datetime.fromisoformat(task_data['last_run'])
                        except ValueError:
                            task.last_run = None
                    
                    if task_data.get('next_run'):
                        try:
                            task.next_run = datetime.fromisoformat(task_data['next_run'])
                        except ValueError:
                            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
                    
                    self.work_tasks[task_id] = task
                
                print(f"Loaded work cycle configuration with {len(self.work_tasks)} tasks")
        except Exception as e:
            logging.error(f"Error loading work cycle configuration: {str(e)}")

    def _save_config(self):
        """Save work cycle configuration to file"""
        try:
            config = {
                'iteration': self.work_cycle_iteration,
                'tasks': {}
            }
            
            for task_id, task in self.work_tasks.items():
                config['tasks'][str(task_id)] = {
                    'name': task.name,
                    'interval_seconds': task.interval_seconds,
                    'action_type': task.action_type,
                    'data': task.data,
                    'total_runs': task.total_runs,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            return True
        except Exception as e:
            logging.error(f"Error saving work cycle configuration: {str(e)}")
            return False

    async def daily_work_cycle_menu(self):
        """UI for daily work cycle menu"""
        while True:
            print("\nDaily Work Cycle Menu")
            print("1. Start Work Cycle")
            print("2. Stop Work Cycle")
            print("3. View Cycle Status")
            print("4. Add Work Task")
            print("5. List Work Tasks")
            print("6. Delete Work Task")
            print("7. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.start_work_cycle()
            elif choice == '2':
                await self.stop_work_cycle()
            elif choice == '3':
                await self.view_cycle_status()
            elif choice == '4':
                await self.add_work_task()
            elif choice == '5':
                await self.list_work_tasks()
            elif choice == '6':
                await self.delete_work_task()
            elif choice == '7':
                break
            else:
                print("Pilihan tidak valid!")

    async def start_work_cycle(self):
        """Start daily work cycle with periodic task execution"""
        if self.work_cycle_task and not self.work_cycle_task.done():
            print("Daily work cycle sudah berjalan.")
            return
        
        # Check if we have tasks
        if not self.work_tasks:
            add_default = await ainput("Tidak ada tugas terdaftar. Tambahkan tugas default? (y/n): ")
            if add_default.lower() == 'y':
                self._add_default_tasks()
            else:
                print("Work cycle tidak dapat dimulai tanpa tugas.")
                return
        
        async def work_cycle():
            try:
                print(f"Work cycle dimulai pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                while True:
                    self.work_cycle_iteration += 1
                    current_time = datetime.now()
                    
                    print(f"[WORK CYCLE] Iterasi {self.work_cycle_iteration} pada {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Check and execute tasks that are due
                    tasks_executed = 0
                    for task_id, task in self.work_tasks.items():
                        if task.next_run <= current_time:
                            print(f"[TASK DUE] '{task.name}' - executing...")
                            await self._execute_task(task_id, task)
                            tasks_executed += 1
                    
                    if tasks_executed == 0:
                        print("No tasks were due in this cycle.")
                    
                    # Save configuration after each cycle
                    self._save_config()
                    
                    # Sleep for 60 seconds between checks
                    await asyncio.sleep(60)
            except asyncio.CancelledError:
                print("Work cycle cancelled.")
                raise
            except Exception as e:
                logging.error(f"Error in work cycle: {str(e)}")
                print(f"Error in work cycle: {str(e)}")
        
        self.work_cycle_task = asyncio.create_task(work_cycle())
        print("Daily work cycle dimulai.")

    async def _execute_task(self, task_id, task):
        """Execute a specific work task"""
        try:
            task.last_run = datetime.now()
            task.total_runs += 1
            
            # Update next run time
            task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
            
            # Execute action based on task type
            if task.action_type == 'log':
                message = task.data.get('message', f"Task {task.name} executed at {task.last_run}")
                print(f"[LOG] {message}")
                logging.info(message)
                return True
            
            elif task.action_type == 'notification':
                message = task.data.get('message', f"Notification: {task.name}")
                recipients = task.data.get('recipients', [])
                print(f"[NOTIFICATION] {message} to {', '.join(recipients) if recipients else 'no recipients'}")
                # Here you could implement actual notification logic
                return True
            
            elif task.action_type == 'command':
                command = task.data.get('command', '')
                if command:
                    print(f"[COMMAND] Executing: {command}")
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        print(f"[COMMAND] Success: {stdout.decode().strip()}")
                        return True
                    else:
                        print(f"[COMMAND] Error: {stderr.decode().strip()}")
                        return False
                else:
                    print("[COMMAND] No command specified")
                    return False
            
            elif task.action_type == 'status_update':
                if self.client_manager and self.db_manager:
                    total_accounts = len(self.db_manager.get_all_accounts())
                    active_clients = len(self.client_manager.active_clients)
                    print(f"[STATUS] Total Accounts: {total_accounts}, Active Clients: {active_clients}")
                    return True
                else:
                    print("[STATUS] Client or DB manager not available")
                    return False
            
            else:
                print(f"[UNKNOWN] Unknown task type: {task.action_type}")
                return False
                
        except Exception as e:
            logging.error(f"Error executing task {task_id} '{task.name}': {str(e)}")
            print(f"[ERROR] Task {task_id} '{task.name}': {str(e)}")
            return False

    def _add_default_tasks(self):
        """Add some default tasks to the work cycle"""
        # Status logging task - every hour
        status_task = WorkCycleTask(
            name="System Status Check",
            interval_seconds=3600,  # 1 hour
            action_type="status_update"
        )
        self.work_tasks[self.task_id_counter] = status_task
        self.task_id_counter += 1
        
        # Heartbeat task - every 15 minutes
        heartbeat_task = WorkCycleTask(
            name="System Heartbeat",
            interval_seconds=900,  # 15 minutes
            action_type="log",
            data={"message": "System is running normally - heartbeat check"}
        )
        self.work_tasks[self.task_id_counter] = heartbeat_task
        self.task_id_counter += 1
        
        print("Added default tasks to work cycle")
        self._save_config()

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
            
            # Show upcoming tasks
            print("\nTugas selanjutnya:")
            current_time = datetime.now()
            upcoming_tasks = sorted(
                [(task_id, task) for task_id, task in self.work_tasks.items()],
                key=lambda x: x[1].next_run
            )
            
            for task_id, task in upcoming_tasks[:5]:  # Show top 5 upcoming tasks
                time_remaining = task.next_run - current_time
                minutes_remaining = int(time_remaining.total_seconds() / 60)
                print(f"- {task.name} (ID: {task_id}): dalam {minutes_remaining} menit")
        else:
            print("Daily work cycle tidak berjalan.")
            
            # Show tasks even if cycle is not running
            if self.work_tasks:
                print(f"\nTotal tugas terdaftar: {len(self.work_tasks)}")
                print("Jalankan 'Start Work Cycle' untuk mulai menjalankan tugas-tugas.")

    async def add_work_task(self):
        """Add a new task to the work cycle"""
        name = await ainput("Nama tugas: ")
        
        print("\nJenis aksi:")
        print("1. Log (Mencatat ke log)")
        print("2. Notification (Pemberitahuan)")
        print("3. Command (Menjalankan perintah)")
        print("4. Status Update (Pembaruan status sistem)")
        
        action_type_choice = await ainput("Pilih jenis aksi (1-4): ")
        action_types = {
            '1': 'log',
            '2': 'notification',
            '3': 'command',
            '4': 'status_update'
        }
        
        if action_type_choice not in action_types:
            print("Pilihan tidak valid!")
            return
        
        action_type = action_types[action_type_choice]
        data = {}
        
        # Get task-specific data
        if action_type == 'log':
            message = await ainput("Pesan log: ")
            data['message'] = message
        
        elif action_type == 'notification':
            message = await ainput("Pesan notifikasi: ")
            recipients = await ainput("Penerima (pisahkan dengan koma): ")
            data['message'] = message
            data['recipients'] = [r.strip() for r in recipients.split(',') if r.strip()]
        
        elif action_type == 'command':
            command = await ainput("Perintah yang akan dijalankan: ")
            data['command'] = command
        
        # Get interval
        interval_choice = await ainput("Interval waktu (1: 15 menit, 2: 1 jam, 3: 1 hari, 4: Custom): ")
        
        if interval_choice == '1':
            interval_seconds = 900  # 15 minutes
        elif interval_choice == '2':
            interval_seconds = 3600  # 1 hour
        elif interval_choice == '3':
            interval_seconds = 86400  # 1 day
        elif interval_choice == '4':
            interval_minutes = await ainput("Masukkan interval dalam menit: ")
            try:
                interval_seconds = int(interval_minutes) * 60
            except ValueError:
                print("Input harus berupa angka!")
                return
        else:
            print("Pilihan tidak valid!")
            return
        
        # Create task
        task = WorkCycleTask(
            name=name,
            interval_seconds=interval_seconds,
            action_type=action_type,
            data=data
        )
        
        # Add randomness to start time to distribute load
        random_offset = random.randint(0, min(300, interval_seconds // 2))  # max 5 min or half the interval
        task.next_run = datetime.now() + timedelta(seconds=random_offset)
        
        task_id = self.task_id_counter
        self.work_tasks[task_id] = task
        self.task_id_counter += 1
        
        if self._save_config():
            print(f"Tugas '{name}' berhasil ditambahkan dengan ID {task_id}")
            print(f"Tugas akan pertama kali dijalankan pada: {task.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Tugas '{name}' ditambahkan tetapi gagal menyimpan konfigurasi.")

    async def list_work_tasks(self):
        """List all work tasks"""
        if not self.work_tasks:
            print("Belum ada tugas terdaftar.")
            return
        
        print("\nDaftar Tugas Work Cycle:")
        current_time = datetime.now()
        
        for task_id, task in self.work_tasks.items():
            time_to_next = task.next_run - current_time
            minutes_to_next = max(0, int(time_to_next.total_seconds() / 60))
            
            print(f"ID: {task_id} - {task.name}")
            print(f"  Jenis: {task.action_type}")
            print(f"  Interval: {task.interval_seconds // 60} menit")
            print(f"  Dijalankan selanjutnya dalam: {minutes_to_next} menit")
            print(f"  Total dijalankan: {task.total_runs} kali")
            if task.last_run:
                print(f"  Terakhir dijalankan: {task.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

    async def delete_work_task(self):
        """Delete a work task"""
        await self.list_work_tasks()
        task_id_input = await ainput("Masukkan ID tugas yang akan dihapus: ")
        
        try:
            task_id = int(task_id_input)
            if task_id in self.work_tasks:
                task_name = self.work_tasks[task_id].name
                del self.work_tasks[task_id]
                
                if self._save_config():
                    print(f"Tugas '{task_name}' dengan ID {task_id} berhasil dihapus.")
                else:
                    print(f"Tugas '{task_name}' dihapus tetapi gagal menyimpan konfigurasi.")
            else:
                print(f"Tugas dengan ID {task_id} tidak ditemukan.")
        except ValueError:
            print("Input harus berupa angka!")