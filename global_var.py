from datetime import datetime

last_day = None

def init_global():
    last_day = datetime.now().day - 1