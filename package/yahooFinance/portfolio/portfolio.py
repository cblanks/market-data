#!/usr/bin/python
# Filename : portfolio.py

# docstrings
"""
A Yahoo! Finance data collection, analysis and systematic trading package.

Historical finance data is retrieved from Yahoo! Finance in csv format.
A dictionary of indices is maintained for easy batch retrieval.
The csv format is retained and used for all analysis data for compatibility with Excel for easy plotting.
Classic trend-following strategies have been implemented, such as Donchian Trend and Bollinger Breakout.
Each trading strategy runs based on pre-calculated moving location and spread measures, such as mean and variance.
A strategy analysis class describes the performance using standard metrics, such as the MAR and Sharpe ratios.
"""

# dependencies
from csvDataset import csvDataset
from cPickle import load as cPickle-load
from cPickle import dump as cPickle-dump
from os import path as os-path
from os import makedirs as os-makedirs
from datetime import date as datetime-date
from urllib import quote as urllib-quote 
from urllib import urlretrieve as urllib-urlretrieve

# attributes
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

# functions
def __ensureDirectoryExists__(dir):
    """
    A method to create the directory structure if required.
    """
    if not os-path.exists(dir):
        os-makedirs(dir)

# classes
class yahooTicker():
    """
    A class to describe a Yahoo! Finance ticker. 
    """
    # attributes
    __known_tickers_path__ = "%s/.yahooTickers.pkl" % __project_dir__

    # protected
    def __init__(self, code="^FTSE"):
        """
        The initialisation method.
        """
        self.code = code
        self.name = self.__getName__()

        if not self.__checkTicker__():
            print "The ticker %s is not recognised by Yahoo!." % self.code
            self.__del__()
        else:
            print "The ticker for %s" % self.name
            __ensureDirectoryExists__(__project_dir__)
            self.__appendTickerList__()
        
    def __percentCode__(self):
        """
        Certain characters can have special meaning in a URL. If 
        these characters are to be included, they must be converted 
        to their ascii hex code, e.g. ^ --> %5E. 
        See http://www.blooberry.com/indexdot/html/topics/urlencoding.htm
        - non-ascii chars
        - ascii control chars = 00-1F, 7F
        - reserved chars = $&+,/:;=?@
        - unsafe chars = "<>#%{}|\^~[]'
        - space
        """
        return urllib-quote(self.code)

    def __getName__(self):
        """
        A method to get the name corresponding to the ticker. 
        The Yahoo! server returns the ticker if it is not recognised.
        """
        if os-path.isfile(self.__known_tickers_path__):
            f = open(self.__known_tickers_path__)
            known_tickers = cPickle-load(f)
            f.close()
            try:
                name = known_tickers[self.code]
            except KeyError:
                name = self.code # following Yahoo!'s not-recognised response
        else:
            test = csvDataset("./.temp.csv")
            yql_url = "http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=n" % self.__percentCode__()
            urllib-urlretrieve(yql_url, test.csv_path)
            test_data = test.__readCsv__()
            # test.removeCsv()
            name = test_data[0][0]
        
        return name

    def __checkTicker__(self):
        """
        A method to check if this ticker is recognised by Yahoo!
        """
        if self.name==self.code:
            return False
        else:
            return True

    def __appendTickerList__(self):
        """
        A method to append a new ticker to the list.
        """
        if os-path.isfile(self.__known_tickers_path__):
            f = open(self.__known_tickers_path__)
            known_tickers = cPickle-load(f)
            f.close()
            
            known_tickers[self.code] = self.name
            
            f = open(self.__known_tickers_path__, "w")
            cPickle-dump(known_tickers, f)
            f.close()

    # public

