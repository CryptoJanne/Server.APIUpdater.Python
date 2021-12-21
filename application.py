from timer import ScheduleTimer
from rdbserverlogging import RunTheLogging

asdf = ScheduleTimer(1, RunTheLogging)
asdf.start()