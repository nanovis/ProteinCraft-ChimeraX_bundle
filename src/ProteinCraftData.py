from enum import Enum

class BondDetailType(Enum):
    CA = "CA"
    ATOM = "ATOM"
    AUTO = "AUTO"

class ProteinCraftData:
    _instance = None
    _json_string = None
    _bond_detail = BondDetailType.AUTO
    # Default chain colors
    CHAIN_A_COLOR = "#816DF9"
    CHAIN_B_COLOR = "#FB8686"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_json_string(self):
        return self._json_string

    def set_json_string(self, json_string):
        self._json_string = json_string

    def get_bond_detail(self):
        return self._bond_detail

    def set_bond_detail(self, bond_detail):
        if isinstance(bond_detail, BondDetailType):
            self._bond_detail = bond_detail
        else:
            raise ValueError("bond_detail must be a BondDetailType enum value") 