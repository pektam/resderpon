# Telethon Unlimited Login System

This project is an unlimited login system built using Telethon, providing auto responder functionality, task scheduling, analytics, and more.

## Running the Code

To run the code, use the following command:

```
python main.py
```

Make sure you have the required dependencies installed.

## Directory Structure

The main directories and files in this project are:

- `db/`: Contains the database manager for handling account data persistence.
- `rules/`: Contains the rules manager for handling auto responder rules.
- `telegram/`: Contains Telethon client manager and message handler.
- `ui/`: Contains the user interface components for various system features.
- `utils/`: Contains utility functions.
- `main.py`: The entry point of the application.

## Additional Notes

- The system uses SQLite for storing account data. The database file is located at `accounts/accounts.db`.
- Auto responder rules are loaded from and saved to `responder_rules.json`.
- Logging is set up to write logs to the `logs/` directory with a daily log file.
- The system supports graceful shutdown handling via SIGINT and SIGTERM signals.

Feel free to explore the code and customize it according to your needs. If you encounter any issues or have questions, please refer to the project documentation or reach out for support.
