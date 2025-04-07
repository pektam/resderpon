
**Dokumentasi Proyek: Telethon Unlimited Login System**

**1. Tujuan:**

Sistem ini bertujuan untuk menyediakan platform yang fleksibel dan mudah digunakan untuk mengelola beberapa akun Telegram, mengotomatiskan respons pesan, dan menjadwalkan tugas.

**2. Struktur Direktori:**

```
/
├── core.py          # Definisi kelas utama UnlimitedLoginSystem
├── main.py          # Titik masuk aplikasi, inisialisasi dan menjalankan sistem
├── db/
│   ├── __init__.py  # Membuat direktori sebagai package
│   └── database_manager.py  # Kelas DatabaseManager
├── telegram/
│   ├── __init__.py  # Membuat direktori sebagai package
│   ├── client_manager.py  # Kelas ClientManager
│   └── message_handler.py # Kelas MessageHandler
├── rules/
│   ├── __init__.py  # Membuat direktori sebagai package
│   └── rules_manager.py   # Kelas RulesManager
├── ui/
│   ├── __init__.py             # Membuat direktori sebagai package
│   ├── main_menu.py            # Menangani menu utama
│   ├── account_management.py   # Menangani penambahan, daftar, pengujian, penghapusan, pembaruan, ekspor, dan impor akun
│   ├── auto_responder.py       # Menangani semua fungsi auto responder
│   ├── task_scheduling.py      # Menangani penjadwalan tugas
│   ├── work_cycle.py           # Menangani siklus kerja harian
│   ├── analytics.py            # Menangani ekspor analitik
│   └── status.py               # Menangani tampilan status dan statistik
└── utils/
    ├── __init__.py  # Membuat direktori sebagai package
    └── helpers.py     # Fungsi-fungsi pembantu (misalnya, setup logging)
```

**3. Deskripsi Modul:**

*   **`core.py`:**
    *   Berisi definisi kelas `UnlimitedLoginSystem`.
    *   Bertindak sebagai *blueprint* untuk sistem.
    *   Tidak berisi inisialisasi atau logika shutdown.

*   **`main.py`:**
    *   Titik masuk utama aplikasi.
    *   Menginisialisasi semua komponen sistem (database, klien Telegram, aturan, UI).
    *   Menangani shutdown aplikasi secara bersih.
    *   Menggunakan `asyncio` untuk menjalankan aplikasi secara asinkron.

*   **`db/database_manager.py`:**
    *   Mengelola koneksi ke database SQLite.
    *   Menyediakan fungsi untuk membuat, membaca, memperbarui, dan menghapus akun.
    *   Menangani migrasi skema database.
    *   Menangani kesalahan koneksi dan query dengan mekanisme retry.

*   **`telegram/client_manager.py`:**
    *   Mengelola pembuatan dan otorisasi klien Telegram.
    *   Menyimpan klien yang aktif.
    *   Menyediakan fungsi untuk memutuskan koneksi klien.

*   **`rules/rules_manager.py`:**
    *   Mengelola aturan respons otomatis.
    *   Memuat dan menyimpan aturan dari/ke file JSON.
    *   Menyediakan fungsi untuk menambah, memperbarui, menghapus, dan mengekspor/impor aturan.

*   **`telegram/message_handler.py`:**
    *   Menangani pesan masuk dari Telegram.
    *   Mencari aturan yang cocok berdasarkan kata kunci dalam pesan.
    *   Mengirim respons otomatis berdasarkan aturan yang cocok.
    *   Mengelola delay respons untuk menghindari pemblokiran.

*   **`ui/` (Semua file di direktori ini):**
    *   Menyediakan antarmuka pengguna berbasis teks untuk berinteraksi dengan sistem.
    *   Setiap file di direktori ini mewakili bagian menu yang berbeda.
    *   Menggunakan `aioconsole` untuk input/output asinkron.
    *   Menggunakan `prettytable` untuk menampilkan data dalam format tabel.

