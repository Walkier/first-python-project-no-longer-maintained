import os
import json
import logging
from typing import List
from PrivateVals import PrivateValsV1 as PrivateVals

class GlobalDict:
    def __init__(self, filename, default_data: dict, folder='savefiles/', on_load=None, on_save=None, persistent=True):   
        #callback signature, mutate data, then return bool
        def __always_true(data) -> bool:
            return True

        self.data = default_data
        self.filename = filename
        self.folder = folder
        self.__on_load = on_load if on_load else __always_true #after load function callback
        self.__on_save = on_save if on_save else __always_true #before load function callback
        self.persistent = persistent

    def load_data(self) -> bool:
        if self.persistent:
            try:
                with open(os.path.join(self.folder, self.filename)) as f:
                    self.data = json.loads(f.read())
                    return self.__on_load(self.data)
            except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
                print('{} load failed {}'.format(self.filename, e))
            
            return False
        else:
            return True

    def save_data(self):
        if self.persistent:
            if self.__on_save(self.data):
                try:
                    with open(os.path.join(self.folder, self.filename), 'w') as f:
                        f.write(json.dumps(self.data))
                        return True
                except Exception as e:
                    logging.warning('{} save failed {}'.format(self.filename, e))

            return False
        else:
            return True

class GlobalStateManager:
    def __init__(self, vars: List[GlobalDict]):
        self.vars = {}
        self.data = {}

        for var in vars:
            name = var.filename.split('.')[0]
            self.vars[name] = var

    #for adding more GlobalDicts pass init 
    def add_var(self, var: GlobalDict):
        self.vars[var.filename.split('.')[0]] = var

    #called once to load all stuff from file
    def load_all(self):
        for key, var in self.vars.items():
            var.load_data()
            self.data[key] = var.data
    
    #called once to save all stuff to file
    def save_all(self):
        for var in self.vars.values():
            var.save_data()
