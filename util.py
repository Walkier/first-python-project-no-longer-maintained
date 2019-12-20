from datetime import datetime
import pytz

def format_time(time):
    '''takes datetime.now(), returns formatted string of timezones'''
    local_tz = pytz.timezone("Asia/Hong_Kong")
    time = local_tz.localize(time)

    hkt = datetime.strftime(time.astimezone(pytz.timezone("Asia/Hong_Kong")), "%I:%M %p")
    pdt = datetime.strftime(time.astimezone(pytz.timezone("America/Vancouver")), "%I:%M %p")
    aus = datetime.strftime(time.astimezone(pytz.timezone("Australia/Melbourne")), "%I:%M %p")
    use = datetime.strftime(time.astimezone(pytz.timezone("America/Toronto")), "%I:%M %p")
    ukt = datetime.strftime(time.astimezone(pytz.timezone("Europe/London")), "%I:%M %p")

    return(":flag_ca:: %s | :flag_us:&T: %s | :flag_gb:: %s | :flag_hk:: %s | :flag_au:: %s" % (pdt, use, ukt, hkt, aus))