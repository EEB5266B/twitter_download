import os
import pickle

class cache_gen():

    def __init__(self, user_media_url) -> None:
        self.cache_data = set(user_media_url)

    def __del__(self):
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache_data, f)

    def add(self, element):
        self.cache_data.add(element)

    def is_present(self, element):
        if element in self.cache_data:
            return False
        else:
            self.add(element)
            return True


