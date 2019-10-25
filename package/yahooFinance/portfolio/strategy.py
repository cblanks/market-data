#!/usr/bin/python
# Filename : tradingStrategy.py

# docstrings
"""
The trading strategy classes of the Yahoo! Finance systematic trading package.

Classic trend-following strategies have been implemented, such as Donchian Trend and Bollinger Breakout.
Each trading strategy runs based on pre-calculated moving location and spread measures, such as mean and variance.
"""

# dependencies
from timeSeriesAnalysis import *
from priceAnalysis import *
import datetime
import math
import ROOT

# attributes
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

__long_ago__ = datetime.date(1897, 1, 1) # the year J.J. Thomson discovered the electron. 

# classes
class tradingSystem(timeSeriesAnalysis):
    """
    A base class to describe a generic trading system.
    """
    # attributes
    analysis_type = "tradingSystem"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0):
        """
        The initialisation method.
        """
        timeSeriesAnalysis.__init__(self, input_data, analysis_period)
        self.init_equity = equity
        self.equity = self.init_equity
        self.debt = 0.0
        self.__position__ = 0 # 1 = Long, -1 = Short
        self.__stop__ = 0.0
    
    def __setHeaders__(self):
        """
        A method to define the headers of the dataset.
        """
        return ["Date", "Position", "Equity", "Debt"]
               
    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        return False # to be specified for each system

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        return False # to be specified for each system

    def __setLongStop__(self, data, row):
        """
        The method to calculate the stop for a new Long position.
        """
        return 0.0 # to be specified for each system

    def __setShortStop__(self, data, row):
        """
        The method to calculate the stop for a new Short position.
        """
        return 0.0 # to be specified for each system

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        return False # to be specified for each system
        
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        return False # to be specified for each system

    def __calculation__(self, data, i, row):
        """
        Method to implement the trading strategy.
        """
        # update fund value
        close = data[self.input_data.name]["Close"][row]
        previous_close = data[self.input_data.name]["Close"][row-1]
        this_return = self.__position__*( close - previous_close )/previous_close
        self.equity *= ( 1 + this_return )
        
        # update debt value
        if self.equity<0.0:
            self.debt += (-1.0*self.equity)
            self.debt += self.init_equity
            self.equity = self.init_equity

        # exit positions
        if self.__position__==1:
            if self.__exitLong__(data, row):
                self.__position__ = 0

        elif self.__position__==-1:
            if self.__exitShort__(data, row):
                self.__position__ = 0
        
        # enter positions
        if self.__position__==0:
            if self.__goLong__(data, row):
                self.__position__ = 1
                self.__stop__ = self.__setLongStop__(data, row)

            elif self.__goShort__(data, row):
                self.__position__ = -1
                self.__stop__ = self.__setShortStop__(data, row)

        return [self.__position__, self.equity, self.debt]


class Hold(tradingSystem):
    """
    A class to describe continuing investment in a security.
    """
    # attributes
    analysis_type = "Hold"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0):
        """
        The initialisation method.
        """
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __initialAnalysisPeriod__(self, i=0):
        """
        A method to return the initial period - in trading days - required 
        for the first analysis.
        """
        return 0

    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        return True
    

class DualMA(tradingSystem):
    """
    A class to describe the Dual Moving Average trading system.
    """
    # attributes
    analysis_type = "DualMovingAverage"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, ma_lookback=[100, 300]):
        """
        The initialisation method.
        """
        self.ma_lookback = ma_lookback
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : EWMA(self.input_data, self.analysis_period, self.ma_lookback) }

    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        ma_newer = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_older = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        close = data[self.input_data.name]["Close"][row]

        enter = ma_newer>ma_older

        return enter

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        ma_newer = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_older = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        close = data[self.input_data.name]["Close"][row]

        enter = ma_newer<ma_older

        return enter

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        return self.__goShort__(data, row)
        
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        return self.__goLong__(data, row)
        

class TripleMA(tradingSystem):
    """
    A class to describe the Triple Moving Average trading system.
    """
    # attributes
    analysis_type = "TripleMovingAverage"
               
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, ma_lookback=[150, 250, 350]):
        """
        The initialisation method.
        """
        self.ma_lookback = ma_lookback
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : EWMA(self.input_data, self.analysis_period, self.ma_lookback) }

    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        ma_newest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_middle = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        ma_oldest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[2])][row]
        close = data[self.input_data.name]["Close"][row]

        enter = ma_newest>ma_middle
        filter = ma_newest>ma_oldest and ma_middle>ma_oldest

        return enter and filter

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        ma_newest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_middle = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        ma_oldest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[2])][row]
        close = data[self.input_data.name]["Close"][row]

        enter = ma_newest<ma_middle
        filter = ma_newest<ma_oldest and ma_middle<ma_oldest
        
        return enter and filter

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        ma_newest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_middle = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        ma_oldest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[2])][row]
        close = data[self.input_data.name]["Close"][row]

        exit = ma_newest<ma_middle
        filter = ma_newest<ma_oldest or ma_middle<ma_oldest

        return exit or filter
        
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        ma_newest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_middle = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        ma_oldest = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[2])][row]
        close = data[self.input_data.name]["Close"][row]

        exit = ma_newest>ma_middle
        filter = ma_newest>ma_oldest or ma_middle>ma_oldest

        return exit or filter
        

