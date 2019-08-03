import os
from jsonkv import JsonKV


class Database:
    def __init__(self,):
        self.db = JsonKV(
            os.getenv('DB_PATH', '/tmp/db.hub2.json'), timeout=10, release_force=True
        )

    @staticmethod
    def init_user_dict(db: JsonKV, chat_id):
        if chat_id not in db.data:
            db[chat_id] = {'topics': []}

    def set_chat_topics(self, chat_id, topics):
        with self.db as db:
            self.init_user_dict(db, chat_id)
            db[chat_id]['topics'] = topics
            return sorted(db[chat_id]['topics'])

    def get_chat_topics(self, chat_id):
        with self.db as db:
            self.init_user_dict(db, chat_id)
            return sorted(db[chat_id]['topics'])

    def add_chat_topics(self, chat_id, topics):
        with self.db as db:
            self.init_user_dict(db, chat_id)
            db[chat_id]['topics'] = list(set(db[chat_id]['topics'] + topics))
            return sorted(db[chat_id]['topics'])

    def remove_chat_topics(self, chat_id, topics):
        with self.db as db:
            self.init_user_dict(db, chat_id)
            db[chat_id]['topics'] = list(set(db[chat_id]['topics']) - set(topics))
            return sorted(db[chat_id]['topics'])

    def clear_chat_topics(self, chat_id):
        with self.db as db:
            self.init_user_dict(db, chat_id)
            db[chat_id]['topics'] = []
            return sorted(db[chat_id]['topics'])

    def get_user_topics_map(self):
        with self.db as db:
            data = db.data
            return {u: v['topics'] for u, v in data.items()}

    def get_all_topics(self):
        topics = []
        map = self.get_user_topics_map()
        for ts in map.values():
            topics += ts
        return sorted(topics)


DB = Database()
