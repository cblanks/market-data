#!/usr/bin/python
# Filename : strategyAnalysis.py

# docstrings
"""
The strategy analysis class for the Yahoo! Finance systematic trading package.

A strategy analysis class to describe trading strategy performance using standard metrics, such as the MAR and Sharpe ratios.
"""

# dependencies
from csvDataset import *
from returnsAnalysis import *
from tradingStrategy import *
import datetime
import math

# attributes
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

__nominal_days_per_year__ = 250 
__risk_free_rate__ = 0.05
__monthly_risk_free_rate__ = math.pow( 1.0 + __risk_free_rate__, 1.0/12.0 ) - 1.0

# classes
class strategyAnalysis(csvDataset):
    """
    A class to perform analysis of a trading strategy over a defined period.
    """
    # attributes
    
    # protected
    def __init__( self, strategy, binning="All" ): # "Annual" - later implement "Quarterly"
        """
        The initialisation method.
        """
        self.strategy = strategy
        self.benchmark = Hold(self.strategy.input_data, self.strategy.analysis_period, self.strategy.equity)
        self.preliminary_analyses = self.__setPreliminaryAnalyses__()

        self.binning = binning
        
        csvDataset.__init__(self, self.__csvPath__())
        
        self.headers = [ "Start Date" ,
                         "End Date" ,
                         "Start Equity" ,
                         "End Equity" ,
                         "Trades Entered" ,
                         "Winning Trades Entered" , 
                         "Win Ratio" ,
                         "Positive Months" ,
                         "CAGR" ,
                         "RAR" ,
                         "RAR Error" ,
                         "Max Drawdown" ,
                         "Max Drawdown Days" ,
                         "MAR Ratio" ,
                         "MAR Regressed" ,
                         "Sharpe Ratio" ,
                         "Sharpe CAGR" ,
                         "Sharpe Benchmark" ,
                         "Sortino Ratio" ]
                         
        self.low_bin_edges = self.__lowBinEdges__()
        
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return { "Drawdowns"             : Drawdowns(self.strategy) ,
                 "Returns"               : Returns(self.strategy, "Monthly") ,
                 "log Returns"           : logReturns(self.strategy, "Monthly") ,
                 "Benchmark Returns"     : Returns(self.benchmark, "Monthly") ,
                 "Benchmark log Returns" : logReturns(self.benchmark, "Monthly") }

    def __csvPath__(self):
        """
        A method to set the csv file path where the analysis results are to be stored. 
        """
        return "%s/%s_%s_analysis.csv" % (self.strategy.analysis_dir, self.strategy.input_data.name, self.strategy.name)
        
    def __lowBinEdges__(self):
        """
        A method to define the time-period bins of this analysis.
        Low edges of each bin plus high edge of final bin.
        """
        low_bin_edges = []
        one_day = datetime.timedelta(days=1)
        
        if self.binning=="Annual":
            low_bin_edges.append(self.strategy.analysis_period[0])
            for year in xrange(self.strategy.analysis_period[0].year+1, self.strategy.analysis_period[1].year+1):
                low_bin_edges.append(datetime.date(year, 1, 1))
                
            low_bin_edges.append(self.strategy.analysis_period[1]+one_day)

        else: #elif self.binning=="All":
            low_bin_edges.append(self.strategy.analysis_period[0])
            low_bin_edges.append(self.strategy.analysis_period[1]+one_day)            

        return low_bin_edges
    
    def __binLimits__(self, bin):
        """
        A method to return the time period covered by an analysis bin.
        """
        return [self.low_bin_edges[bin], self.low_bin_edges[bin+1]]

    def __listTrades__(self, input): # TBC make sub-class of returnsAnalysis
        """
        A method to list each trade's entry and exit dates executed by the strategy 
        and the fund value before and after.
        """
        entry_date = []
        entry_equity = []
        exit_date = []
        exit_equity = []
        
        for row in xrange(self.strategy.__initialAnalysisPeriod__()+1, len(input["Date"])):

            # look for position changes
            if not input["Position"][row]==input["Position"][row-1]:
                
                # note trade exit
                if not len(entry_date)==0 and not input["Position"][row-1]==0:
                    exit_date.append(input["Date"][row])
                    exit_equity.append(input["Equity"][row])
                    
                # note trade entry
                if not input["Position"][row]==0:
                    entry_date.append(input["Date"][row])
                    entry_equity.append(input["Equity"][row])
                    
        # check for an ongoing trade
        if len(entry_date)>len(exit_date):
            exit_date.append("TBC")
            exit_equity.append("TBC")
            
        return { "Entry Date"   : entry_date ,
                 "Entry Equity" : entry_equity ,
                 "Exit Date"    : exit_date ,
                 "Exit Equity"  : exit_equity }
    
    def __countTrades__(self, trade_list, bin_limits):
        """
        A method to count the number of trades executed in this system 
        and the number of them which are successful.
        """
        trades = 0
        wins = 0
        
        for i in xrange(0, len(trade_list["Entry Date"])):
            if trade_list["Entry Date"][i]>=bin_limits[0] and trade_list["Entry Date"][i]<bin_limits[1]:
                trades+=1
                
                if not trade_list["Exit Equity"][i]=="TBC" and trade_list["Exit Equity"][i]>trade_list["Entry Equity"][i]:
                    wins+=1
                    
        if trades==0:
            win_ratio = 0.0
        else:
            win_ratio = (1.0*wins)/(1.0*trades)
            
        return trades, wins, win_ratio
    
    def __rowAtDate__(self, analysis, input, test_date):
        """
        A method to find the row in the input data set at a particular date of type 'datetime.date'.
        """
        # check if date is at a boundary of, or falls outside, the period of testing
        lower = analysis.__initialAnalysisPeriod__()
        upper = len(input["Date"]) - 1
        
        if input["Date"][lower]>=test_date:
            return lower
            
        elif input["Date"][upper]<=test_date:
            return upper
            
        else: # perform binary search through test dates
            while True:
                middle = (lower + upper)/2
                
                if input["Date"][middle-1]<test_date and input["Date"][middle]>=test_date:
                    return middle
                
                elif input["Date"][middle]<test_date:
                    lower = middle
                    
                else: #input["Date"][middle]>test_date:
                    upper = middle
                    
    def __positiveMonths__(self, input, row_limits):
        """
        A method to return the fraction of months with positive returns.
        """
        positive = 0
        months = 0

        for row in xrange(row_limits[0], row_limits[1]):
            months += 1
            if input["Return"][row]>0.0:
                positive += 1
            
        if months==0:
            return 0.0
        else:
            return (1.0*positive)/(1.0*months)
        
    def __meanSdevReturns__(self, input, row_limits, log=False, flavour="Plain"): # "Plain", "RFR" or "Benchmark"
        """
        A method to calculate the annualised mean and standard deviation of the 
        monthly (log)returns of a strategy.
        """
        sum_x = 0.0
        n = 0
        row_range = xrange(row_limits[0], row_limits[1])

        if log:
            key = "log Returns"
        else:
            key = "Returns"
                
        for row in row_range:
            x = input[key]["Return"][row]
            
            if flavour=="Benchmark":
                b = input["Benchmark "+key]["Return"][row]
                x -= b
                
            elif flavour=="RFR":
                x -= __monthly_risk_free_rate__
            
            sum_x += x
            n += 1
            
        mean_x = sum_x / (1.0*n)
        
        rsq_x = 0.0
        for row in row_range:
            x = input[key]["Return"][row]
            
            if flavour=="Benchmark":
                b = input["Benchmark "+key]["Return"][row]
                x -= b
                
            elif flavour=="RFR":
                x -= __monthly_risk_free_rate__
                
            rsq_x += (x - mean_x)*(x - mean_x)
            
        var_x = rsq_x / (n-1.0)
        
        return 12.0*mean_x, math.sqrt(12.0*var_x)
        
    def __CAGR__(self, equity, time):
        """
        A method to calculate the Compound Annual Growth Rate.
        """
        period_in_days = (time[1]-time[0]).days
        period_in_years = ( 1.0*period_in_days )/( 1.0*__nominal_days_per_year__ )

        return math.pow( equity[1]/equity[0], 1.0/period_in_years ) - 1.0
    
    def __regressedCAGR__(self, input, row_limits):
        """
        A method to calculate the regressed Compound Annual Growth Rate, as the gradient 
        of the log Equity.
        """
        sum_x = 0.0
        sum_y = 0.0
        n = 0
        
        row_range = xrange(row_limits[0], row_limits[1])

        for row in row_range:
            sum_x += (1.0*row)/(1.0*__nominal_days_per_year__) # i.e. trading years
            sum_y += math.log( input["Equity"][row] )
            n += 1
            
        mean_x = (1.0*sum_x)/(1.0*n)
        mean_y = (1.0*sum_y)/(1.0*n)
        
        res_xx = 0.0
        res_yy = 0.0
        res_xy = 0.0
        
        for row in row_range:
            x = (1.0*row)/(1.0*__nominal_days_per_year__)
            y = math.log( input["Equity"][row] )
            res_xx += (x-mean_x)*(x-mean_x)
            res_yy += (y-mean_y)*(y-mean_y)
            res_xy += (x-mean_x)*(y-mean_y)
            
        # calculation of variances is unnecessary since only ratios will be used
        grad = res_xy/res_xx
        gerr = math.sqrt( ( (res_yy/res_xx) - (grad*grad) )/( n - 2.0 ) )
        
        return grad, gerr
    
    def __maxDrawdown__(self, input, row_limits):
        """
        A method to find the maximum drawdown in equity.
        """
        max_drawdown = 0.0
        peak = input["Date"][0]
        period = 0
        max_period = 0
        
        for row in xrange(row_limits[0], row_limits[1]):
            if input["Drawdown"][row]>max_drawdown:
                max_drawdown = input["Drawdown"][row]
                
            if input["Peak"][row]==input["Peak"][row-1]:
                if not input["Peak"][row]==input["Equity"][row]:
                    period += 1 
                    if period>max_period:
                        max_period = period
            else:
                peak = input["Date"][row]
                
        return max_drawdown, max_period
        
    def __meanSdevCAGR__(self, input, row_limits, flavour="RFR"): # "Plain", "RFR" or "Benchmark"
        """
        A method to calculate the annualised mean and standard deviation Compound Annual 
        Growth Rate of a strategy.
        """ 
        mean, sdev = self.__meanSdevReturns__(input, row_limits, True, flavour)
        
        cagr_mean = math.pow( math.e, mean ) - 1.0
        cagr_sdev = sdev * math.pow( math.e, mean )
        
        return cagr_mean, cagr_sdev

    def __SharpeRatio__(self, input, row_limits, flavour="Plain"): # "Plain", "RFR", "CAGR" or "Benchmark"
        """
        A method to calculate the annualised Sharpe Ratio using monthly returns.
        """
        if flavour=="CAGR":
            mean, sdev = self.__meanSdevCAGR__(input, row_limits, "RFR")
        else:
            mean, sdev = self.__meanSdevReturns__(input, row_limits, False, flavour)
            
        if sdev==0.0:
            return "NaN"
        else:
            return mean/sdev
        
    def __downsideSdevReturns__(self, input, row_limits, log=False):
        """
        A method to calculate the annualised standard deviation of the 
        downside monthly (log)returns of a strategy.
        """
        sum_x = 0.0
        n = 0
        row_range = xrange(row_limits[0], row_limits[1])

        if log:
            key = "log Returns"
        else:
            key = "Returns"
            
        for row in row_range:
            x = input[key]["Return"][row]
            
            if x<0.0: 
                continue
            
            x -= __monthly_risk_free_rate__
            
            sum_x += x
            n += 1
            
        if n<1:
            mean_x = 0.0
        else:
            mean_x = sum_x / (1.0*n)
            
        res_xx = 0.0

        for row in row_range:
            x = input[key]["Return"][row]
            
            if not x<0.0: 
                continue
            
            x -= __monthly_risk_free_rate__
            
            res_xx += (x-mean_x)*(x-mean_x)
            
        if n<2:
            var_x = 0.0
        else:
            var_x = res_xx/(n-1.0)
        
        return math.sqrt(12.0*var_x)
        
    def __SortinoRatio__(self, input, bin_limits, log=False):
        """
        A method to calculate the annualised Sortino Ratio using monthly returns.
        """
        mean, sdev = self.__meanSdevReturns__(input, bin_limits, log)
        sdev = self.__downsideSdevReturns__(input, bin_limits, log)
        
        if sdev==0.0:
            return "NaN"
        else:
            return mean/sdev

    # public
    def run(self):
        """
        The method to run the analysis.
        """
        print "Running the %s trading strategy for %s..." % (self.strategy.name, self.strategy.input_data.name)
        self.strategy.run()
        self.benchmark.run()
        
        print "Running the preliminary analyses..."
        for analysis in self.preliminary_analyses.values():
            analysis.run()
        
        input = { "Strategy" : self.strategy.__getCsvData__() }
        if not self.preliminary_analyses==None:
            for i in xrange(0, len(self.preliminary_analyses.keys())):
                input[self.preliminary_analyses.keys()[i]] = self.preliminary_analyses.values()[i].__getCsvData__()

        print "Running the strategy analysis..."
        output = {}
        for header in self.headers:
            output[header] = []
            
        list_of_trades = self.__listTrades__(input["Strategy"])
        
        for i in xrange(0, len(self.low_bin_edges)-1):
            
            # find limits for this bin
            bin_limits = self.__binLimits__(i)

            strategy_row_limits = [ self.__rowAtDate__(self.strategy, input["Strategy"], bin_limits[0]) ,
                                    self.__rowAtDate__(self.strategy, input["Strategy"], bin_limits[1]) ]

            drawdowns_row_limits = [ self.__rowAtDate__(self.preliminary_analyses["Drawdowns"], input["Drawdowns"], bin_limits[0]) ,
                                     self.__rowAtDate__(self.preliminary_analyses["Drawdowns"], input["Drawdowns"], bin_limits[1]) ]

            returns_row_limits = [ self.__rowAtDate__(self.preliminary_analyses["Returns"], input["Returns"], bin_limits[0]) ,
                                   self.__rowAtDate__(self.preliminary_analyses["Returns"], input["Returns"], bin_limits[1]) ]
            
            # period
            output["Start Date"].append( input["Strategy"]["Date"][strategy_row_limits[0]] )
            output["End Date"].append( input["Strategy"]["Date"][strategy_row_limits[1]] )
            print "%s to %s" %( output["Start Date"][i], output["End Date"][i] )
            
            # equity
            output["Start Equity"].append( input["Strategy"]["Equity"][strategy_row_limits[0]] )
            output["End Equity"].append( input["Strategy"]["Equity"][strategy_row_limits[1]] )
            
            # CAGR
            output["CAGR"].append( self.__CAGR__( [output["Start Equity"][i], output["End Equity"][i]] , 
                                                  [output["Start Date"][i], output["End Date"][i]] ) )
            
            _rar, _serr = self.__regressedCAGR__( input["Strategy"], strategy_row_limits )
            output["RAR"].append( _rar )
            output["RAR Error"].append( _serr )
            
            # number of trades and win ratio
            _trades, _wins, _win_ratio = self.__countTrades__(list_of_trades, bin_limits) # TBC
            output["Trades Entered"].append( _trades )
            output["Winning Trades Entered"].append( _wins )
            output["Win Ratio"].append( _win_ratio )
            
            # drawdowns
            _max_drawdown, _max_drawdown_days = self.__maxDrawdown__( input["Drawdowns"], drawdowns_row_limits )
            output["Max Drawdown"].append( _max_drawdown )
            output["Max Drawdown Days"].append( _max_drawdown_days )
            
            # positive months
            output["Positive Months"].append( self.__positiveMonths__(input["Returns"], returns_row_limits) )
            
            # MAR ratio
            if output["Max Drawdown"][i]==0.0:
                output["MAR Ratio"].append("NaN")
                output["MAR Regressed"].append("NaN")
            else:
                output["MAR Ratio"].append( output["CAGR"][i]/output["Max Drawdown"][i] )
                output["MAR Regressed"].append( output["RAR"][i]/output["Max Drawdown"][i] )
            
            # Sharpe ratio
            output["Sharpe Ratio"].append( self.__SharpeRatio__( input, returns_row_limits, flavour="RFR" ) )
            output["Sharpe CAGR"].append( self.__SharpeRatio__( input, returns_row_limits, flavour="CAGR" ) )
            output["Sharpe Benchmark"].append( self.__SharpeRatio__( input, returns_row_limits, flavour="Benchmark" ) )
            
            # Sortino ratio
            output["Sortino Ratio"].append( self.__SortinoRatio__( input, returns_row_limits ) )

        # write output
        self.__setCsvData__(output)
        print "complete."

# end of file
