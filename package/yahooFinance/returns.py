#!/usr/bin/python
# Filename : returnsAnalysis.py

# docstrings ----------------------------------------------------
"""
The returns analysis classes of the Yahoo! Finance systematic trading package.

These classes evaluate strategy returns and drawdowns with daily or monthly granularity.
"""

# dependencies
from timeSeriesAnalysis import *
import math

# attributes
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

# classes
class returnsAnalysis(timeSeriesAnalysis):
    """
    An base class for time series analysis of the returns of a trading system.
    """
    # attributes
    analysis_type = "returnsAnalysis"
    
    # protected
    def __init__(self, input_data, granularity="Daily"): # "Monthly"
        """
        The initialisation method.
        """
        self.granularity = granularity
        timeSeriesAnalysis.__init__(self, input_data, input_data.analysis_period, lookback_days=["N/A"])        

    def __csvPath__(self):
        """
        A method to set the csv file path where the analysis results are to be stored. 
        """
        return "%s/%s_%s_%s%s.csv" % ( self.analysis_dir ,
                                       self.input_data.input_data.name ,
                                       self.input_data.name ,
                                       self.granularity ,
                                       self.name )

    def __initialAnalysisPeriod__(self, i=0):
        """
        A method to return the initial period - in trading days - required 
        for the first analysis.
        """
        return 0

    def __setAnalysisPeriod__(self, analysis_period):
        """
        A method to define the analysis time period. If necessary, shorten 
        requested period to available input data.
        """
        return analysis_period 

    def __pruneData__(self, input):
        """
        A method to prune the input data to the desired granularity: Daily or Monthly.
        """
        output = {}
        for key in input.keys(): # fill starting row
            output[key] = [input[key][self.input_data.__initialAnalysisPeriod__()]]
        
        if self.granularity=="Daily":
            for row in xrange(self.input_data.__initialAnalysisPeriod__()+1, len(input["Date"])):
                    for key in input.keys():
                        output[key].append(input[key][row])                
        
        else: # self.granularity=="Monthly"
            for row in xrange(self.input_data.__initialAnalysisPeriod__()+1, len(input["Date"])):
                
                # check for the last day in the data set
                try:
                    the_month_tomorrow = input["Date"][row+1].month
                except IndexError: 
                    for key in input.keys():
                        output[key].append(input[key][row])
            
                # otherwise check for a changing month
                if not the_month_tomorrow==input["Date"][row].month:
                    for key in input.keys():
                        output[key].append(input[key][row])
                
        return output

    # public


class Returns(returnsAnalysis):
    """
    An object to calculate the daily returns of a trading system.
    """
    # attributes
    analysis_type = "Returns"
    
    # protected
    def __init__(self, input_data, granularity="Daily"): # "Monthly"
        """
        The initialisation method.
        """
        returnsAnalysis.__init__(self, input_data, granularity)
        self.__equity__ = input_data.init_equity
        self.__debt__ = 0.0 

    def __setHeaders__(self):
        """
        A method to define the headers of the dataset.
        """
        return ["Date", "Equity", "Debt", "Return"]
    
    def __thisReturn__(self, this_equity, this_debt):
        """
        The method to calculate this return.
        """
        return ( (this_equity-this_debt) / (self.__equity__-self.__debt__) ) - 1.0

    def __calculation__(self, data, i, row):
        """
        The method to calculate the returns.
        """
        this_equity = data[self.input_data.name]["Equity"][row]
        this_debt = data[self.input_data.name]["Debt"][row]
        this_return = self.__thisReturn__(this_equity, this_debt)
        self.__equity__ = this_equity
        self.__debt__ = this_debt
        return [ this_equity, this_debt, this_return ]
               
    # public
    
    
class logReturns(Returns):
    """
    An object to calculate the daily logarithmic returns of a trading system.
    """
    # attributes
    analysis_type = "logReturns"
    
    # protected
    def __init__(self, input_data, granularity="Daily"): # "Monthly"
        """
        The initialisation method.
        """
        Returns.__init__(self, input_data, granularity)
    
    def __thisReturn__(self, this_equity, this_debt):
        """
        The method to calculate this return.
        """
        return math.log( (this_equity-this_debt) / (self.__equity__-self.__debt__) )
               
    # public
    
    
class Drawdowns(returnsAnalysis):
    """
    An object to calculate the fractional drawdowns of a trading system.
    """
    # attributes
    analysis_type = "Drawdowns"
    
    # protected
    def __init__(self, input_data, granularity="Daily"): # "Monthly"
        """
        The initialisation method.
        """
        returnsAnalysis.__init__(self, input_data, granularity)
        self.__peak__ = 0.0

    def __setHeaders__(self):
        """
        A method to define the headers of the dataset.
        """
        return ["Date", "Equity", "Peak", "Drawdown"]
    
    def __calculation__(self, data, i, row):
        """
        The method to calculate the cumulative daily drawdown.
        """
        if data[self.input_data.name]["Equity"][row]>self.__peak__:
            self.__peak__ = data[self.input_data.name]["Equity"][row]

        return [ data[self.input_data.name]["Equity"][row] ,
                 self.__peak__ ,
                 ( self.__peak__ - data[self.input_data.name]["Equity"][row] ) / self.__peak__ ]
               
    # public
    
# end of file
