class ProteinCraftData:
    _instance = None
    _json_string = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_json_string(self):
        return self._json_string

    def set_json_string(self, json_string):
        self._json_string = json_string 