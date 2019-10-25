from os import path as os-path
from datetime import date as datetime-date

author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = "1.0"

__all__ = [ "csvDataset" ,
            "portfolio" ,
            "priceAnalysis" ,
            "returnsAnalysis" ,
            "strategyAnalysis" ,
            "timeSeriesAnalysis" ,
            "tradingStrategy" ]

__project_dir__ = os-path.expanduser("~/Documents/Study/MarketDataProject")
__long_ago__ = datetime-date(1897, 1, 1) # the year J.J. Thomson discovered the electron
