#!/usr/bin/python
# Filename : priceAnalysis.py

# docstrings
"""
The price analysis methods for the Yahoo! Finance systematic trading package.

These price analysis classes, calculating moving location and spread measures, are the bulding blocks for all trading strategies.
"""

# dependencies
from timeSeriesAnalysis import *
import datetime
import math

# attributes
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

__long_ago__ = datetime.date(1897, 1, 1) # the year J.J. Thomson discovered the electron. 

# classes
class MA(timeSeriesAnalysis):
    """
    An object to calculate the N-Day Moving Average of the closing price.
    """
    # attributes
    analysis_type = "MA"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        timeSeriesAnalysis.__init__(self, input_data, analysis_period, lookback_days)
        self.__lookback_values__ = []
        self.__sum__ = -999.0
        
    def __variable__(self, data, row, i):
        """
        Method to return the variable to be averaged.
        """
        return data[self.input_data.name]["Close"][row]

    def __dof__(self, i):
        """
        The method to return the number of degrees of freedom.
        """
        return 1.0*self.__initialAnalysisPeriod__(i)

    def __calculation__(self, data, i, row):
        """
        The method to calculate the N-Day moving Average.
        """
        # First step
        if row==self.__initialAnalysisPeriod__(i):
            for r in xrange(0, row):
                x = self.__variable__(data, r, i) 
                self.__lookback_values__.append(x)
                self.__sum__ += x
                
        # Iterate the moving average
        else:
            x = self.__variable__(data, row-1) 
            self.__sum__ += x
            self.__sum__ -= self.__lookback_values__[0]
            self.__lookback_values__.pop(0)
            self.__lookback_values__.append(x)
            
        return self.__sum__ / self.__dof__(i)

    # public


class VAR(MA):
    """
    An object to calculate the N-Day VARiance of the daily closing price.
    """
    # attributes
    analysis_type = "VAR"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        MA.__init__(self, input_data, analysis_period, lookback_days)

    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : MA(self.input_data, self.analysis_period, self.lookback_days) }
        
    def __variable__(self, data, row, i):
        """
        Method to return the variable to be averaged.
        """
        if row<self.__initialAnalysisPeriod__(i):
            ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback_days[i])][self.__initialAnalysisPeriod__(i)]
        else:
            ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback_days[i])][row]

        res = data[self.input_data.name]["Close"][row] - ma
        return res*res

    def __dof__(self, i):
        """
        The method to return the number of degrees of freedom.
        """
        return self.__initialAnalysisPeriod__(i) - 1.0

    # public


class MADAY(MA):
    """
    An object to calculate the N-Day Moving Average business day, 
    counted from the start of the analysis period.
    """
    # attributes
    analysis_type = "MADAY"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        MA.__init__(self, input_data, analysis_period, lookback_days)
        
    def __variable__(self, data, row, i):
        """
        Method to return the variable to be averaged.
        """
        return row

    # public


class COV(VAR):
    """
    An object to calculate the N-Day COVariance of the daily closing price and the date.
    """
    # attributes
    analysis_type = "COV"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        VAR.__init__(self, input_data, analysis_period, lookback_days)

    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : MA(self.input_data, self.analysis_period, self.lookback_days) ,
                 "maday" : MADAY(self.input_data, self.analysis_period, self.lookback_days) }
        
    def __variable__(self, data, row, i):
        """
        Method to return the variable to be averaged.
        """
        if row<self.__initialAnalysisPeriod__(i):
            ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback_days[i])][self.__initialAnalysisPeriod__(i)]
            maday = data["maday"]["%s_%i" % (self.preliminary_analyses["maday"].analysis_type, self.lookback_days[i])][self.__initialAnalysisPeriod__(i)]
        else:
            ma = data["ma"]["%s_%i" % (self.preliminary_analyses["ma"].analysis_type, self.lookback_days[i])][row]
            maday = data["maday"]["%s_%i" % (self.preliminary_analyses["maday"].analysis_type, self.lookback_days[i])][row]

        res_y = data[self.input_data.name]["Close"][row] - ma
        res_x = row - maday
        return res_y*res_x

    # public


class ATR(MA):
    """
    An object to calculate the moving Average of the daily True Range, 
    where the true range is defined as the largest of:
    a) High - Low
    b)|High - Previous Close|
    c)|Low  - Previous Close|
    """
    # attributes
    analysis_type = "ATR"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        MA.__init__(self, input_data, analysis_period, lookback_days)

    def __variable__(self, data, row, i):
        """
        Method to return the variable to be averaged: the True Range.
        """
        a = data[self.input_data.name]["High"][row] - data[self.input_data.name]["Low"][row]
        if row==0: # special case for the first data point. TBC does this ever occur with the initialAnalysisPeriod?
            return a
        
        b = math.fabs(data[self.input_data.name]["Close"][row-1] - data[self.input_data.name]["High"][row])
        c = math.fabs(data[self.input_data.name]["Close"][row-1] - data[self.input_data.name]["Low"][row])

        true_range = a
        if b>true_range:
            true_range = b
        if c>true_range:
            true_range = c
            
        return true_range

    # public


