import time,datetime


def time2timestamp(year,month,date,hour=0,minute=0,second=0):
    datetime_time = datetime.datetime(int(year),int(month),int(date),int(hour),int(minute),int(second))
    timestamp = time.mktime(datetime_time.timetuple())
    return timestamp

def timestamp2time(timestamp):
    dateArray = datetime.datetime.fromtimestamp(int(timestamp))
    otherStyleTime = dateArray.strftime("%Y-%m-%d %H:%M:%S")
    return otherStyleTime
def timestamp2datetime(timestamp):
    dateArray = datetime.datetime.utcfromtimestamp(int(timestamp))
    return dateArray

def datetime2timestamp(dt):
    return time.mktime(dt.timetuple())

def timedeltahandler(days=0,hours=0,minutes=0,seconds=0):
    current_time = datetime.datetime.now()
    calc_time = current_time - datetime.timedelta(days=days,hours=hours,minutes=minutes,seconds=seconds)
    return datetime2timestamp(calc_time)
    
def currenttimestamp():
    now = datetime.datetime.now()
    return datetime2timestamp(now)