import json
import configparser
from enum import Enum


class Pref(Enum):
    USER = 1
    BOT = 2
    CUSTOM = 3

    def set_pref(pref: str):
        match pref.lower():
            case 'user':
                return Pref.USER
            case 'bot':
                return Pref.BOT
            case _:
                return None

class ConfigManager():
    def __init__(self, settings_path: str = './configs/settings.json') -> None:
        f = open(settings_path)
        config = json.load(f)
        f.close()

        self.client_config_path = config['Client']['path'] + config['Client']['Settings']['in_game_path']
        client_config = configparser.ConfigParser()
        client_config.read(self.client_config_path)
        self.client_config = client_config
        user_pref = configparser.ConfigParser()
        user_pref.read(config["Client"]["Settings"]["user_preferences"])
        self.user_pref = user_pref
        bot_pref = configparser.ConfigParser()
        bot_pref.read(config["Client"]["Settings"]["bot_preferences"])
        self.bot_pref = bot_pref

    def active(self) -> Pref:
        is_user = True
        for section in self.user_pref.sections():
            for option in self.user_pref[section]:
                if self.user_pref[section][option] != self.client_config[section][option]:
                    is_user = False
                    break

        is_bot = True
        for section in self.bot_pref.sections():
            for option in self.bot_pref[section]:
                if self.bot_pref[section][option] != self.client_config[section][option]:
                    is_bot = False
                    break

        if is_user:
            return Pref.USER
        elif is_bot:
            return Pref.BOT
        else:
            return Pref.CUSTOM

    def change_config(self, template: Pref) -> None:
        if template is Pref.USER:
            conf = self.user_pref
        elif template is Pref.BOT:
            conf = self.bot_pref
        else:
            raise ValueError('Currently this template is not supported.')

        for section in conf.sections():
            for option in conf[section]:
                if conf[section][option] != self.client_config[section][option]:
                    self.client_config[section][option] = conf[section][option]
        
    def save(self) -> None:
        with open(self.client_config_path,'w') as cf:
            self.client_config.write(cf)

