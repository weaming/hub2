import os
from jsonkv import JsonKV

sorted_set = lambda x: sorted(set(list(x)))


class Event:
    def __init__(self, user, chat):
        self.user = user
        self.chat = chat

    @property
    def key(self):
        return f"{self.user.id}|{self.user.username}|{self.chat.id}"

    def __repr__(self):
        return f"<Event: {self.key}>"

    @classmethod
    def parse_key(cls, key: str):
        ids = key.split('|')
        print(key, ids)
        return ids[0], ids[1], ids[2]


class Database:
    def __init__(self,):
        self.db = JsonKV(
            os.getenv('DB_PATH', '/tmp/db.hub2.json'), timeout=10, release_force=True
        )

    @staticmethod
    def init_user_dict(db: JsonKV, key):
        if key not in db.data:
            db[key] = {'topics': []}

    def set_chat_topics(self, key, topics):
        with self.db as db:
            self.init_user_dict(db, key)
            db[key]['topics'] = topics
            return sorted(db[key]['topics'])

    def get_chat_topics(self, key):
        with self.db as db:
            self.init_user_dict(db, key)
            return sorted(db[key]['topics'])

    def add_chat_topics(self, key, topics):
        with self.db as db:
            self.init_user_dict(db, key)
            db[key]['topics'] = list(set(db[key]['topics'] + topics))
            return sorted(db[key]['topics'])

    def remove_chat_topics(self, key, topics):
        with self.db as db:
            self.init_user_dict(db, key)
            db[key]['topics'] = list(set(db[key]['topics']) - set(topics))
            return sorted(db[key]['topics'])

    def clear_chat_topics(self, key):
        with self.db as db:
            self.init_user_dict(db, key)
            db[key]['topics'] = []
            return sorted(db[key]['topics'])

    def get_key_topics_map(self):
        with self.db as db:
            data = db.data
            return {u: v['topics'] for u, v in data.items() if u != 'upstream'}

    def get_all_topics(self):
        topics = []
        map = self.get_key_topics_map()
        for ts in map.values():
            topics += ts
        return sorted_set(topics)

    def get_upstream_topics(self):
        return self.get_chat_topics("upstream")

    def set_upstream_topics(self, topics):
        return self.set_chat_topics("upstream", sorted_set(topics))


DB = Database()