class N(ATR):
    """
    An object to calculate the moving Average of the daily True Range, 
    as defined in Way of the Turtle.
    """
    # attributes
    analysis_type = "N"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        ATR.__init__(self, input_data, analysis_period, lookback_days)
        self.__N__ = 0.0

    def __calculation__(self, data, i, row):
        """
        The method to calculate one iteration of an exponential moving average.
        """
        # calculate starting value
        if row==self.__initialAnalysisPeriod__(i):
            for r in xrange(0, row):
                self.__sum__ += self.__variable__(data, r, i)

            self.__N__ = self.__sum__ / self.lookback_days[i]
        
        # iterate the moving average
        else:
            self.__N__ = ( self.__N__*(self.lookback_days[i]-1) + self.__variable__(data, row-1, i) ) / self.lookback_days[i]
            
        return self.__N__

    # public


class MMAX(timeSeriesAnalysis):
    """
    An object to calculate the N-Day Moving MAXimum value of the 
    daily highest price.
    """
    # attributes
    analysis_type = "MMAX"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        timeSeriesAnalysis.__init__(self, input_data, analysis_period, lookback_days)
        self.__lookback_values__ = []
        self.__extreme__ = -999.0
        
    def __variable__(self, data, row, i):
        """
        Method to return the variable to be tested.
        """
        return data[self.input_data.name]["High"][row]

    def __test__(self, value, extreme):
        """
        Method to return a True if a value is greater than the maximum.
        """
        return extreme < value

    def __calculation__(self, data, i, row):
        """
        The method to calculate the N-Day Moving MAXimum.
        """
        # First step
        if row==self.__initialAnalysisPeriod__(i):
            x = self.__variable__(data, 0, i)
            self.__lookback_values__.append(x)
            self.__extreme__ = x
            
            for r in xrange(1, row):
                x = self.__variable__(data, r, i)
                self.__lookback_values__.append(x)
                if self.__test__(x, self.__extreme__):
                    self.__extreme__ = x
                
        # Iterate extreme value
        else:
            x = self.__variable__(data, row-1, i)
            self.__lookback_values__.append(x)

            # if the previous extreme is being dropped, re-examine the lookback_values
            if self.__lookback_values__[0]==self.__extreme__:
                self.__lookback_values__.pop(0)
                self.__extreme__ = self.__lookback_values__[0]
                for i in self.__lookback_values__:
                    if self.__test__(i, self.__extreme__):
                        self.__extreme__ = i

            # otherwise, check the new value
            else:
                self.__lookback_values__.pop(0)
                if self.__test__(x, self.__extreme__):
                    self.__extreme__ = x

        return self.__extreme__

    # public


class MMIN(MMAX):
    """
    An object to calculate the N-Day Moving MINimum value of the 
    daily lowest price.
    """
    # attributes
    analysis_type = "MMIN"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        MMAX.__init__(self, input_data, analysis_period, lookback_days)
        
    def __variable__(self, data, row, i):
        """
        Method to return the variable to be tested.
        """
        return data[self.input_data.name]["Low"][row]

    def __test__(self, value, extreme):
        """
        Method to return a True if a value is less than the minimum.
        """
        return extreme > value

    # public


class GRAD(timeSeriesAnalysis):
    """
    An object to calculate the N-Day linear GRADient of the daily closing price.
    """
    # attributes
    analysis_type = "GRAD"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        timeSeriesAnalysis.__init__(self, input_data, analysis_period, lookback_days)
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "var" : VAR(self.input_data, self.analysis_period, self.lookback_days) ,
                 "cov" : COV(self.input_data, self.analysis_period, self.lookback_days) }
    
    def __calculation__(self, data, i, row):
        """
        Method to calculate the N-Day GRADient.
        """
        var = data["var"]["%s_%i" % (self.preliminary_analyses["var"].analysis_type, self.lookback_days[i])][row]
        cov = data["cov"]["%s_%i" % (self.preliminary_analyses["cov"].analysis_type, self.lookback_days[i])][row]
        return cov/var


class GRADERR(timeSeriesAnalysis):
    """
    An object to calculate the N-Day Standard Error on the linear GRADient of the daily closing price.
    """
    # attributes
    analysis_type = "GRADERR"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        timeSeriesAnalysis.__init__(self, input_data, analysis_period, lookback_days)
        self.__day_var__ = self.__dayVar__()
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "grad" : GRAD(self.input_data, self.analysis_period, self.lookback_days) ,
                 "var" : VAR(self.input_data, self.analysis_period, self.lookback_days) }
        
    def __dayVar__(self):
        """
        A method to return the business day variance for each requested lookback period.
        """
        day_var = []
        for i in xrange(0, len(self.lookback_days)):
            sum_d = 0.0
            for d in xrange(0, i):
                sum_d += d

            mean_d = sum_d/(1.0*self.lookback_days[i])
            
            sum_ressq_d = 0.0
            for d in xrange(0, self.lookback_days[i]):
                sum_ressq_d += (d - mean_d)*(d - mean_d)

            day_var.append( sum_ressq_d/(self.lookback_days[i]-1.0) )
        
        return day_var

    def __calculation__(self, data, i, row):
        """
        Method to calculate the standard ERRor on the N-Day GRADient.
        """
        grad = data["grad"]["%s_%i" % (self.preliminary_analyses["grad"].analysis_type, self.lookback_days[i])][row]
        var = data["var"]["%s_%i" % (self.preliminary_analyses["var"].analysis_type, self.lookback_days[i])][row]
        
        gvar = ( (self.__day_var__[i]/var) - (grad*grad) )/( self.lookback_days[i] - 2.0 )
        if gvar<0.0:
            return 0.0
        else:
            return math.sqrt(gvar)


