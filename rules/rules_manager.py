# rules/rules_manager.py
import os
import logging
import json
import random

class RulesManager:
    def __init__(self, rules_file='responder_rules.json'):
        self.rules_file = rules_file
        self.rules = {}
        self._load_rules()
    def _load_rules(self):
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
                self._migrate_rules_format()
            except Exception as e:
                logging.error(f"Error loading rules: {str(e)}")
                self.rules = {}
        else:
            self.rules = {}
            self._save_rules()
    def _migrate_rules_format(self):
        changed = False
        for rule_id, rule in self.rules.items():
            if isinstance(rule.get('response'), str):
                rule['responses'] = [rule['response']]
                del rule['response']
                changed = True
        if changed:
            self._save_rules()
            logging.info("Rules migrated to support multiple responses")
    def _save_rules(self):
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=4)
            logging.debug("Rules saved successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving rules: {str(e)}")
            return False
    def get_all_rules(self):
        return self.rules
    def get_rule(self, rule_id):
        return self.rules.get(rule_id)
    def add_rule(self, keyword, response, private_only=False):
        if not keyword.strip() or not response.strip():
            return False, "Kata kunci dan pesan balasan tidak boleh kosong!"
        rule_id = str(len(self.rules) + 1)
        self.rules[rule_id] = {'keyword': keyword, 'responses': [response], 'private_only': private_only}
        saved = self._save_rules()
        return saved, f"Aturan dengan ID {rule_id} berhasil ditambahkan!" if saved else "Gagal menyimpan aturan!"
    def update_rule(self, rule_id, keyword=None, response=None, private_only=None):
        if rule_id not in self.rules:
            return False, f"Aturan dengan ID {rule_id} tidak ditemukan!"
        rule = self.rules[rule_id]
        if keyword is not None and keyword.strip():
            rule['keyword'] = keyword
        if response is not None and response.strip():
            if 'responses' not in rule:
                rule['responses'] = []
            rule['responses'].append(response)
        if private_only is not None:
            rule['private_only'] = private_only
        saved = self._save_rules()
        return saved, f"Aturan dengan ID {rule_id} berhasil diperbarui!" if saved else "Gagal menyimpan aturan!"
    def delete_rule(self, rule_id):
        if rule_id not in self.rules:
            return False, f"Aturan dengan ID {rule_id} tidak ditemukan!"
        del self.rules[rule_id]
        saved = self._save_rules()
        return saved, f"Aturan dengan ID {rule_id} berhasil dihapus!" if saved else "Gagal menghapus aturan!"
    def delete_response(self, rule_id, response_index):
        if rule_id not in self.rules:
            return False, f"Aturan dengan ID {rule_id} tidak ditemukan!"
        rule = self.rules[rule_id]
        if 'responses' not in rule or not isinstance(rule['responses'], list):
            return False, "Format aturan tidak valid!"
        if response_index < 0 or response_index >= len(rule['responses']):
            return False, f"Indeks respons {response_index} tidak valid!"
        del rule['responses'][response_index]
        if not rule['responses']:
            rule['responses'] = ["Default response"]
        saved = self._save_rules()
        return saved, f"Respons pada indeks {response_index} berhasil dihapus!" if saved else "Gagal menghapus respons!"
    def get_random_response(self, rule_id):
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        responses = rule.get('responses', [])
        if not responses and 'response' in rule:
            return rule['response']
        if not responses:
            return None
        return random.choice(responses)
    def export_rules(self, filename="responder_rules_export.json"):
        if not self.rules:
            return False, "Tidak ada aturan yang dapat diekspor."
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=4)
            return True, f"Berhasil mengekspor {len(self.rules)} aturan ke {filename}"
        except Exception as e:
            logging.error(f"Gagal mengekspor aturan: {str(e)}")
            return False, f"Gagal mengekspor aturan: {str(e)}"
    def import_rules(self, filename="responder_rules_export.json", replace=False):
        if not os.path.exists(filename):
            return False, f"File {filename} tidak ditemukan!"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_rules = json.load(f)
            if not imported_rules:
                return False, "Tidak ada aturan yang dapat diimpor."
            for rule_id, rule in imported_rules.items():
                if 'response' in rule and 'responses' not in rule:
                    rule['responses'] = [rule['response']]
                    del rule['response']
            if replace:
                self.rules = imported_rules
            else:
                highest_id = 0
                for rule_id in self.rules:
                    try:
                        rule_id_int = int(rule_id)
                        if rule_id_int > highest_id:
                            highest_id = rule_id_int
                    except ValueError:
                        pass
                for rule_id, rule in imported_rules.items():
                    if rule_id not in self.rules:
                        self.rules[rule_id] = rule
                    else:
                        highest_id += 1
                        self.rules[str(highest_id)] = rule
            saved = self._save_rules()
            return saved, f"Berhasil mengimpor aturan. Total aturan saat ini: {len(self.rules)}"
        except Exception as e:
            logging.error(f"Gagal mengimpor aturan: {str(e)}")
            return False, f"Gagal mengimpor aturan: {str(e)}"