*   **`utils/helpers.py`:**
    *   Berisi fungsi-fungsi utilitas umum, seperti `setup_logging()`.

**4. Cara Menggunakan Setiap Modul:**

*   **`db/database_manager.py`:**

    ```python
    from db.database_manager import DatabaseManager

    db_manager = DatabaseManager(db_path='accounts/accounts.db')
    # Tambah akun
    db_manager.add_account(api_id=12345, api_hash='your_api_hash', phone='+6281234567890', twofa=None, user_id=None, username=None, name='John Doe')
    # Ambil semua akun
    accounts = db_manager.get_all_accounts()
    ```

*   **`telegram/client_manager.py`:**

    ```python
    from telegram.client_manager import ClientManager

    client_manager = ClientManager()
    # Buat klien Telegram
    client = await client_manager.create_client(api_id=12345, api_hash='your_api_hash', phone='+6281234567890')
    # Otorisasi klien
    me = await client_manager.authorize_client(client, phone='+6281234567890')
    ```

*   **`rules/rules_manager.py`:**

    ```python
    from rules.rules_manager import RulesManager

    rules_manager = RulesManager(rules_file='responder_rules.json')
    # Tambah aturan
    rules_manager.add_rule(keyword='halo', response='Hai juga!')
    # Ambil semua aturan
    rules = rules_manager.get_all_rules()
    ```

*   **`telegram/message_handler.py`:**

    ```python
    from telegram.message_handler import MessageHandler
    from rules.rules_manager import RulesManager
    from telegram.client_manager import ClientManager

    # Pastikan rules_manager dan client_manager sudah diinisialisasi
    rules_manager = RulesManager()
    client_manager = ClientManager()

    message_handler = MessageHandler(rules_manager)
    # Buat klien Telegram (pastikan sudah diotorisasi)
    client = await client_manager.create_client(api_id=12345, api_hash='your_api_hash', phone='+6281234567890')
    # Setup handler pesan
    message_handler.setup_handler(client, phone='+6281234567890')

    # Pastikan klien tetap berjalan (misalnya, dengan asyncio.Future())
    ```

*   **`ui/` (Semua file di direktori ini):**
    *   Kelas-kelas UI diinisialisasi dan digunakan di `main.py`.
    *   Tidak perlu menggunakannya secara langsung di luar `main.py`.

*   **`utils/helpers.py`:**

    ```python
    from utils.helpers import setup_logging

    setup_logging() # Panggil di awal program untuk mengatur logging
    ```

**5. Cara Menjalankan Aplikasi:**

1.  Pastikan Anda telah menginstal semua dependensi yang diperlukan (misalnya, `telethon`, `aioconsole`, `prettytable`).
2.  Konfigurasi API ID dan API HASH Telegram Anda.
3.  Jalankan `main.py`:

    ```bash
    python main.py
    ```

**6. Cara Berkontribusi:**

1.  Fork repositori ini.
2.  Buat branch baru untuk fitur atau perbaikan bug Anda.
3.  Tulis kode Anda.
4.  Tulis unit test untuk kode Anda.
5.  Jalankan semua unit test untuk memastikan tidak ada yang rusak.
6.  Buat pull request ke branch `main`.

**7. Panduan Gaya Kode:**

*   Gunakan PEP 8 untuk gaya kode Python.
*   Gunakan type hints untuk meningkatkan keterbacaan.
*   Tulis docstring untuk semua fungsi dan kelas.
*   Tulis unit test untuk semua kode baru.

**8. Catatan Penting:**

*   **Keamanan:** Simpan API ID dan API HASH Anda dengan aman. Jangan pernah mempostingnya di tempat umum.
*   **Rate Limiting:** Telegram memiliki batas laju (rate limiting). Pastikan kode Anda tidak melanggar batas ini.
*   **Autentikasi 2FA:** Sistem ini mendukung autentikasi 2 faktor. Pastikan Anda menangani autentikasi 2 faktor dengan benar.
*   **Error Handling:** Tambahkan penanganan kesalahan yang komprehensif untuk mencegah aplikasi crash.

