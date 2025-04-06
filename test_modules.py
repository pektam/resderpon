# test_modules.py
import asyncio
import logging
import os
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

from core import UnlimitedLoginSystem
from db.database_manager import DatabaseManager
from telegram.client_manager import ClientManager
from rules.rules_manager import RulesManager
from telegram.message_handler import MessageHandler
from utils.helpers import setup_logging
from ui import MainMenu, AccountManagement, AutoResponderMenu, TaskSchedulingMenu, WorkCycleMenu, AnalyticsMenu, StatusMenu

# Konfigurasi Logging untuk Pengujian
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TestModules(unittest.TestCase):

    def setUp(self):
        """Set up untuk setiap pengujian"""
        self.db_path = 'test_accounts.db'  # Database pengujian terpisah
        self.rules_file = 'test_responder_rules.json'  # File aturan pengujian terpisah
        self.test_phone = '6281234567890'  # Nomor telepon untuk pengujian (ganti dengan nomor yang valid)

        # Salin database asli ke database pengujian
        if os.path.exists('accounts/accounts.db'):
            import shutil
            shutil.copy('accounts/accounts.db', self.db_path)
        else:
            # Buat database kosong jika tidak ada
            open(self.db_path, 'a').close()

        # Inisialisasi dengan path pengujian
        self.db_manager = DatabaseManager(db_path=self.db_path)
        self.client_manager = ClientManager()
        self.rules_manager = RulesManager(rules_file=self.rules_file)
        self.message_handler = MessageHandler(self.rules_manager)
        self.system = UnlimitedLoginSystem()

        # Inisialisasi UI (beberapa mungkin memerlukan mocking input)
        # self.account_manager = AccountManagement(self.db_manager, self.client_manager) # Dipindahkan ke dalam pengujian
        self.auto_responder_menu = AutoResponderMenu(self.rules_manager, self.client_manager, self.message_handler)
        self.task_scheduling_menu = TaskSchedulingMenu()
        self.work_cycle_menu = WorkCycleMenu()
        self.analytics_menu = AnalyticsMenu(self.db_manager, self.client_manager)
        self.status_menu = StatusMenu(self.db_manager, self.client_manager)
        self.main_menu = MainMenu(None, self.auto_responder_menu, self.task_scheduling_menu, self.work_cycle_menu, self.analytics_menu, self.status_menu) # AccountManager di set None

    def tearDown(self):
        """Membersihkan setelah setiap pengujian"""
        self.db_manager._close_connection()
        # Hapus file pengujian
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.rules_file):
            os.remove(self.rules_file)

    @patch('telegram.client_manager.TelegramClient', new_callable=MagicMock)
    @patch('aioconsole.ainput', side_effect=['123', 'hash123', 'testcode'])  # Urutan input yang benar
    def test_account_management_add_account_mocked(self, mock_ainput, mock_telegram_client):
        """Menguji penambahan akun dengan mocking TelegramClient"""
        try:
            # Konfigurasi mock TelegramClient
            mock_client_instance = AsyncMock()
            mock_client_instance.connect.return_value = None
            mock_client_instance.is_user_authorized.return_value = False  # Set ke False untuk pengujian
            mock_client_instance.send_code_request.return_value = None
            mock_client_instance.sign_in.return_value = None
            mock_client_instance.get_me.return_value = AsyncMock(id=1, username='testuser', first_name='Test')
            mock_client_instance.disconnect.return_value = None
            mock_telegram_client = MagicMock(return_value=mock_client_instance) # Perbaikan mock telegram client

            async def test_add_account():
                print("Mocking aioconsole.ainput")
                # Inisialisasi AccountManagement di dalam pengujian
                account_manager = AccountManagement(self.db_manager, self.client_manager)
                print("Sebelum account_manager.add_account()") # Tambahkan ini
                await account_manager.add_account()
                print("Setelah account_manager.add_account()") # Tambahkan ini
                count = self.db_manager.count_accounts()
                self.assertEqual(count, 1)

            asyncio.run(test_add_account())
            logging.info("Pengujian AccountManagement add_account berhasil (mocked Telegram)")
        except Exception as e:
            logging.error(f"Pengujian AccountManagement add_account gagal (mocked Telegram): {str(e)}")
            self.fail(f"Pengujian AccountManagement add_account gagal (mocked Telegram): {str(e)}")

    @patch('telegram.client_manager.TelegramClient', new_callable=MagicMock)
    def test_client_manager_create_client_mocked(self, mock_telegram_client):
        """Menguji pembuatan klien dengan mocking TelegramClient"""
        try:
            # Konfigurasi mock TelegramClient
            mock_client_instance = AsyncMock()
            mock_client_instance.connect.return_value = None
            mock_client_instance.disconnect.return_value = None
            mock_telegram_client.return_value = mock_client_instance

            async def test_create_client():
                client = await self.client_manager.create_client(123, 'hash123', '1234567890')
                self.assertIsNotNone(client)
                self.assertTrue(mock_client_instance.connect.called)
                self.assertTrue(mock_client_instance.disconnect.called)

            asyncio.run(test_create_client())
            logging.info("Pengujian ClientManager create_client berhasil (mocked Telegram)")
        except Exception as e:
            logging.error(f"Pengujian ClientManager create_client gagal (mocked Telegram): {str(e)}")
            self.fail(f"Pengujian ClientManager create_client gagal (mocked Telegram): {str(e)}")

    @patch('telegram.client_manager.TelegramClient', new_callable=MagicMock)
    @patch('aioconsole.ainput', side_effect=['testcode'])
    async def test_client_manager_authorize_client_mocked(self, mock_ainput, mock_telegram_client):
        """Menguji otorisasi klien dengan mocking TelegramClient"""
        try:
            # Konfigurasi mock TelegramClient
            mock_client_instance = AsyncMock()
            mock_client_instance.connect.return_value = None
            mock_client_instance.is_user_authorized.return_value = False
            mock_client_instance.send_code_request.return_value = None
            mock_client_instance.sign_in.return_value = None
            mock_client_instance.get_me.return_value = AsyncMock(id=1, username='testuser', first_name='Test')
            mock_client_instance.disconnect.return_value = None
            mock_telegram_client.return_value = mock_client_instance

            # Buat instance ClientManager
            client_manager = ClientManager()

            # Buat klien
            client = await client_manager.create_client(123, 'hash123', self.test_phone)

            # Otorisasi klien
            me = await client_manager.authorize_client(client, self.test_phone)

            self.assertIsNotNone(me)
            self.assertEqual(me.username, 'testuser')
            logging.info("Pengujian ClientManager authorize_client berhasil (mocked Telegram)")
        except Exception as e:
            logging.error(f"Pengujian ClientManager authorize_client gagal (mocked Telegram): {str(e)}")
            self.fail(f"Pengujian ClientManager authorize_client gagal (mocked Telegram): {str(e)}")

    def test_database_manager_add_get_delete(self):
        """Menguji fungsi-fungsi dasar DatabaseManager (add, get, delete)"""
        try:
            # Tambah akun
            self.db_manager.add_account(123, 'hash123', '1234567890', 'twofa', 1, 'testuser', 'Test User')
            # Ambil akun
            account = self.db_manager.get_account_by_api_id(123)
            self.assertIsNotNone(account)
            self.assertEqual(account[2], '1234567890')
            # Hapus akun
            self.db_manager.delete_account(123)
            account = self.db_manager.get_account_by_api_id(123)
            self.assertIsNone(account)
            logging.info("Pengujian DatabaseManager (add, get, delete) berhasil")
        except Exception as e:
            logging.error(f"Pengujian DatabaseManager (add, get, delete) gagal: {str(e)}")
            self.fail(f"Pengujian DatabaseManager (add, get, delete) gagal: {str(e)}")

    def test_database_manager_count_accounts(self):
        """Menguji fungsi count_accounts"""
        try:
            # Tambah beberapa akun
            self.db_manager.add_account(123, 'hash123', '1234567890', 'twofa', 1, 'testuser1', 'Test User 1')
            self.db_manager.add_account(456, 'hash456', '0987654321', 'twofa', 2, 'testuser2', 'Test User 2')
            # Hitung akun
            count = self.db_manager.count_accounts()
            self.assertEqual(count, 2)
            # Hapus akun
            self.db_manager.delete_account(123)
            self.db_manager.delete_account(456)
            logging.info("Pengujian DatabaseManager count_accounts berhasil")
        except Exception as e:
            logging.error(f"Pengujian DatabaseManager count_accounts gagal: {str(e)}")
            self.fail(f"Pengujian DatabaseManager count_accounts gagal: {str(e)}")

    def test_rules_manager_add_get_delete(self):
        """Menguji fungsi-fungsi dasar RulesManager (add, get, delete)"""
        try:
            # Tambah aturan
            success, message = self.rules_manager.add_rule('testkeyword', 'testresponse')
            self.assertTrue(success)
            # Ambil aturan
            rules = self.rules_manager.get_all_rules()
            self.assertIn('1', rules)
            self.assertEqual(rules['1']['keyword'], 'testkeyword')
            # Hapus aturan
            self.rules_manager.delete_rule('1')
            rules = self.rules_manager.get_all_rules()
            self.assertNotIn('1', rules)
            logging.info("Pengujian RulesManager (add, get, delete) berhasil")
        except Exception as e:
            logging.error(f"Pengujian RulesManager (add, get, delete) gagal: {str(e)}")
            self.fail(f"Pengujian RulesManager (add, get, delete) berhasil")

    def test_rules_manager_update_rule(self):
        """Menguji fungsi update_rule"""
        try:
            # Tambah aturan
            self.rules_manager.add_rule('testkeyword', 'testresponse')
            # Edit aturan
            success, message = self.rules_manager.update_rule('1', keyword='newkeyword', response='newresponse', private_only=True)
            self.assertTrue(success)
            rules = self.rules_manager.get_all_rules()
            self.assertEqual(rules['1']['keyword'], 'newkeyword')
            self.assertEqual(rules['1']['responses'], ['testresponse', 'newresponse'])
            self.assertTrue(rules['1']['private_only'])
            # Hapus aturan
            self.rules_manager.delete_rule('1')
            logging.info("Pengujian RulesManager update_rule berhasil")
        except Exception as e:
            logging.error(f"Pengujian RulesManager update_rule gagal: {str(e)}")
            self.fail(f"Pengujian RulesManager update_rule gagal: {str(e)}")

    @patch('aioconsole.ainput', side_effect=['testtask', 'testcommand', '0.1'])
    def test_task_scheduling_menu_add_task(self, mock_ainput):
        """Menguji fungsi add_task"""
        try:
            async def test_add_task():
                await self.task_scheduling_menu.add_task()
                self.assertEqual(len(self.task_scheduling_menu.scheduled_tasks), 1)
            asyncio.run(test_add_task())
            logging.info("Pengujian TaskSchedulingMenu add_task berhasil")
        except Exception as e:
            logging.error(f"Pengujian TaskSchedulingMenu add_task gagal: {str(e)}")
            self.fail(f"Pengujian TaskSchedulingMenu add_task gagal: {str(e)}")

    @patch('aioconsole.ainput', side_effect=['1'])
    def test_task_scheduling_menu_delete_task(self, mock_ainput):
        """Menguji fungsi delete_task"""
        try:
            async def test_delete_task():
                # Tambah tugas terlebih dahulu
                with patch('aioconsole.ainput', side_effect=['testtask', 'testcommand', '0.1']):
                    await self.task_scheduling_menu.add_task()
                # Hapus tugas
                await self.task_scheduling_menu.delete_task()
                self.assertEqual(len(self.task_scheduling_menu.scheduled_tasks), 0)
            asyncio.run(test_delete_task())
            logging.info("Pengujian TaskSchedulingMenu delete_task berhasil")
        except Exception as e:
            logging.error(f"Pengujian TaskSchedulingMenu delete_task gagal: {str(e)}")
            self.fail(f"Pengujian TaskSchedulingMenu delete_task gagal: {str(e)}")

    def test_work_cycle_menu_start_stop(self):
        """Menguji fungsi start dan stop dari WorkCycleMenu"""
        try:
            async def test_work_cycle():
                # Mulai siklus kerja
                await self.work_cycle_menu.start_work_cycle()
                self.assertIsNotNone(self.work_cycle_menu.work_cycle_task)

                # Hentikan siklus kerja
                await self.work_cycle_menu.stop_work_cycle()
                self.assertTrue(self.work_cycle_menu.work_cycle_task.done())

            asyncio.run(test_work_cycle())
            logging.info("Pengujian WorkCycleMenu start/stop berhasil")
        except Exception as e:
            logging.error(f"Pengujian WorkCycleMenu start/stop gagal: {str(e)}")
            self.fail(f"Pengujian WorkCycleMenu start/stop berhasil")

    @patch('aioconsole.ainput', side_effect=['test_daily.json', 'test_weekly.json', 'test_monthly.json'])
    def test_analytics_menu_export(self, mock_ainput):
        """Menguji fungsi-fungsi export dari AnalyticsMenu"""
        try:
            async def test_analytics():
                # Ekspor analitik harian
                await self.analytics_menu.export_daily_analytics()
                self.assertTrue(os.path.exists('test_daily.json'))
                os.remove('test_daily.json')

                # Ekspor analitik mingguan
                await self.analytics_menu.export_weekly_analytics()
                self.assertTrue(os.path.exists('test_weekly.json'))
                os.remove('test_weekly.json')

            asyncio.run(test_analytics())
            logging.info("Pengujian AnalyticsMenu export berhasil")
        except Exception as e:
            logging.error(f"Pengujian AnalyticsMenu export gagal: {str(e)}")
            self.fail(f"Pengujian AnalyticsMenu export gagal: {str(e)}")

    def test_status_menu_view(self):
        """Menguji fungsi-fungsi view dari StatusMenu"""
        try:
            async def test_status():
                # Lihat status sistem
                await self.status_menu.view_system_status() # Hanya memastikan tidak error

                # Lihat statistik akun
                await self.status_menu.view_account_statistics() # Hanya memastikan tidak error

            asyncio.run(test_status())
            logging.info("Pengujian StatusMenu view berhasil")
        except Exception as e:
            logging.error(f"Pengujian StatusMenu view gagal: {str(e)}")
            self.fail(f"Pengujian StatusMenu view gagal: {str(e)}")

if __name__ == '__main__':
    unittest.main()