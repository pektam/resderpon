# main.py
import asyncio
import logging
import signal

from core import UnlimitedLoginSystem
from db.database_manager import DatabaseManager
from telegram.client_manager import ClientManager
from rules.rules_manager import RulesManager
from telegram.message_handler import MessageHandler
from ui import MainMenu, AccountManagement, AutoResponderMenu, TaskSchedulingMenu, WorkCycleMenu, AnalyticsMenu, StatusMenu
from utils.helpers import setup_logging

async def main():
    setup_logging()  # Inisialisasi logging

    # Inisialisasi sistem
    db_manager = DatabaseManager()
    client_manager = ClientManager()
    rules_manager = RulesManager()
    message_handler = MessageHandler(rules_manager)
    system = UnlimitedLoginSystem() # Meskipun minimal, instance tetap dibuat

    # Membuat instance dari setiap menu UI
    account_manager = AccountManagement(db_manager, client_manager)
    auto_responder_menu = AutoResponderMenu(rules_manager, client_manager, message_handler, db_manager)
    task_scheduling_menu = TaskSchedulingMenu()
    work_cycle_menu = WorkCycleMenu()
    analytics_menu = AnalyticsMenu(db_manager, client_manager)
    status_menu = StatusMenu(db_manager, client_manager)

    # Membuat instance dari MainMenu dan memberikan dependensi
    ui = MainMenu(account_manager, auto_responder_menu, task_scheduling_menu,
                  work_cycle_menu, analytics_menu, status_menu)

    loop = asyncio.get_event_loop()

    async def shutdown():
        await client_manager.disconnect_all_clients()
        db_manager._close_connection()
        logging.info("Program shutdown complete")

    def shutdown_handler(signame):
        logging.info(f"Received signal {signame}. Shutting down...")
        asyncio.create_task(shutdown())
        loop.stop()

    for signame in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(getattr(signal, signame), lambda: shutdown_handler(signame))
        except NotImplementedError:
            pass

    try:
        await ui.display_main_menu()
    except asyncio.CancelledError:
        logging.info("Program canceled")
    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        await shutdown()
        logging.info("Program shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)