class Donchian(tradingSystem):
    """
    A class to describe the Donchian Trend trading system.
    """
    # attributes
    analysis_type = "Donchian"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, ma_lookback=[25, 350], min_lookback=[10, 20], max_lookback=[10, 20], atr_lookback=[20], atr_stop=2.0):
        """
        The initialisation method.
        """
        self.ma_lookback = ma_lookback
        self.min_lookback = min_lookback
        self.max_lookback = max_lookback
        self.atr_lookback = atr_lookback
        self.atr_stop = atr_stop
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : EWMA(self.input_data, self.analysis_period, self.ma_lookback) ,
                 "mmin" : MMIN(self.input_data, self.analysis_period, self.min_lookback) ,
                 "mmax" : MMAX(self.input_data, self.analysis_period, self.max_lookback) ,
                 "atr" : EWATR(self.input_data, self.analysis_period, self.atr_lookback) }
        
    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        ma_newer = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_older = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        mmax_older = data["mmax"]["%s_%i" % (self.preliminary_analyses["mmax"].analysis_type, self.max_lookback[1])][row]
        close = data[self.input_data.name]["Close"][row]

        filter = ma_newer>ma_older
        enter = close>mmax_older

        return filter and enter

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        ma_newer = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_older = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        mmin_older = data["mmin"]["%s_%i" % (self.preliminary_analyses["mmin"].analysis_type, self.min_lookback[1])][row]
        close = data[self.input_data.name]["Close"][row]

        filter = ma_newer<ma_older
        enter = close<mmin_older

        return filter and enter

    def __setLongStop__(self, data, row):
        """
        The method to calculate the stop for a new Long position.
        """
        atr = data["atr"]["%s_%i" % (self.preliminary_analyses["atr"].analysis_type, self.atr_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        return close - atr*self.atr_stop

    def __setShortStop__(self, data, row):
        """
        The method to calculate the stop for a new Short position.
        """
        atr = data["atr"]["%s_%i" % (self.preliminary_analyses["atr"].analysis_type, self.atr_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        return close + atr*self.atr_stop

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        ma_newer = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_older = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        mmin_newer = data["mmin"]["%s_%i" % (self.preliminary_analyses["mmin"].analysis_type, self.min_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        filter = ma_newer<ma_older
        exit = close<mmin_newer
        stop = close<self.__stop__

        return filter or exit or stop 
       
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        ma_newer = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[0])][row]
        ma_older = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.ma_lookback[1])][row]
        mmax_newer = data["mmax"]["%s_%i" % (self.preliminary_analyses["mmax"].analysis_type, self.max_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        filter = ma_newer>ma_older
        exit = close>mmax_newer
        stop = close>self.__stop__

        return filter or exit or stop 


class BollingerBreakout(tradingSystem):
    """
    A class to describe the Bollinger Breakout trading system.
    """
    # attributes
    analysis_type = "BollingerBreakout"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, lookback=[350], n_sigma=2.5):
        """
        The initialisation method.
        """
        self.lookback = lookback
        self.n_sigma = n_sigma
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : EWMA(self.input_data, self.analysis_period, self.lookback) ,
                 "var" : EWVAR(self.input_data, self.analysis_period, self.lookback) }
        
    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback[0])][row]
        var = data["var"]["%s_%i" % (self.preliminary_analyses["var"].analysis_type, self.lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        return close>( ma + (self.n_sigma*math.sqrt(var)) )

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback[0])][row]
        var = data["var"]["%s_%i" % (self.preliminary_analyses["var"].analysis_type, self.lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        return close<( ma - (self.n_sigma*math.sqrt(var)) )

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        return not close>ma
       
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]

        return not close<ma


class TurtlesSystemTwo(tradingSystem):
    """
    A class to describe the Turtles' System 2 trading system.
    """
    # attributes
    analysis_type = "TurtlesSystemTwo"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, min_lookback=[55], max_lookback=[55], atr_lookback=[20], atr_stop=2.0):
        """
        The initialisation method.
        """
        self.min_lookback = min_lookback
        self.max_lookback = max_lookback
        self.atr_lookback = atr_lookback
        self.atr_stop = atr_stop
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "mmin" : MMIN(self.input_data, self.analysis_period, self.min_lookback) ,
                 "mmax" : MMAX(self.input_data, self.analysis_period, self.max_lookback) ,
                 "atr" : N(self.input_data, self.analysis_period, self.atr_lookback) }
        
    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        mmax = data["mmax"]["%s_%i" % (self.preliminary_analyses["mmax"].analysis_type, self.max_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]
        return close>mmax

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        mmin = data["mmin"]["%s_%i" % (self.preliminary_analyses["mmin"].analysis_type, self.min_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]
        return close<mmin

    def __setLongStop__(self, data, row):
        """
        The method to calculate the stop for a new Long position.
        """
        atr = data["atr"]["%s_%i" % (self.preliminary_analyses["atr"].analysis_type, self.atr_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]
        return close - atr*self.atr_stop

    def __setShortStop__(self, data, row):
        """
        The method to calculate the stop for a new Short position.
        """
        atr = data["atr"]["%s_%i" % (self.preliminary_analyses["atr"].analysis_type, self.atr_lookback[0])][row]
        close = data[self.input_data.name]["Close"][row]
        return close + atr*self.atr_stop

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        close = data[self.input_data.name]["Close"][row]
        return close<self.__stop__
       
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        close = data[self.input_data.name]["Close"][row]
        return close>self.__stop__


class GradSig(tradingSystem):
    """
    A class to describe a trading system based on price gradient significance.
    """
    # attributes
    analysis_type = "GradSig"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, lookback=[20], n_sigma=3.0):
        """
        The initialisation method.
        """
        self.lookback = lookback
        self.n_sigma = n_sigma
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "grad" : EWGRAD(self.input_data, self.analysis_period, self.lookback) ,
                 "gerr" : EWGRADERR(self.input_data, self.analysis_period, self.lookback) }
        
    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback[0])][row]
        gerr = data["gerr"]["%s_%i" % (self.preliminary_analyses["gerr"].analysis_type, self.lookback[0])][row]

        if gerr==0.0:
            filter = False
        else:
            filter = math.fabs(grad/gerr)>self.n_sigma
        
        enter = grad>0.0

        return filter and enter

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback[0])][row]
        gerr = data["gerr"]["%s_%i" % (self.preliminary_analyses["gerr"].analysis_type, self.lookback[0])][row]

        if gerr==0.0:
            filter = False
        else:
            filter = math.fabs(grad/gerr)>self.n_sigma
        
        enter = grad<0.0

        return filter and enter

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback[0])][row]
        gerr = data["gerr"]["%s_%i" % (self.preliminary_analyses["gerr"].analysis_type, self.lookback[0])][row]

        if gerr==0.0:
            filter = False
        else:
            filter = math.fabs(grad/gerr)>self.n_sigma

        return not filter
       
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        return self.__exitLong__(data, row)