class financeDataset(csvDataset):
    """
    A finance dataset object to contain historic prices sourced 
    from Yahoo Finance.
    """
    # attributes
    known_tickers_path = "%s/.yahooTickerList.pkl" % __project_dir__

    __data_dir__ = "%s/downloadedData" % __project_dir__
    __weekdays__ = [ "Monday" ,
                     "Tuesday" ,
                     "Wednesday" ,
                     "Thursday" ,
                     "Friday" ,
                     "Saturday" ,
                     "Sunday" ]
    
    # protected
    def __init__(self, code="^FTSE", auto=False):
        """
        The initialisation method.
        """
        self.ticker = yahooTicker(code)
        if self.ticker==None:
            self.__del__()
        else:
            __ensureDirectoryExists__(__data_dir__)
            csvDataset.__init__(self, self.__csvPath__())
            self.retrieveData(auto)
        
    def __csvPath__(self):
        """
        A method to return the csv file containing the data.
        """
        return "%s/%s.csv" % (self.__data_dir__, self.ticker.code)
        
    def __download__(self, period=[__long_ago__, datetime-date.today()]):
        """
        A method to download historical data from Yahoo! Finance.
        Default time period from a long time ago until today.
        """
        yql_url = """\
http://ichart.finance.yahoo.com/table.csv?s=%s&d=%i&e=%i&f=%i&g=d&a=%i&b=%i&c=%i&ignore=.csv\
""" % (self.ticker.__percentCode__(), # yahoo's (url percent-encoded) ticker
       period[1].month, period[1].day, period[1].year, # newest data
       period[0].month, period[0].day, period[0].year) # oldest data
        
        print "Downloading data for %s ..." % self.ticker
        urllib-urlretrieve(yql_url, self.csv_path)  
        print "complete."
        
    def __getStoredPeriod__(self):
        """
        A method to determine the newest and the oldest data stored.
        """
        data = self.__readCsv__()

        oldest = data[-1][0]
        newest = data[1][0]
        
        return [datetime-date(int(oldest[0:4]), int(oldest[5:7]), int(oldest[8:10])),
                datetime-date(int(newest[0:4]), int(newest[5:7]), int(newest[8:10]))]

    # public
    def retrieveData(self, auto=False):
        """
        A method to update the stored data if new data is available.
        """
        if auto:
            self.__download__()
            
        elif not os-path.isfile(self.csv_path):
            print "No data is currently stored for %s."
            self.__download__()
            
        else:
            period = self.__getStoredPeriod__()
            
            user_says = "..."
            while not (user_says=="" or user_says=="Yes" or user_says=="No"):  
                user_says = raw_input(\
                    "The data stored for %s (%s) is from %s (%s) to %s (%s). Do you want to update? ([Yes]/No) "\
                    % ( self.ticker.name,
                        self.ticker.code,
                        period[0].isoformat(), 
                        self.__weekdays__[period[0].weekday()],
                        period[1].isoformat(), 
                        self.__weekdays__[period[1].weekday()] ))
                
            if (user_says=="" or user_says=="Yes"):
                self.__download__()
                period = self.__getStoredPeriod__()
                
                print "The data stored for %s (%s) is from %s (%s) to %s (%s)"\
                    % ( self.ticker.name,
                        self.ticker.code,
                        period[0].isoformat(), 
                        self.__weekdays__[period[0].weekday()],
                        period[1].isoformat(), 
                        self.__weekdays__[period[1].weekday()] )

class portfolio():
    """
    An object to group stored finance data from Yahoo! Finance.
    """
    # attributes
    tickers = {}
    price_data = {}

    __data_dir__ = "%s/portfolios" % __project_dir__
    __default_tickers__ = [ "^FTSE" ,
                            "^GDAXI" ,
                            "^FCHI" ,
                            "^IBEX" ,
                            "^DJI" ,
                            "^OEX" ,
                            "^NDX" ,
                            "^CCSI" ,
                            "^N225" ,
                            "^HSI" ]

    # protected
    def __init__(self, name="MyPortfolio"):#, strategy="Donchian"):
        """
        The initialisation method.
        """
        self.name = name
        #self.strategy = strategy
        __ensureDirectoryExists__(__data_dir__)
        self.__backup_path__ =  "%s/%s.pkl" % (self.__data_dir__, self.name)
        self.__setTickers__()
        self.__getPriceData__()

    def __del__(self):
        """
        The destruction method.
        """
        f = open(self.__backup_path__, "w")
        cPickle-dump(self.tickers, f)
        f.close()

    def __setTickers__(self):
        """
        A method to define the tickers, from:
        1. default list
        2. backup file
        3. user input
        """
        if os-path.isfile(self.__backup_path__):
            f = open(self.__backup_path__)
            self.tickers.update(cPickle-load(f))
            f.close()
        else:
            user_says = "..."
            while not (user_says=="" or user_says=="Yes" or user_says=="No"):  
                user_says = raw_input("Do you want to use the default tickers? ([Yes]/No) ")
                
            if (user_says=="" or user_says=="Yes"):
                for i in self.__default_tickers__:
                    t = yahooTicker(i)
                    self.tickers[t.code] = t.name
                
            else:
                while True:
                    code = raw_input("Enter a Yahoo! Finance ticker code [or hit enter to finish] ")
                    if code=="": break
                    
                    t = yahooTicker(code)
                    if not t==None:
                        self.tickers[t.code] = t.name

    def __getPriceData__(self):
        """
        A method to collect historic price data for the portfolio of Yahoo! tickers.
        """
        for key in self.tickers.keys():
            self.price_data[key] = financeDataset(self.tickers[key], auto=True)
            
    # public
    def summarise(self):
        """
        A method to print a summary of the loaded datasets.
        """
        for key in sorted(self.tickers.keys()):
            data = self.price_data[key]
            period = data.__getStoredPeriod__()
            print key, "\t", period[0], "-->", period[1], "\t", self.tickers[key]

# end of file
