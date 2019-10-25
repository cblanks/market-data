#!/usr/bin/python
# Filename : mydatetime.py

import datetime
_datetime = datetime.datetime

class mydatetime(_datetime):
    """
    My modified datetime class.
    """
    def __init__(self, year, month, day, *args, **kw):
        _datetime.__init__(self, year, month, day, *args, **kw)
        
    def dayoftheweek(self):
        """
        A method to return the name of the day of the week.
        """
        days_of_the_week = { 0 : "Monday",
                             1 : "Tuesday",
                             2 : "Wednesday",
                             3 : "Thursday",
                             4 : "Friday",
                             5 : "Saturday",
                             6 : "Sunday" }
        
        return days_of_the_week[_datetime.date.weekday()]
