import configparser
import os

class Config(object):
    ini_file = None
    config = None

    def __init__(self, ini_file):
        conf = configparser.ConfigParser()

        # copy sample if init_file not exists
        if not os.path.exists(ini_file):
            init_sample_path = '{}.sample'.format(ini_file)
            with open(init_sample_path, encoding='utf-8') as f:
                sample_data = f.read()
                f.close()
                with open(ini_file, 'w', encoding='utf-8') as f_init:
                    f_init.write(sample_data)
                    f_init.close()

        conf.read(ini_file, encoding='utf-8')
        self.conf = conf
        self.ini_file = ini_file

    def get_config(self):
        ret = {}
        for section in self.conf.sections():
            ret[section] = {}
            for i, v in self.conf.items(section):
                ret[section][i] = v
        return ret

    def set_config(self, section, option, value):
        if section:
            if option and value == '':
                self.conf.remove_option(section, option)
            elif value:
                self.conf.set(section, option, value)

            with open(self.ini_file, 'w', encoding='utf-8') as configfile:
                self.conf.write(configfile)

        return self.get_config()