**9. Peningkatan yang Mungkin:**

*   **GUI:** Buat antarmuka pengguna grafis (GUI) untuk aplikasi.
*   **Database:** Gunakan database yang lebih kuat seperti PostgreSQL atau MySQL.
*   **Testing:** Tambahkan lebih banyak unit test untuk meningkatkan cakupan kode.
*   **Konfigurasi:** Gunakan file konfigurasi (misalnya, `config.ini` atau `config.yaml`) untuk menyimpan pengaturan aplikasi.
*   **Logging:** Tingkatkan konfigurasi logging untuk memberikan informasi yang lebih berguna.

**Contoh Penggunaan di `main.py` (Diperluas):**

```python
# main.py (bagian terkait inisialisasi dan shutdown)
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
    try:
        db_manager = DatabaseManager()
        logging.info("Database manager initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize DatabaseManager: {e}")
        return # Hentikan program jika database gagal

    try:
        client_manager = ClientManager()
        logging.info("Client manager initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize ClientManager: {e}")
        db_manager._close_connection() # Tutup koneksi database sebelum keluar
        return

    try:
        rules_manager = RulesManager()
        logging.info("Rules manager initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize RulesManager: {e}")
        db_manager._close_connection()
        await client_manager.disconnect_all_clients()
        return

    try:
        message_handler = MessageHandler(rules_manager)
        logging.info("Message handler initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize MessageHandler: {e}")
        db_manager._close_connection()
        await client_manager.disconnect_all_clients()
        return

    system = UnlimitedLoginSystem() # Meskipun minimal, instance tetap dibuat

    # Membuat instance dari setiap menu UI
    account_manager = AccountManagement(db_manager, client_manager)
    auto_responder_menu = AutoResponderMenu(rules_manager, client_manager, message_handler)
    task_scheduling_menu = TaskSchedulingMenu()
    work_cycle_menu = WorkCycleMenu()
    analytics_menu = AnalyticsMenu(db_manager, client_manager)
    status_menu = StatusMenu(db_manager, client_manager)

    # Membuat instance dari MainMenu dan memberikan dependensi
    ui = MainMenu(account_manager, auto_responder_menu, task_scheduling_menu,
                  work_cycle_menu, analytics_menu, status_menu)

    loop = asyncio.get_event_loop()

    async def shutdown():
        logging.info("Shutting down...")
        try:
            await client_manager.disconnect_all_clients()
            logging.info("All clients disconnected.")
        except Exception as e:
            logging.error(f"Error disconnecting clients: {e}")

        try:
            db_manager._close_connection()
            logging.info("Database connection closed.")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
        logging.info("Program shutdown complete.")

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
        logging.info("Program shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
```

**Poin-Poin Tambahan:**

*   **Penanganan Kegagalan Inisialisasi:** Contoh `main.py` yang diperbarui menunjukkan cara menangani kegagalan selama inisialisasi komponen. Jika sebuah komponen gagal diinisialisasi, program akan keluar dengan aman, menutup koneksi database dan memutuskan koneksi klien Telegram.
*   **Peningkatan Logging:** Pesan log yang lebih deskriptif ditambahkan untuk memberikan informasi yang lebih baik tentang apa yang terjadi selama inisialisasi dan shutdown.
*   **Urutan Shutdown:** Urutan shutdown dijamin dengan menutup koneksi klien Telegram *sebelum* menutup koneksi database.

Dokumentasi ini harus memberikan dasar yang kuat bagi pengembang lain untuk memahami, menggunakan, dan berkontribusi pada proyek Anda. Ingatlah untuk terus memperbarui dokumentasi ini seiring dengan perkembangan proyek Anda.