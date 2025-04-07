# ui/analytics.py
import asyncio
import logging
import json
import csv
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time

from aioconsole import ainput
from prettytable import PrettyTable

class AnalyticsMenu:
    def __init__(self, db_manager, client_manager):
        self.db_manager = db_manager
        self.client_manager = client_manager
        self.analytics_dir = 'analytics'
        self.charts_dir = os.path.join(self.analytics_dir, 'charts')
        self._setup_folders()
        self.analytics_data = self._load_analytics_data()

    def _setup_folders(self):
        """Set up necessary folders for analytics"""
        os.makedirs(self.analytics_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)

    def _load_analytics_data(self):
        """Load previous analytics data if available"""
        data_file = os.path.join(self.analytics_dir, 'analytics_history.json')
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading analytics data: {str(e)}")
        
        # Return empty data structure if file doesn't exist or has an error
        return {
            "daily": {},
            "weekly": {},
            "monthly": {},
            "last_updated": None
        }

    def _save_analytics_data(self):
        """Save analytics data to file"""
        data_file = os.path.join(self.analytics_dir, 'analytics_history.json')
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics_data, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving analytics data: {str(e)}")
            return False

    def _collect_current_analytics(self):
        """Collect current analytics data from the system"""
        timestamp = datetime.now().isoformat()
        
        # Get account statistics
        accounts = self.db_manager.get_all_accounts()
        account_count = len(accounts)
        active_clients = len(self.client_manager.active_clients)
        
        # Collect additional metrics
        data = {
            "timestamp": timestamp,
            "total_accounts": account_count,
            "active_clients": active_clients,
            "system_uptime": time.time() - psutil.boot_time() if psutil_available else 0,
        }
        
        # Update history data
        today = datetime.now().strftime('%Y-%m-%d')
        current_week = datetime.now().strftime('%Y-W%W')
        current_month = datetime.now().strftime('%Y-%m')
        
        # Daily data
        if today not in self.analytics_data["daily"]:
            self.analytics_data["daily"][today] = []
        self.analytics_data["daily"][today].append(data)
        
        # Weekly data
        if current_week not in self.analytics_data["weekly"]:
            self.analytics_data["weekly"][current_week] = []
        self.analytics_data["weekly"][current_week].append(data)
        
        # Monthly data
        if current_month not in self.analytics_data["monthly"]:
            self.analytics_data["monthly"][current_month] = []
        self.analytics_data["monthly"][current_month].append(data)
        
        # Update last updated timestamp
        self.analytics_data["last_updated"] = timestamp
        
        # Save data
        self._save_analytics_data()
        
        return data

    def _generate_chart(self, data_points, title, ylabel, filename):
        """Generate chart from data points"""
        x_values = []
        y_values = []
        
        for point in data_points:
            if isinstance(point, dict):
                # If data point is a dictionary with timestamp and value
                try:
                    timestamp = datetime.fromisoformat(point.get('timestamp', '')).strftime('%H:%M')
                    value = point.get('total_accounts', 0)  # Change this to the field you want to plot
                    x_values.append(timestamp)
                    y_values.append(value)
                except (ValueError, AttributeError):
                    continue
            elif isinstance(point, tuple) and len(point) == 2:
                # If data point is a tuple of (label, value)
                x_values.append(point[0])
                y_values.append(point[1])
        
        if not x_values or not y_values:
            return None
            
        # Create a chart
        plt.figure(figsize=(10, 6))
        plt.plot(x_values, y_values, marker='o')
        plt.title(title)
        plt.xlabel('Time')
        plt.ylabel(ylabel)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart
        chart_path = os.path.join(self.charts_dir, filename)
        plt.savefig(chart_path)
        plt.close()
        
        return chart_path

    async def export_analytics_menu(self):
        """UI for export analytics menu"""
        while True:
            print("\nExport Analytics Menu")
            print("1. Collect Current Analytics")
            print("2. Export Daily Analytics")
            print("3. Export Weekly Analytics")
            print("4. Export Monthly Analytics")
            print("5. Generate Analytics Charts")
            print("6. View Analytics Dashboard")
            print("7. Kembali ke Menu Utama")
            choice = await ainput("Pilih menu: ")
            
            if choice == '1':
                await self.collect_analytics()
            elif choice == '2':
                await self.export_daily_analytics()
            elif choice == '3':
                await self.export_weekly_analytics()
            elif choice == '4':
                await self.export_monthly_analytics()
            elif choice == '5':
                await self.generate_analytics_charts()
            elif choice == '6':
                await self.view_analytics_dashboard()
            elif choice == '7':
                break
            else:
                print("Pilihan tidak valid!")

    async def collect_analytics(self):
        """Collect current analytics data"""
        try:
            print("Mengumpulkan data analitik terbaru...")
            data = self._collect_current_analytics()
            
            print("\nData berhasil dikumpulkan:")
            print(f"Timestamp: {datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Akun: {data['total_accounts']}")
            print(f"Klien Aktif: {data['active_clients']}")
            
            print("\nData telah disimpan.")
        except Exception as e:
            logging.error(f"Error collecting analytics: {str(e)}")
            print(f"Gagal mengumpulkan data analitik: {str(e)}")

    async def export_daily_analytics(self):
        """Export daily analytics data to a JSON file"""
        try:
            # Collect current data before exporting
            self._collect_current_analytics()
            
            today = datetime.now().strftime('%Y-%m-%d')
            today_data = self.analytics_data["daily"].get(today, [])
            
            if not today_data:
                print("Tidak ada data harian untuk diekspor.")
                return
            
            # Prepare export data
            export_data = {
                "date": today,
                "data_points": len(today_data),
                "analytics": today_data,
                "summary": {
                    "total_accounts": today_data[-1]["total_accounts"] if today_data else 0,
                    "active_clients": today_data[-1]["active_clients"] if today_data else 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            # Get filename from user
            filename = await ainput("Masukkan nama file untuk daily analytics (default: daily_analytics.json): ")
            if not filename.strip():
                filename = "daily_analytics.json"
            
            # Ensure .json extension
            if not filename.lower().endswith('.json'):
                filename += '.json'
            
            # Save to file
            filepath = os.path.join(self.analytics_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            
            print(f"Daily analytics berhasil diekspor ke {filepath}.")
            
            # Ask if CSV export is also needed
            csv_export = await ainput("Ekspor juga sebagai CSV? (y/n): ")
            if csv_export.lower() == 'y':
                csv_filename = filename.replace('.json', '.csv')
                csv_filepath = os.path.join(self.analytics_dir, csv_filename)
                
                with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(['Timestamp', 'Total Accounts', 'Active Clients'])
                    
                    # Write data
                    for point in today_data:
                        writer.writerow([
                            datetime.fromisoformat(point['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                            point['total_accounts'],
                            point['active_clients']
                        ])
                
                print(f"Daily analytics berhasil diekspor ke CSV: {csv_filepath}")
        except Exception as e:
            logging.error(f"Gagal mengekspor daily analytics: {str(e)}")
            print(f"Gagal mengekspor daily analytics: {str(e)}")

    async def export_weekly_analytics(self):
        """Export weekly analytics data to a JSON file"""
        try:
            # Collect current data before exporting
            self._collect_current_analytics()
            
            current_week = datetime.now().strftime('%Y-W%W')
            week_data = self.analytics_data["weekly"].get(current_week, [])
            
            if not week_data:
                print("Tidak ada data mingguan untuk diekspor.")
                return
            
            # Calculate daily averages
            daily_data = {}
            for point in week_data:
                day = datetime.fromisoformat(point['timestamp']).strftime('%Y-%m-%d')
                if day not in daily_data:
                    daily_data[day] = {
                        'total_accounts': [],
                        'active_clients': []
                    }
                daily_data[day]['total_accounts'].append(point['total_accounts'])
                daily_data[day]['active_clients'].append(point['active_clients'])
            
            daily_averages = {}
            for day, metrics in daily_data.items():
                daily_averages[day] = {
                    'avg_total_accounts': sum(metrics['total_accounts']) / len(metrics['total_accounts']),
                    'avg_active_clients': sum(metrics['active_clients']) / len(metrics['active_clients']),
                    'max_total_accounts': max(metrics['total_accounts']),
                    'max_active_clients': max(metrics['active_clients'])
                }
            
            # Prepare export data
            export_data = {
                "week": current_week,
                "data_points": len(week_data),
                "daily_averages": daily_averages,
                "analytics": week_data,
                "summary": {
                    "total_accounts": week_data[-1]["total_accounts"] if week_data else 0,
                    "active_clients": week_data[-1]["active_clients"] if week_data else 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            # Get filename from user
            filename = await ainput("Masukkan nama file untuk weekly analytics (default: weekly_analytics.json): ")
            if not filename.strip():
                filename = "weekly_analytics.json"
            
            # Ensure .json extension
            if not filename.lower().endswith('.json'):
                filename += '.json'
            
            # Save to file
            filepath = os.path.join(self.analytics_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            
            print(f"Weekly analytics berhasil diekspor ke {filepath}.")
        except Exception as e:
            logging.error(f"Gagal mengekspor weekly analytics: {str(e)}")
            print(f"Gagal mengekspor weekly analytics: {str(e)}")

    async def export_monthly_analytics(self):
        """Export monthly analytics data to a JSON file"""
        try:
            # Collect current data before exporting
            self._collect_current_analytics()
            
            current_month = datetime.now().strftime('%Y-%m')
            month_data = self.analytics_data["monthly"].get(current_month, [])
            
            if not month_data:
                print("Tidak ada data bulanan untuk diekspor.")
                return
            
            # Calculate weekly averages
            weekly_data = {}
            for point in month_data:
                date = datetime.fromisoformat(point['timestamp'])
                week = date.strftime('%Y-W%W')
                if week not in weekly_data:
                    weekly_data[week] = {
                        'total_accounts': [],
                        'active_clients': []
                    }
                weekly_data[week]['total_accounts'].append(point['total_accounts'])
                weekly_data[week]['active_clients'].append(point['active_clients'])
            
            weekly_averages = {}
            for week, metrics in weekly_data.items():
                weekly_averages[week] = {
                    'avg_total_accounts': sum(metrics['total_accounts']) / len(metrics['total_accounts']),
                    'avg_active_clients': sum(metrics['active_clients']) / len(metrics['active_clients']),
                    'max_total_accounts': max(metrics['total_accounts']),
                    'max_active_clients': max(metrics['active_clients'])
                }
            
            # Prepare export data
            export_data = {
                "month": current_month,
                "data_points": len(month_data),
                "weekly_averages": weekly_averages,
                "analytics": month_data,
                "summary": {
                    "total_accounts": month_data[-1]["total_accounts"] if month_data else 0,
                    "active_clients": month_data[-1]["active_clients"] if month_data else 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            # Get filename from user
            filename = await ainput("Masukkan nama file untuk monthly analytics (default: monthly_analytics.json): ")
            if not filename.strip():
                filename = "monthly_analytics.json"
            
            # Ensure .json extension
            if not filename.lower().endswith('.json'):
                filename += '.json'
            
            # Save to file
            filepath = os.path.join(self.analytics_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            
            print(f"Monthly analytics berhasil diekspor ke {filepath}.")
        except Exception as e:
            logging.error(f"Gagal mengekspor monthly analytics: {str(e)}")
            print(f"Gagal mengekspor monthly analytics: {str(e)}")

    async def generate_analytics_charts(self):
        """Generate various analytics charts"""
        try:
            # Collect current data
            self._collect_current_analytics()
            
            print("Generating analytics charts...")
            charts_generated = 0
            
            # Get daily data for today
            today = datetime.now().strftime('%Y-%m-%d')
            today_data = self.analytics_data["daily"].get(today, [])
            
            if today_data:
                # Generate daily account chart
                chart_path = self._generate_chart(
                    today_data,
                    f"Daily Account Statistics - {today}",
                    "Number of Accounts",
                    f"daily_accounts_{today}.png"
                )
                if chart_path:
                    print(f"Generated daily account chart: {chart_path}")
                    charts_generated += 1
            
            # Get weekly data
            current_week = datetime.now().strftime('%Y-W%W')
            week_data = self.analytics_data["weekly"].get(current_week, [])
            
            if week_data:
                # Transform data for weekly chart - one point per day
                daily_averages = {}
                for point in week_data:
                    day = datetime.fromisoformat(point['timestamp']).strftime('%Y-%m-%d')
                    if day not in daily_averages:
                        daily_averages[day] = {'total_accounts': [], 'active_clients': []}
                    daily_averages[day]['total_accounts'].append(point['total_accounts'])
                    daily_averages[day]['active_clients'].append(point['active_clients'])
                
                chart_data = []
                for day, metrics in sorted(daily_averages.items()):
                    chart_data.append((
                        day,
                        sum(metrics['total_accounts']) / len(metrics['total_accounts'])
                    ))
                
                # Generate weekly account chart
                chart_path = self._generate_chart(
                    chart_data,
                    f"Weekly Account Statistics - {current_week}",
                    "Average Number of Accounts",
                    f"weekly_accounts_{current_week.replace(':', '_')}.png"
                )
                if chart_path:
                    print(f"Generated weekly account chart: {chart_path}")
                    charts_generated += 1
            
            # Get monthly data
            current_month = datetime.now().strftime('%Y-%m')
            month_data = self.analytics_data["monthly"].get(current_month, [])
            
            if month_data:
                # Transform data for monthly chart - one point per week
                weekly_averages = {}
                for point in month_data:
                    date = datetime.fromisoformat(point['timestamp'])
                    week = date.strftime('%Y-W%W')
                    if week not in weekly_averages:
                        weekly_averages[week] = {'total_accounts': [], 'active_clients': []}
                    weekly_averages[week]['total_accounts'].append(point['total_accounts'])
                    weekly_averages[week]['active_clients'].append(point['active_clients'])
                
                chart_data = []
                for week, metrics in sorted(weekly_averages.items()):
                    chart_data.append((
                        week,
                        sum(metrics['total_accounts']) / len(metrics['total_accounts'])
                    ))
                
                # Generate monthly account chart
                chart_path = self._generate_chart(
                    chart_data,
                    f"Monthly Account Statistics - {current_month}",
                    "Average Number of Accounts",
                    f"monthly_accounts_{current_month}.png"
                )
                if chart_path:
                    print(f"Generated monthly account chart: {chart_path}")
                    charts_generated += 1
            
            if charts_generated == 0:
                print("Tidak ada data yang cukup untuk menghasilkan grafik.")
            else:
                print(f"Berhasil menghasilkan {charts_generated} grafik di folder {self.charts_dir}")
        except Exception as e:
            logging.error(f"Error generating analytics charts: {str(e)}")
            print(f"Gagal menghasilkan grafik analitik: {str(e)}")

    async def view_analytics_dashboard(self):
        """View a simple analytics dashboard in the console"""
        try:
            # Collect current data
            current_data = self._collect_current_analytics()
            
            print("\n==== ANALYTICS DASHBOARD ====")
            print(f"Timestamp: {datetime.fromisoformat(current_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Accounts: {current_data['total_accounts']}")
            print(f"Active Clients: {current_data['active_clients']}")
            
            # Show historical data
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            today_data = self.analytics_data["daily"].get(today, [])
            yesterday_data = self.analytics_data["daily"].get(yesterday, [])
            
            if today_data:
                # Calculate day statistics
                today_start = None
                for point in today_data:
                    if not today_start:
                        today_start = point
                
                if today_start:
                    print("\n--- Today's Changes ---")
                    account_change = current_data['total_accounts'] - today_start['total_accounts']
                    print(f"Account Change: {account_change:+d}")
                    client_change = current_data['active_clients'] - today_start['active_clients']
                    print(f"Active Client Change: {client_change:+d}")
            
            if yesterday_data:
                # Get the last data point from yesterday
                yesterday_end = yesterday_data[-1]
                print("\n--- Yesterday vs Today ---")
                account_change = current_data['total_accounts'] - yesterday_end['total_accounts']
                print(f"Account Change: {account_change:+d}")
                client_change = current_data['active_clients'] - yesterday_end['active_clients']
                print(f"Active Client Change: {client_change:+d}")
            
            # Show recent charts if available
            print("\n--- Recent Charts ---")
            chart_files = [f for f in os.listdir(self.charts_dir) if f.endswith('.png')]
            
            if chart_files:
                for chart_file in sorted(chart_files, reverse=True)[:3]:  # Show 3 most recent charts
                    print(f"- {chart_file} ({os.path.join(self.charts_dir, chart_file)})")
            else:
                print("No charts available. Generate charts first.")
            
            print("\n=============================")
        except Exception as e:
            logging.error(f"Error displaying analytics dashboard: {str(e)}")
            print(f"Gagal menampilkan dasbor analitik: {str(e)}")


# Try to import psutil for system metrics, but don't fail if it's not available
try:
    import psutil
    psutil_available = True
except ImportError:
    psutil_available = False