class exponentialWeighting():
    """
    An object to provide additional attributes and methods to a 
    'timeSeriesAnalysis'-derived class for exponential weighting.
    """
    # attributes
    
    # protected
    def __init__(self, lookback_days=[10]):
        """
        The initialisation method.
        """
        self.__ewma__ = 0.0 # the iterator
        self.alpha = self.__calcAlpha__(lookback_days)

    def __initialAnalysisPeriod__(self, i=0):
        """
        A method to return the initial period - in trading days - preliminary 
        for the first analysis.
        """
        return 5

    def __calcAlpha__(self, lookback_days):
        """
        Method to calculate the smoothing factor alpha corresponding to an 
        N-Day average.
        """
        alpha = []
        for i in lookback_days:
            alpha.append( 2.0 / ( i + 1.0 ) )

        return alpha

    def __calculation__(self, data, i, row):
        """
        The method to calculate one iteration of an exponential moving average.
        """
        # First step
        if row==self.__initialAnalysisPeriod__(i):
            sum = 0.0
            for r in xrange(0, row):
                sum += self.__variable__(data, r, i)

            self.__ewma__ = sum / self.__dof__(i)

        # Iterate the exponentially weighted moving average
        else:
            x = self.__variable__(data, row-1, i)
            self.__ewma__ = self.alpha[i]*x + (1.0-self.alpha[i])*self.__ewma__
            
        return self.__ewma__

    # public


class EWMA(exponentialWeighting, MA):
    """
    An object to calculate the Exponentially Weighted Moving Average
    of the daily closing price.
    """
    # attributes
    analysis_type = "EWMA"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        MA.__init__(self, input_data, analysis_period, lookback_days)
        exponentialWeighting.__init__(self, lookback_days)

    # public


class EWVAR(exponentialWeighting, VAR):
    """
    An object to calculate the Exponentially Weighted VARiance
    of the daily closing price.
    """
    # attributes
    analysis_type = "EWVAR"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        VAR.__init__(self, input_data, analysis_period, lookback_days)
        exponentialWeighting.__init__(self, lookback_days)

    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : EWMA(self.input_data, self.analysis_period, self.lookback_days) }        

    # public


class EWMADAY(exponentialWeighting, MADAY):
    """
    An object to calculate the Exponentially Weighted Moving Average
    of the daily closing price.
    """
    # attributes
    analysis_type = "EWMA"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        MADAY.__init__(self, input_data, analysis_period, lookback_days)
        exponentialWeighting.__init__(self, lookback_days)

    # public


class EWCOV(exponentialWeighting, COV):
    """
    An object to calculate the Exponentially Weighted COVariance
    of the daily closing price and the date.
    """
    # attributes
    analysis_type = "EWCOV"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        COV.__init__(self, input_data, analysis_period, lookback_days)
        exponentialWeighting.__init__(self, lookback_days)

    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "ma" : EWMA(self.input_data, self.analysis_period, self.lookback_days) ,
                 "maday" : EWMADAY(self.input_data, self.analysis_period, self.lookback_days) }

    # public


class EWATR(exponentialWeighting, ATR):
    """
    An object to calculate the Exponentially Weighted Average of the 
    daily True Range.
    """
    # attributes
    analysis_type = "EWATR"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        ATR.__init__(self, input_data, analysis_period, lookback_days)
        exponentialWeighting.__init__(self, lookback_days)

    # public


class EWGRAD(GRAD):
    """
    An object to calculate the exponentially weighted linear gradient 
    of the daily closing price.
    """
    # attributes
    analysis_type = "EWGRAD"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        GRAD.__init__(self, input_data, analysis_period, lookback_days)

    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "var" : EWVAR(self.input_data, self.analysis_period, self.lookback_days) ,
                 "cov" : EWCOV(self.input_data, self.analysis_period, self.lookback_days) }
        
    # public


class EWGRADERR(GRADERR):
    """
    An object to calculate the exponentially weighted standard error on the 
    linear gradient of the daily closing price.
    """
    # attributes
    analysis_type = "EWGRADERR"
    
    # protected
    def __init__(self, input_data, analysis_period=[__long_ago__, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        GRADERR.__init__(self, input_data, analysis_period, lookback_days)

    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "grad" : EWGRAD(self.input_data, self.analysis_period, self.lookback_days) ,
                 "var" : EWVAR(self.input_data, self.analysis_period, self.lookback_days) }
        
    # public

# end of file
