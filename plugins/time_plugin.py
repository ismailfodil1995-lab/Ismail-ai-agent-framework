import datetime

from plugins.registry import register


def tool_time():
    return datetime.datetime.now().strftime("%H:%M:%S")


def tool_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


register("time", tool_time)
register("date", tool_date)