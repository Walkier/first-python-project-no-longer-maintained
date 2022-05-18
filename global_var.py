from datetime import datetime

last_day = None
background_hooked = False

def init_global():
    last_day = datetime.now().day - 1