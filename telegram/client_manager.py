# telegram/client_manager.py
import os
import logging

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, RPCError

class ClientManager:
    def __init__(self):
        self.active_clients = {}
        os.makedirs('session', exist_ok=True)
    async def create_client(self, api_id, api_hash, phone, default_2fa=None):
        client = None
        try:
            client = TelegramClient(f'session/{phone}', api_id, api_hash)
            await client.connect()
            return client
        except Exception as e:
            logging.error(f"Error creating client for {phone}: {str(e)}")
            if client and client.is_connected():
                await client.disconnect()
            raise
    async def authorize_client(self, client, phone, default_2fa=None, code_callback=None):
        try:
            if not await client.is_user_authorized():
                try:
                    await client.send_code_request(phone)
                    code = await code_callback() if code_callback else input("Masukkan kode yang diterima: ")
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    if default_2fa:
                        await client.sign_in(password=default_2fa)
                    else:
                        password = input("Masukkan password 2FA: ")
                        await client.sign_in(password=password)
            me = await client.get_me()
            return me
        except Exception as e:
            logging.error(f"Error authorizing client for {phone}: {str(e)}")
            raise
    async def test_connection(self, client, phone):
        try:
            if not client.is_connected():
                await client.connect()
            is_authorized = await client.is_user_authorized()
            return {'phone': phone, 'status': 'Berhasil' if is_authorized else 'Gagal', 'error': None}
        except RPCError as e:
            return {'phone': phone, 'status': 'Gagal', 'error': str(e)}
        except Exception as e:
            return {'phone': phone, 'status': 'Error', 'error': str(e)}
    def add_active_client(self, phone, client):
        self.active_clients[phone] = client
    def remove_active_client(self, phone):
        if phone in self.active_clients:
            del self.active_clients[phone]
    async def disconnect_client(self, phone):
        if phone in self.active_clients:
            client = self.active_clients[phone]
            if client and client.is_connected():
                await client.disconnect()
            self.remove_active_client(phone)
            return True
        return False
    async def disconnect_all_clients(self):
        for phone, client in list(self.active_clients.items()):
            try:
                if client and client.is_connected():
                    await client.disconnect()
            except Exception as e:
                logging.error(f"Error disconnecting client {phone}: {str(e)}")
            finally:
                self.remove_active_client(phone)