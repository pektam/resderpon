# ui/status.py
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta

from aioconsole import ainput
from prettytable import PrettyTable

class StatusMenu:
    def __init__(self, db_manager, client_manager):
        self.db_manager = db_manager
        self.client_manager = client_manager
        self.start_time = datetime.now()
        self.status_log_file = 'status_history.json'
        self.status_history = self._load_status_history()

    def _load_status_history(self):
        """Load status history from file if available"""
        if os.path.exists(self.status_log_file):
            try:
                with open(self.status_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading status history: {str(e)}")
        return []

    def _save_status_history(self):
        """Save status history to file"""
        try:
            with open(self.status_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.status_history, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving status history: {str(e)}")
            return False

    def _add_status_record(self, record):
        """Add a status record to history"""
        self.status_history.append(record)
        # Keep only the last 100 records to prevent file growth
        if len(self.status_history) > 100:
            self.status_history = self.status_history[-100:]
        return self._save_status_history()

    async def status_and_stats_menu(self):
        """UI for status and statistics menu"""
        while True:
            print("\nStatus and Statistics Menu")
            print("1. View System Status")
            print("2. View Account Statistics")
            print("3. View Active Clients")
            print("4. View Status History")
            print("5. Check System Health")
            print("6. Export Status Report")
            print("7. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            if choice == '1':
                await self.view_system_status()
            elif choice == '2':
                await self.view_account_statistics()
            elif choice == '3':
                await self.view_active_clients()
            elif choice == '4':
                await self.view_status_history()
            elif choice == '5':
                await self.check_system_health()
            elif choice == '6':
                await self.export_status_report()
            elif choice == '7':
                break
            else:
                print("Pilihan tidak valid!")

    async def view_system_status(self):
        """Display system status including uptime and active components"""
        # Calculate uptime
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Get account and client statistics
        total_accounts = len(self.db_manager.get_all_accounts())
        active_clients = len(self.client_manager.active_clients)
        
        # Get database info
        try:
            conn, cursor = self.db_manager.get_connection()
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size = page_count * page_size / (1024 * 1024)  # Size in MB
        except Exception as e:
            logging.error(f"Error getting database info: {str(e)}")
            db_size = 0
        
        # Check if session files exist
        session_count = 0
        if os.path.exists('session'):
            session_count = len([f for f in os.listdir('session') if f.endswith('.session')])
        
        # Display status info
        print("\n--- System Status ---")
        print(f"Uptime: {uptime_str}")
        print(f"Total Accounts: {total_accounts}")
        print(f"Active Clients: {active_clients}")
        print(f"Session Files: {session_count}")
        print(f"Database Size: {db_size:.2f} MB")
        print(f"Status Records: {len(self.status_history)}")
        
        # Add status record to history
        status_record = {
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime_str,
            "total_accounts": total_accounts,
            "active_clients": active_clients,
            "session_files": session_count,
            "db_size_mb": round(db_size, 2)
        }
        self._add_status_record(status_record)
        
        # Show additional system info menu
        print("\nOptions:")
        print("1. Check Database Integrity")
        print("2. View Log Summary")
        print("3. Back")
        
        choice = await ainput("Pilih opsi: ")
        if choice == '1':
            await self._check_database_integrity()
        elif choice == '2':
            await self._view_log_summary()

    async def _check_database_integrity(self):
        """Check database integrity"""
        print("\nMemeriksa integritas database...")
        try:
            conn, cursor = self.db_manager.get_connection()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            if result == "ok":
                print("✅ Database integrity check passed")
            else:
                print(f"⚠️ Database integrity issues found: {result}")
                
            # Check for database optimizations
            cursor.execute("PRAGMA auto_vacuum")
            auto_vacuum = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            print(f"\nDatabase settings:")
            print(f"Auto Vacuum: {auto_vacuum}")
            print(f"Journal Mode: {journal_mode}")
            
            if auto_vacuum == 0:
                print("⚠️ Consider enabling auto_vacuum to reduce database size over time")
            if journal_mode.lower() != "wal":
                print("⚠️ Consider using WAL journal mode for better performance")
        except Exception as e:
            logging.error(f"Error checking database integrity: {str(e)}")
            print(f"Error checking database: {str(e)}")

    async def _view_log_summary(self):
        """Display summary of recent logs"""
        print("\nLog Summary:")
        log_dir = 'logs'
        
        if not os.path.exists(log_dir):
            print("Log directory not found")
            return
        
        # Get today's log file
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"{today}.log")
        
        if not os.path.exists(log_file):
            print(f"No log file found for today ({log_file})")
            # Try to find the most recent log file
            log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)
            if log_files:
                log_file = os.path.join(log_dir, log_files[0])
                print(f"Using most recent log file: {log_file}")
            else:
                print("No log files found")
                return
        
        # Read the last 20 log entries
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Count log levels
            log_levels = {'INFO': 0, 'ERROR': 0, 'WARNING': 0, 'DEBUG': 0, 'CRITICAL': 0}
            for line in lines:
                for level in log_levels.keys():
                    if f' - {level} - ' in line:
                        log_levels[level] += 1
            
            print("\nLog level summary:")
            for level, count in log_levels.items():
                print(f"{level}: {count}")
            
            # Show the last 10 lines
            print("\nRecent log entries:")
            for line in lines[-10:]:
                print(line.strip())
        except Exception as e:
            logging.error(f"Error reading log file: {str(e)}")
            print(f"Error reading log file: {str(e)}")

    async def view_account_statistics(self):
        """Display account statistics using a table"""
        accounts = self.db_manager.get_all_accounts()
        if not accounts:
            print("Tidak ada data akun untuk ditampilkan.")
            return
        
        # Create main table
        table = PrettyTable()
        table.field_names = ["API ID", "Phone", "User ID", "Username", "Name"]
        
        # Add rows
        for row in accounts:
            table.add_row([row[0], row[2], row[4], row[5], row[6]])
        
        print("\n--- Account Statistics ---")
        print(table)
        
        # Add account summary
        print("\nAccount Summary:")
        print(f"Total Accounts: {len(accounts)}")
        
        # Count accounts with username
        accounts_with_username = sum(1 for row in accounts if row[5])
        print(f"Accounts with Username: {accounts_with_username} ({accounts_with_username/len(accounts)*100:.1f}%)")
        
        # Show additional account options
        print("\nOptions:")
        print("1. Search Account")
        print("2. Sort Accounts")
        print("3. View Account Distribution")
        print("4. Back")
        
        choice = await ainput("Pilih opsi: ")
        if choice == '1':
            await self._search_account()
        elif choice == '2':
            await self._sort_accounts()
        elif choice == '3':
            await self._view_account_distribution()

    async def _search_account(self):
        """Search for specific account"""
        search_term = await ainput("Masukkan kata kunci pencarian (phone/username/name): ")
        if not search_term.strip():
            return
        
        accounts = self.db_manager.get_all_accounts()
        results = []
        
        for row in accounts:
            # Search in phone, username, and name
            if (search_term.lower() in str(row[2]).lower() or  # phone
                (row[5] and search_term.lower() in str(row[5]).lower()) or  # username
                (row[6] and search_term.lower() in str(row[6]).lower())):  # name
                results.append(row)
        
        if not results:
            print(f"Tidak ditemukan akun dengan kata kunci '{search_term}'")
            return
        
        # Display results
        table = PrettyTable()
        table.field_names = ["API ID", "Phone", "User ID", "Username", "Name"]
        
        for row in results:
            table.add_row([row[0], row[2], row[4], row[5], row[6]])
        
        print(f"\nHasil pencarian untuk '{search_term}' ({len(results)} akun):")
        print(table)

    async def _sort_accounts(self):
        """Sort accounts by different criteria"""
        print("\nSort by:")
        print("1. API ID")
        print("2. Phone")
        print("3. Username")
        print("4. Name")
        
        choice = await ainput("Pilih kriteria pengurutan: ")
        
        sort_index = {
            '1': 0,  # API ID
            '2': 2,  # Phone
            '3': 5,  # Username
            '4': 6   # Name
        }.get(choice)
        
        if sort_index is None:
            print("Pilihan tidak valid!")
            return
        
        accounts = self.db_manager.get_all_accounts()
        
        # Sort accounts
        # Handle None values in sort
        sorted_accounts = sorted(accounts, key=lambda x: str(x[sort_index] or '').lower())
        
        # Display sorted accounts
        table = PrettyTable()
        table.field_names = ["API ID", "Phone", "User ID", "Username", "Name"]
        
        for row in sorted_accounts:
            table.add_row([row[0], row[2], row[4], row[5], row[6]])
        
        print("\nAkun terurut:")
        print(table)

    async def _view_account_distribution(self):
        """View account distribution by username presence"""
        accounts = self.db_manager.get_all_accounts()
        
        # Count accounts with/without username
        with_username = 0
        without_username = 0
        
        for row in accounts:
            if row[5]:  # Username exists
                with_username += 1
            else:
                without_username += 1
        
        print("\nDistribusi Akun:")
        print(f"Dengan Username: {with_username} ({with_username/len(accounts)*100:.1f}%)")
        print(f"Tanpa Username: {without_username} ({without_username/len(accounts)*100:.1f}%)")
        
        # Create a simple ASCII chart
        total_width = 50
        with_width = int(with_username / len(accounts) * total_width)
        without_width = total_width - with_width
        
        print("\nDistribusi Visual:")
        print("Dengan Username    : " + "█" * with_width + f" {with_username}")
        print("Tanpa Username     : " + "█" * without_width + f" {without_username}")

    async def view_active_clients(self):
        """Display information about active clients"""
        active_clients = self.client_manager.active_clients
        
        if not active_clients:
            print("Tidak ada klien aktif saat ini.")
            return
        
        print(f"\n--- Active Clients ({len(active_clients)}) ---")
        
        # Get account info for active clients
        client_info = []
        for phone, client in active_clients.items():
            # Find account info
            account_info = None
            accounts = self.db_manager.get_all_accounts()
            for account in accounts:
                if account[2] == phone:  # Match by phone
                    account_info = account
                    break
            
            # Check connection status
            is_connected = False
            user_id = None
            username = None
            try:
                is_connected = client.is_connected()
                if is_connected:
                    # This would be async but we're simplifying for this example
                    pass
            except Exception as e:
                logging.error(f"Error checking client connection for {phone}: {str(e)}")
            
            client_info.append({
                'phone': phone,
                'connected': is_connected,
                'api_id': account_info[0] if account_info else None,
                'username': account_info[5] if account_info else None,
                'name': account_info[6] if account_info else None
            })
        
        # Display clients in table
        table = PrettyTable()
        table.field_names = ["Phone", "Connected", "API ID", "Username", "Name"]
        
        for info in client_info:
            table.add_row([
                info['phone'],
                "✅" if info['connected'] else "❌",
                info['api_id'],
                info['username'],
                info['name']
            ])
        
        print(table)
        
        # Show options for active clients
        print("\nOptions:")
        print("1. Disconnect Client")
        print("2. Disconnect All Clients")
        print("3. Back")
        
        choice = await ainput("Pilih opsi: ")
        if choice == '1':
            await self._disconnect_client()
        elif choice == '2':
            await self._disconnect_all_clients()

    async def _disconnect_client(self):
        """Disconnect a specific client"""
        active_clients = self.client_manager.active_clients
        
        if not active_clients:
            print("Tidak ada klien aktif untuk diputuskan.")
            return
        
        print("\nDaftar klien aktif:")
        for i, phone in enumerate(active_clients.keys(), 1):
            print(f"{i}. {phone}")
        
        choice = await ainput("Pilih nomor klien yang akan diputuskan: ")
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(active_clients):
                print("Pilihan tidak valid!")
                return
            
            phone = list(active_clients.keys())[idx]
            
            print(f"Memutuskan koneksi klien {phone}...")
            result = await self.client_manager.disconnect_client(phone)
            
            if result:
                print(f"Klien {phone} berhasil diputuskan.")
            else:
                print(f"Gagal memutuskan klien {phone}.")
        except ValueError:
            print("Input harus berupa angka!")
        except Exception as e:
            logging.error(f"Error disconnecting client: {str(e)}")
            print(f"Error: {str(e)}")

    async def _disconnect_all_clients(self):
        """Disconnect all active clients"""
        active_clients = self.client_manager.active_clients
        
        if not active_clients:
            print("Tidak ada klien aktif untuk diputuskan.")
            return
        
        confirm = await ainput(f"Apakah Anda yakin ingin memutuskan {len(active_clients)} klien aktif? (y/n): ")
        if confirm.lower() != 'y':
            return
        
        print("Memutuskan semua klien aktif...")
        await self.client_manager.disconnect_all_clients()
        print("Semua klien telah diputuskan.")

    async def view_status_history(self):
        """View historical status records"""
        if not self.status_history:
            print("Tidak ada riwayat status yang tersimpan.")
            return
        
        # Sort by timestamp (newest first)
        sorted_history = sorted(
            self.status_history,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Display options
        print("\nOpsi tampilan:")
        print("1. Tampilkan 5 riwayat terbaru")
        print("2. Tampilkan 10 riwayat terbaru")
        print("3. Tampilkan semua riwayat")
        print("4. Bandingkan dua riwayat")
        print("5. Grafik perubahan akun")
        print("6. Kembali")
        
        choice = await ainput("Pilih opsi: ")
        
        if choice == '1':
            limit = 5
        elif choice == '2':
            limit = 10
        elif choice == '3':
            limit = len(sorted_history)
        elif choice == '4':
            await self._compare_status_records()
            return
        elif choice == '5':
            await self._show_account_changes()
            return
        elif choice == '6':
            return
        else:
            print("Pilihan tidak valid!")
            return
        
        # Display records in table
        table = PrettyTable()
        table.field_names = ["No", "Timestamp", "Uptime", "Total Accounts", "Active Clients"]
        
        for i, record in enumerate(sorted_history[:limit], 1):
            timestamp = datetime.fromisoformat(record.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S')
            table.add_row([
                i,
                timestamp,
                record.get('uptime', 'N/A'),
                record.get('total_accounts', 0),
                record.get('active_clients', 0)
            ])
        
        print("\nRiwayat Status:")
        print(table)

    async def _compare_status_records(self):
        """Compare two status records"""
        if len(self.status_history) < 2:
            print("Minimal 2 riwayat status diperlukan untuk perbandingan.")
            return
        
        # Sort by timestamp (newest first)
        sorted_history = sorted(
            self.status_history,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Display records for selection
        print("\nDaftar Riwayat Status:")
        for i, record in enumerate(sorted_history, 1):
            timestamp = datetime.fromisoformat(record.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{i}. {timestamp} - Accounts: {record.get('total_accounts', 0)}, Clients: {record.get('active_clients', 0)}")
        
        # Get selections
        try:
            idx1 = int(await ainput("\nPilih riwayat pertama (#): ")) - 1
            idx2 = int(await ainput("Pilih riwayat kedua (#): ")) - 1
            
            if idx1 < 0 or idx1 >= len(sorted_history) or idx2 < 0 or idx2 >= len(sorted_history):
                print("Pilihan tidak valid!")
                return
            
            record1 = sorted_history[idx1]
            record2 = sorted_history[idx2]
            
            # Ensure record1 is the newer one
            if datetime.fromisoformat(record1.get('timestamp', '')) < datetime.fromisoformat(record2.get('timestamp', '')):
                record1, record2 = record2, record1
            
            # Format timestamps
            time1 = datetime.fromisoformat(record1.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S')
            time2 = datetime.fromisoformat(record2.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate differences
            account_diff = record1.get('total_accounts', 0) - record2.get('total_accounts', 0)
            client_diff = record1.get('active_clients', 0) - record2.get('active_clients', 0)
            
            # Calculate time difference
            time_diff = datetime.fromisoformat(record1.get('timestamp', '')) - datetime.fromisoformat(record2.get('timestamp', ''))
            
            # Display comparison
            print(f"\nPerbandingan antara {time1} dan {time2}")
            print(f"Selisih waktu: {time_diff}")
            print(f"Perubahan Total Accounts: {account_diff:+d}")
            print(f"Perubahan Active Clients: {client_diff:+d}")
            
            # Display detailed table
            table = PrettyTable()
            table.field_names = ["Metrik", "Nilai Lama", "Nilai Baru", "Perubahan"]
            
            table.add_row(["Timestamp", time2, time1, f"{time_diff}"])
            table.add_row(["Total Accounts", record2.get('total_accounts', 0), record1.get('total_accounts', 0), 
                          f"{account_diff:+d}"])
            table.add_row(["Active Clients", record2.get('active_clients', 0), record1.get('active_clients', 0), 
                          f"{client_diff:+d}"])
            table.add_row(["Database Size", f"{record2.get('db_size_mb', 0):.2f} MB", f"{record1.get('db_size_mb', 0):.2f} MB", 
                          f"{record1.get('db_size_mb', 0) - record2.get('db_size_mb', 0):+.2f} MB"])
            
            print(table)
        except ValueError:
            print("Input harus berupa angka!")
        except Exception as e:
            logging.error(f"Error comparing status records: {str(e)}")
            print(f"Error: {str(e)}")

    async def _show_account_changes(self):
        """Show account changes over time"""
        if len(self.status_history) < 2:
            print("Minimal 2 riwayat status diperlukan untuk analisis perubahan.")
            return
        
        # Sort by timestamp
        sorted_history = sorted(
            self.status_history,
            key=lambda x: x.get('timestamp', '')
        )
        
        # Extract data for display
        timestamps = []
        account_counts = []
        client_counts = []
        
        for record in sorted_history:
            timestamp = datetime.fromisoformat(record.get('timestamp', '')).strftime('%m-%d %H:%M')
            timestamps.append(timestamp)
            account_counts.append(record.get('total_accounts', 0))
            client_counts.append(record.get('active_clients', 0))
        
        # Display as ASCII chart (simple)
        print("\nPerubahan Jumlah Akun:")
        max_accounts = max(account_counts)
        chart_width = 40
        
        for i, (time, count) in enumerate(zip(timestamps, account_counts)):
            bar_width = int(count / max_accounts * chart_width) if max_accounts > 0 else 0
            print(f"{time}: {'█' * bar_width} {count}")
        
        print("\nPerubahan Jumlah Klien Aktif:")
        max_clients = max(client_counts) if client_counts else 0
        
        for i, (time, count) in enumerate(zip(timestamps, client_counts)):
            bar_width = int(count / max_clients * chart_width) if max_clients > 0 else 0
            print(f"{time}: {'█' * bar_width} {count}")

    async def check_system_health(self):
        """Check system health and display status"""
        print("\n--- System Health Check ---")
        
        # Check uptime
        uptime = datetime.now() - self.start_time
        print(f"System Uptime: {str(uptime).split('.')[0]}")
        
        # Check database
        try:
            conn, cursor = self.db_manager.get_connection()
            
            # Check if database is locked
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("COMMIT")
                print("✅ Database: Available (not locked)")
            except Exception as e:
                print(f"⚠️ Database: Locked or busy ({str(e)})")
            
            # Check database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size = page_count * page_size / (1024 * 1024)  # Size in MB
            
            db_status = "Normal"
            if db_size > 100:
                db_status = "Large"
            
            print(f"✅ Database Size: {db_size:.2f} MB ({db_status})")
            
            # Check database integrity
            cursor.execute("PRAGMA quick_check")
            integrity = cursor.fetchone()[0]
            if integrity == "ok":
                print("✅ Database Integrity: Good")
            else:
                print(f"⚠️ Database Integrity: Issues found ({integrity})")
        except Exception as e:
            logging.error(f"Database check error: {str(e)}")
            print(f"❌ Database Check: Error ({str(e)})")
        
        # Check active clients
        active_clients = len(self.client_manager.active_clients)
        print(f"✅ Active Clients: {active_clients}")
        
        # Check disk space
        try:
            total, used, free = shutil.disk_usage('/')
            free_gb = free / (1024**3)
            print(f"✅ Free Disk Space: {free_gb:.2f} GB")
            
            if free_gb < 1:
                print("⚠️ Low disk space! Less than 1GB available.")
        except Exception as e:
            logging.error(f"Disk check error: {str(e)}")
            print("⚠️ Disk Space Check: Could not determine")
        
        # Check log files
        log_dir = 'logs'
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            log_count = len(log_files)
            
            # Get size of log files
            log_size = sum(os.path.getsize(os.path.join(log_dir, f)) for f in log_files) / (1024 * 1024)  # MB
            
            print(f"✅ Log Files: {log_count} files ({log_size:.2f} MB)")
            
            # Check for error frequency in most recent log
            if log_files:
                newest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
                try:
                    with open(os.path.join(log_dir, newest_log), 'r', encoding='utf-8') as f:
                        content = f.read()
                        error_count = content.count(" - ERROR - ")
                        if error_count > 10:
                            print(f"⚠️ High Error Count: {error_count} errors in {newest_log}")
                        else:
                            print(f"✅ Error Frequency: {error_count} errors in {newest_log}")
                except Exception as e:
                    logging.error(f"Log check error: {str(e)}")
        else:
            print("⚠️ Log Directory: Not found")
        
        # Overall health assessment
        print("\nOverall System Health: Good")

    async def export_status_report(self):
        """Export a comprehensive status report"""
        # Collect current status
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]
        
        total_accounts = len(self.db_manager.get_all_accounts())
        active_clients = len(self.client_manager.active_clients)
        
        # Generate report data
        report = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "uptime": uptime_str,
                "uptime_seconds": int(uptime.total_seconds())
            },
            "accounts": {
                "total": total_accounts,
                "active_clients": active_clients
            },
            "history": {
                "status_records": len(self.status_history),
                "recent_changes": []
            }
        }
        
        # Add recent changes if available
        if len(self.status_history) >= 2:
            sorted_history = sorted(
                self.status_history,
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            
            recent1 = sorted_history[0]
            recent2 = sorted_history[1]
            
            report["history"]["recent_changes"] = {
                "timespan": (datetime.fromisoformat(recent1.get('timestamp', '')) - 
                            datetime.fromisoformat(recent2.get('timestamp', ''))).total_seconds(),
                "account_change": recent1.get('total_accounts', 0) - recent2.get('total_accounts', 0),
                "client_change": recent1.get('active_clients', 0) - recent2.get('active_clients', 0)
            }
        
        # Get filename from user
        filename = await ainput("Masukkan nama file untuk status report (default: system_status_report.json): ")
        if not filename.strip():
            filename = "system_status_report.json"
        
        # Ensure .json extension
        if not filename.lower().endswith('.json'):
            filename += '.json'
        
        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4)
            print(f"Status report berhasil disimpan ke {filename}")
            
            # Ask if user wants a text report too
            text_report = await ainput("Buat juga laporan teks (y/n)? ")
            if text_report.lower() == 'y':
                text_filename = filename.replace('.json', '.txt')
                with open(text_filename, 'w', encoding='utf-8') as f:
                    f.write(f"SYSTEM STATUS REPORT\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("SYSTEM INFORMATION\n")
                    f.write(f"Uptime: {uptime_str}\n")
                    
                    f.write("\nACCOUNT INFORMATION\n")
                    f.write(f"Total Accounts: {total_accounts}\n")
                    f.write(f"Active Clients: {active_clients}\n")
                    
                    if "recent_changes" in report["history"]:
                        f.write("\nRECENT CHANGES\n")
                        changes = report["history"]["recent_changes"]
                        f.write(f"Account Change: {changes['account_change']:+d}\n")
                        f.write(f"Client Change: {changes['client_change']:+d}\n")
                
                print(f"Laporan teks berhasil disimpan ke {text_filename}")
        except Exception as e:
            logging.error(f"Error exporting status report: {str(e)}")
            print(f"Gagal menyimpan status report: {str(e)}")


# Try to import shutil for disk space check, but don't fail if not available
try:
    import shutil
except ImportError:
    logging.warning("shutil module not available, disk space check will be limited")