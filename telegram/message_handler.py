# telegram/message_handler.py
import asyncio
import logging
import time
import random

from telethon import events

class MessageHandler:
    def __init__(self, rules_manager):
        self.rules_manager = rules_manager
        self.message_queues = {}
        self.handlers = {}
        self.delays = {}
        self.last_responses = {}
        self.last_response_times = {}
    def setup_handler(self, client, phone, delay_seconds=0.5):
        self.delays[phone] = delay_seconds
        self.last_responses[phone] = {}
        self.last_response_times[phone] = time.time()
        self.message_queues[phone] = asyncio.Queue()
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                if not hasattr(event, 'message') or not hasattr(event.message, 'text'):
                    return
                message_text = event.message.text
                if not message_text:
                    return
                is_private = event.is_private
                should_respond = False
                rule_matched = None
                for rule_id, rule in self.rules_manager.get_all_rules().items():
                    private_only = rule.get('private_only', False)
                    if private_only and not is_private:
                        continue
                    if rule['keyword'].lower() in message_text.lower():
                        should_respond = True
                        rule_matched = rule_id
                        all_responses = rule.get('responses', [])
                        if not all_responses and 'response' in rule:
                            all_responses = [rule['response']]
                        if len(all_responses) <= 1:
                            response_text = all_responses[0] if all_responses else ""
                        else:
                            recent_responses = self.last_responses.get(phone, {}).get(rule_id, [])
                            available_responses = [r for r in all_responses if r not in recent_responses]
                            if not available_responses:
                                available_responses = all_responses
                            response_text = random.choice(available_responses)
                            if rule_id not in self.last_responses.get(phone, {}):
                                self.last_responses[phone][rule_id] = []
                            self.last_responses[phone][rule_id].append(response_text)
                            if len(self.last_responses[phone][rule_id]) > 2:
                                self.last_responses[phone][rule_id].pop(0)
                        break
                if should_respond and rule_matched and response_text:
                    current_time = time.time()
                    time_since_last = current_time - self.last_response_times.get(phone, 0)
                    extra_delay = 0
                    if time_since_last < 30:
                        extra_delay = random.uniform(10, 40)
                    await self.message_queues[phone].put({'event': event, 'response': response_text, 'rule_id': rule_matched, 'extra_delay': extra_delay})
            except Exception as e:
                logging.error(f"Error handling message: {str(e)}")
        self.handlers[phone] = handle_new_message
        asyncio.create_task(self._process_message_queue(phone))
    async def _process_message_queue(self, phone):
        if phone not in self.message_queues:
            return
        queue = self.message_queues[phone]
        base_delay_seconds = self.delays.get(phone, 0.5)
        while phone in self.message_queues:
            try:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                event = item['event']
                response = item['response']
                rule_id = item['rule_id']
                extra_delay = item.get('extra_delay', 0)
                delay_variation = random.uniform(0.5, 1.5)
                actual_delay = base_delay_seconds * delay_variation + extra_delay
                logging.info(f"Phone {phone}: Waiting {actual_delay:.2f}s before responding (base: {base_delay_seconds:.2f}s, extra: {extra_delay:.2f}s)")
                await asyncio.sleep(actual_delay)
                typing_duration = min(len(response) / 5, 10)
                typing_duration *= random.uniform(0.8, 1.2)
                async with event.client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(typing_duration)
                await asyncio.sleep(0.5)
                await event.respond(response)
                logging.info(f"Auto respond to {event.sender_id} with rule {rule_id} (delay: {actual_delay:.2f}s, typing: {typing_duration:.2f}s)")
                self.last_response_times[phone] = time.time()
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error processing message queue: {str(e)}")
                await asyncio.sleep(1)
    def remove_handler(self, phone):
        if phone in self.handlers:
            del self.handlers[phone]
        if phone in self.message_queues:
            del self.message_queues[phone]
        if phone in self.delays:
            del self.delays[phone]
        if phone in self.last_responses:
            del self.last_responses[phone]
        if phone in self.last_response_times:
            del self.last_response_times[phone]