class GradConf(tradingSystem):
    """
    A class to describe a trading system based on price gradient confidence interval.
    """
    # attributes
    analysis_type = "GradConf"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], equity=100.0, lookback=[250], confidence=0.95):
        """
        The initialisation method.
        """
        self.lookback = lookback
        self.confidence = confidence
        tradingSystem.__init__(self, input_data, analysis_period, equity)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "grad" : EWGRAD(self.input_data, self.analysis_period, self.lookback) ,
                 "gerr" : EWGRADERR(self.input_data, self.analysis_period, self.lookback) }
        
    def __pOneTail__(self, pTwoTail):
        """
        A method to return the corresponding one-tail interval for a 
        given two-tail test interval.
        """
        return 1.0 - ( (1.0 - pTwoTail)/2.0 )

    def __tValue__(self):
        """
        A methof to return the critical t-value for a two-tail test.
        """
        return ROOT.TMath.StudentQuantile(self.__pOneTail__(self.confidence), self.lookback[0]-2)

    def __goLong__(self, data, row):
        """
        The method to test if a Long position should be taken.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback[0])][row]
        gerr = data["gerr"]["%s_%i" % (self.preliminary_analyses["gerr"].analysis_type, self.lookback[0])][row]
        
        if gerr==0.0:
            filter = False
        else:
            filter = math.fabs(grad/gerr)>self.__tValue__()

        enter = grad>0.0
        
        return filter and enter

    def __goShort__(self, data, row):
        """
        The method to test if a Short position should be taken.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback[0])][row]
        gerr = data["gerr"]["%s_%i" % (self.preliminary_analyses["gerr"].analysis_type, self.lookback[0])][row]

        if gerr==0.0:
            filter = False
        else:
            filter = math.fabs(grad/gerr)>self.__tValue__()

        enter = grad<0.0

        return filter and enter

    def __exitLong__(self, data, row):
        """
        The method to test if a Long position should be closed.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback[0])][row]
        gerr = data["gerr"]["%s_%i" % (self.preliminary_analyses["gerr"].analysis_type, self.lookback[0])][row]

        if gerr==0.0:
            filter = False
        else:
            filter = math.fabs(grad/gerr)>self.__tValue__()

        return not filter
       
    def __exitShort__(self, data, row):
        """
        The method to test if a Short position should be closed.
        """
        return self.__exitLong__(data, row)

# end of file
