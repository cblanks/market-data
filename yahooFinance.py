#!/usr/bin/python
# Filename : yahooFinance.py

# docstrings ----------------------------------------------------
"""
A Yahoo! Finance data collection, analysis and systematic trading package.

Historical finance data is retrieved from Yahoo! Finance in csv format.
A dictionary of indices is maintained for easy batch retrieval.
The csv format is retained and used for all analysis data for compatibility with Excel for easy plotting.
Classic trend-following strategies have been implemented, such as Donchian Trend and Bollinger Breakout.
Each trading strategy runs based on pre-calculated moving location and spread measures, such as mean and variance.
A strategy analysis class describes the performance using standard metrics, such as the MAR and Sharpe ratios.
"""


# dependencies --------------------------------------------------
import cPickle
import csv
import datetime
import math
import os
import ROOT
import sys
import urllib 


# attributes ----------------------------------------------------
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

project_dir = os.path.expanduser("~/Documents/Study/MarketDataProject")
days_of_the_week = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]
a_long_time_ago = datetime.date(1897, 1, 1) # the year J.J. Thomson discovered the electron. 
nominal_days_per_year = 250 
risk_free_rate = 0.05
monthly_risk_free_rate = math.pow( 1.0 + risk_free_rate, 1.0/12.0 ) - 1.0


# functions -----------------------------------------------------
def volatility(variance, lookback_days):
    """
    A function to convert a daily standard deviation to volatility.
    """
    return math.sqrt( variance*nominal_days_per_year/lookback_days )


# classes -------------------------------------------------------
class financeDatasetGroup(dict):
    """
    A dictionary-derived object to group stored finance data from Yahoo! Finance.
    """
    # attributes

    # protected
    def __init__(self):
        """
        Initialise the dataset based on a supplied yahoo index dictionary.
        """
        self.indices = indexDictionary()
        for i in self.indices.keys():
            self[i] = financeDataset(i)
            
    # public
    def getLatest(self):
        """
        A method to update the dataset based on the list of Yahoo! indices. Ensures 
        that all existing data are up to date, that non-existing data is downloaded 
        and that previously saved data for non-listed indices is removed.
        """
        # check for redundant datasets to delete
        for i in self.keys():
            if not self.indices.has_key(i):
                self[i].removeCsv()
                del self[i]

        # update existing datasets
        for key in self.keys():
            self[key].getLatest(auto=True)
        
        # check for new indices to download
        for i in self.indices.keys():
            if not self.has_key(i): 
                self[i] = financeDataset(i)
                
    def summarise(self):
        """
        A method to print a summary of the loaded datasets.
        """
        for key in sorted(self.indices.keys()):
            data = self[key]
            period = data.__getStoredPeriod__()
            print data.name, "\t", period[0], "-->", period[1], "\t", self.indices[data.name]


class indexDictionary(dict):
    """
    A dictionary class for Yahoo's listed financial indices.
    """
    # attributes
    __backup__ = "%s/.yahooIndexDictionary.pkl" % project_dir
    
    default_indices = { "FTSE"  : "London FTSE 100 index"       ,
                        "FTMC"  : "London FTSE 250 index"       ,
                        "GDAXI" : "Frankfurt DAX 30 index"      ,
                        "FCHI"  : "Paris CAC 40"                ,
                        "IBEX"  : "Madrid IBEX 35"              ,
                        "DJI"   : "New York Dow Jones 30 index" ,
                        "OEX"   : "Chicago S&P 100 index"       ,
                        "VIX"   : "Chicago S&P 500 volatility"  ,
                        "NDX"   : "NASDAQ 100 index"            ,
                        "CCSI"  : "Cairo EGX 70 index"          ,
                        "N225"  : "Osaka Nikkei 225 index"      ,
                        "HSI"   : "Hong Kong Hang Seng index"   }
    
    # protected
    def __init__(self):
        """
        The initialisation method.
        """
        if not os.path.exists(project_dir): 
            os.makedirs(project_dir)
        
        # reset index dictionary if no backup file found
        if not os.path.isfile(self.__backup__):
            self.reset()
        else:
            f = open(self.__backup__)
            self.update(cPickle.load(f))
            f.close()

    def __del__(self):
        """
        The destruction method.
        """
        f = open(self.__backup__, "w")
        cPickle.dump(self, f)
        f.close()

    # public
    def reset(self):
        """
        Reset Yahoo! index dictionary to default list.
        """
        self.update(self.default_indices)


class csvDataset():
    """
    An object to contain data stored as a csv file.
    """
    # attributes
    
    # protected
    def __init__(self, csv_path):
        """
        The initialisation method.
        """
        self.csv_path = csv_path
        if os.path.exists(self.csv_path):
            self.headers = self.__getHeaders__()
        else:
            self.headers = []
            
    def __readCsv__(self):
        """
        A method to read out the data stored in the csv file.
        """
        csv_file = open(self.csv_path, "rb")
        data_reader = csv.reader(csv_file)
        data = []
        for row in data_reader:
            data.append(row)
        
        csv_file.close()

        return data

    def __getHeaders__(self):
        """
        A method to read out the headers of the stored data.
        """
        data = self.__readCsv__()
        headers = []
        for col in xrange(0, len(data[0])):
            headers.append(data[0][col])

        return headers

    def __writeCsv__(self, formatted_data):
        """
        A method to write formatted data to the csv file.
        """
        csv_file = open(self.csv_path, "wb")
        data_writer = csv.writer(csv_file)
        for row in formatted_data:
            data_writer.writerow(row)
        
        csv_file.close()
        
    def __getCsvData__(self):
        """
        Method to return csv file data, formatted into python dictionary {header:[entries]}.
        """
        data = self.__readCsv__()
        
        formatted_data = {}

        col_range = xrange(0, len(data[0]))
        row_range = xrange(1, len(data))
        
        for col in col_range:
            self.headers.append(data[0][col])
            entries = []
            
            for row in row_range.__reversed__():
                # reverse time order -> oldest first
                #row = n_rows - row
                #row = row_range[-1] - row
                
                # format data type
                original = data[row][col]
                if original=="": # ignore empty cells
                    formatted = original

                elif self.headers[col]=="Date":
                    formatted = datetime.date(int(original[0:4]), 
                                              int(original[5:7]), 
                                              int(original[8:10]))
                
                elif not original.find(" to ")==-1: # retain string format
                    formatted = original

                else:
                    formatted = float(original)
                    
                entries.append(formatted)

            formatted_data[self.headers[col]] = entries
            
        return formatted_data
    
    def __setCsvData__(self, data):
        """
        Method to write formatted analysis results - stored as a python 
        dictionary {header:[entries]} - to a csv file.
        """
        formatted_data = [self.headers]
        
        col_range = xrange(0, len(data.keys()))
        row_range = xrange(0, len(data[self.headers[0]]))

        for row in row_range.__reversed__():
            # reverse time order -> newest first
            #row = (n_rows - 1) - row
            #row = (row_range[-1] - 1) - row
            
            # arrange data for writing
            this_row = []
            for col in col_range:
                this_cell = data[self.headers[col]][row]
                if type(this_cell) is datetime.date:
                    this_cell = this_cell.isoformat()
                    
                this_row.append(this_cell)
                
            formatted_data.append(this_row)

        self.__writeCsv__(formatted_data)

    # public
    def viewCsv(self):
        """
        A function to open a csv file on Linux or Mac OSX.
        """
        if not os.path.exists(self.csv_path):
            print "This file was not found."
        else:
            if sys.platform.startswith("linux"): 
                os.system("gnome-open %s" % self.csv_path)
                
            elif sys.platform.startswith("darwin"):
                os.system("open %s" % self.csv_path)
            else:
                print "No command specified for this operating system."

    def removeCsv(self):
        """
        A function to delete a csv file.
        """
        if not os.path.exists(self.csv_path):
            print "This file was not found."
        else:
            os.system("rm -f %s" % self.csv_path)
            

class financeDataset(csvDataset):
    """
    A finance dataset object to contain historic prices sourced 
    from Yahoo Finance.
    """
    # attributes
    data_dir = "%s/downloadedData" % project_dir
    
    # protected
    def __init__(self, name="FTSE"):
        """
        The initialisation method.
        """
        if not os.path.exists(self.data_dir): 
            os.makedirs(self.data_dir)
        
        self.name = name
        
        csvDataset.__init__(self, self.__csvPath__())

        self.__ensureCsvExists__()
        
    def __csvPath__(self):
        """
        A method to return the csv file containing the data.
        """
        return "%s/%s.csv" % (self.data_dir, self.name)
        
    def __download__(self, period=[a_long_time_ago, datetime.date.today()]):
        """
        A method to download historical data from Yahoo! Finance.
        Default time period from a long time ago until today.
        """
        url_query = """\
http://ichart.finance.yahoo.com/table.csv?s=%sE%s&d=%i&e=%i&f=%i&g=d&a=%i&b=%i&c=%i&ignore=.csv\
""" % ("%5", # following yahoo's standard query string 
       self.name, # yahoo's code for this index
       period[1].month, period[1].day, period[1].year, # newest data
       period[0].month, period[0].day, period[0].year) # oldest data
        
        print "Downloading data for %s ..." % self.name
        urllib.urlretrieve(url_query, self.csv_path)  
        print "complete."
        
    def __ensureCsvExists__(self):
        """
        """
        if not os.path.isfile(self.csv_path):
            self.__download__()

    def __getStoredPeriod__(self):
        """
        A method to determine the newest and the oldest data stored.
        """
        data = self.__readCsv__()

        old = data[-1][0]
        new = data[1][0]
        
        return [datetime.date(int(old[0:4]), int(old[5:7]), int(old[8:10])),
                datetime.date(int(new[0:4]), int(new[5:7]), int(new[8:10]))]

    # public
    def getLatest(self, auto=False):
        """
        A method to update the stored data if new data is available.
        """
        if auto:
            self.__download__()
            
        elif not os.path.isfile(self.csv_path):
            print "No data is currently stored for %s."
            self.__download__()
            
        else:
            period = self.__getStoredPeriod__()
            
            user_says = "..."
            while not (user_says=="" or user_says=="Yes" or user_says=="No"):  
                user_says = raw_input(\
                    "The data stored for %s is from %s (%s) to %s (%s). Do you want to update? ([Yes]/No) "\
                    % ( self.name,
                        period[0].isoformat(), 
                        dayoftheweek[period[0].weekday()],
                        period[1].isoformat(), 
                        dayoftheweek[period[1].weekday()] ))
                
            if (user_says=="" or user_says=="Yes"):
                self.__download__()
                period = self.__getStoredPeriod__()
                
                print "The data stored for %s is from %s (%s) to %s (%s)"\
                    % ( self.name,
                        period[0].isoformat(), 
                        dayoftheweek[period[0].weekday()],
                        period[1].isoformat(), 
                        dayoftheweek[period[1].weekday()] )


class timeSeriesAnalysis(csvDataset):
    """
    A base class for time series analysis of Yahoo! Finance datasets.
    """
    # attributes
    analysis_dir = "%s/analysis" % project_dir
    analysis_type = "timeSeries"

    # protected
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
        """
        The initialisation method.
        """
        if not os.path.exists(self.analysis_dir):
            os.makedirs(self.analysis_dir)
        
        self.input_data = input_data
        self.lookback_days = lookback_days
        for i in lookback_days:
            if i<1: 
                print "Number of lookback days must be greater than zero."
                break

        self.name = self.__setName__()
        
        csvDataset.__init__(self, self.__csvPath__())
        
        self.headers = self.__setHeaders__()
        self.analysis_period = self.__setAnalysisPeriod__(analysis_period)
        self.preliminary_analyses = self.__setPreliminaryAnalyses__()
        
        print self.name, "(%s to %s)" % ( self.analysis_period[0].isoformat(), self.analysis_period[1].isoformat() )
        
    def __setName__(self):
        """
        A method to return the name of this analysis.
        """
        return self.analysis_type
    
    def __csvPath__(self):
        """
        A method to return the path to the csv file containing the analysis results.
        """
        return "%s/%s_%s.csv" % (self.analysis_dir,
                                 self.input_data.name,
                                 self.name)
    
    def __setAnalysisPeriod__(self, analysis_period):
        """
        A method to define the analysis time period. If necessary, shorten 
        requested period to available input data.
        """
        input_data_period = self.input_data.__getStoredPeriod__()
        
        if analysis_period[0]<input_data_period[0]:
            analysis_period[0] = input_data_period[0]

        if analysis_period[1]>input_data_period[1]:
            analysis_period[1] = input_data_period[1]
    
        return analysis_period 

    def __pruneData__(self, input):
        """
        A method to retain only the input data over the desired time period 
        and with the desired granularity.
        """
        output = {}
        for key in input.keys():
            values = [] 
            for row in xrange(0, len(input["Date"])):
                if not input["Date"][row]<self.analysis_period[0] and not input["Date"][row]>self.analysis_period[1]:
                    values.append( input[key][row] )
            
            output[key] = values

        return output

    def __setHeaders__(self):
        """
        A method to define the headers of the dataset.
        """
        headers = ["Date"]
        for n in self.lookback_days:
            headers.append("%s_%i" % (self.analysis_type, n))
        
        return headers
    
    def __setPreliminaryAnalyses__(self):
        """
        A method to return the previous analyses preliminary for this analysis.
        """
        return None

    def __messages__(self, key):
        """
        A method to print analysis progress to the user.
        """
        messages = { "started"  : "%s analysis begun ..." % self.name ,
                     "preliminary" : "Running preliminary analyses first:" ,
                     "finished" : "complete." }

        print messages[key]
        
    def __initialAnalysisPeriod__(self, i=0):
        """
        A method to return the initial period - in trading days - preliminary 
        for the first analysis.
        """
        if self.preliminary_analyses==None:
            return self.lookback_days[i]

        else: # find maximum time preliminary
            lookback = []
            for analysis in self.preliminary_analyses.values():
                for i in xrange(0, len(analysis.lookback_days)):
                    lookback.append(analysis.__initialAnalysisPeriod__(i))
                    
            max = 0
            for i in lookback:
                if max<i:
                    max = i
                
            return max

    def __iterations__(self):
        """
        The method to count the number of requested iterations over the input data.
        """
        return len(self.lookback_days)

    def __calculation__(self, data, i, row):
        """
        A placeholder calculation method to be defined for each 
        derived analysis class.
        """
        return 1.0
        
    def __ensureCsvExists__(self):
        """
        A method to ensure the csv data file exists.
        """
        if not os.path.isfile(self.csv_path):
            self.run()

    # public
    def run(self):
        """
        Method to run the time series analysis.
        """
        # first run any preliminary analyses
        if not self.preliminary_analyses==None:
            for analysis in self.preliminary_analyses.values():
                analysis.run()

        self.__messages__("started")
        
        # get input data
        input = { self.input_data.name : self.__pruneData__( self.input_data.__getCsvData__() ) }
        if not self.preliminary_analyses==None:
            for i in xrange(0, len(self.preliminary_analyses.keys())):
                input[self.preliminary_analyses.keys()[i]] = self.preliminary_analyses.values()[i].__getCsvData__()
                
        # fill output, loop over the requested iterations
        output = { self.headers[0] : input[self.input_data.name]["Date"] }
        
        for i in xrange(0, self.__iterations__()):
                    
            # fill initial analysis range
            start = []
            for row in xrange(0, self.__initialAnalysisPeriod__(i)):
                start.append("")

            # calculate and fill remaining entries
            results = []
            for row in xrange(self.__initialAnalysisPeriod__(i), len(input[self.input_data.name]["Date"])):
                results.append( self.__calculation__(input, i, row) )
                
            # expand single iteration, multi-value results
            if type(results[0]) is list:
                for col in xrange(0, len(results[0])):
                    this_result = []
                    for row in xrange(0, len(results)):
                       this_result.append(results[row][col])
    
                    output[self.headers[col+1]] = start + this_result

            else: # for multi-iteration, single value results
                output[self.headers[i+1]] = start + results

        self.__setCsvData__(output)
        self.__messages__("finished")


class MA(timeSeriesAnalysis):
    """
    An object to calculate the N-Day Moving Average of the closing price.
    """
    # attributes
    analysis_type = "MA"
    
    # protected
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], lookback_days=[10]):
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


class tradingSystem(timeSeriesAnalysis):
    """
    A base class to describe a generic trading system.
    """
    # attributes
    analysis_type = "tradingSystem"
    
    # protected
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, ma_lookback=[100, 300]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, ma_lookback=[150, 250, 350]):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, ma_lookback=[25, 350], min_lookback=[10, 20], max_lookback=[10, 20], atr_lookback=[20], atr_stop=2.0):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, lookback=[350], n_sigma=2.5):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, min_lookback=[55], max_lookback=[55], atr_lookback=[20], atr_stop=2.0):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, lookback=[20], n_sigma=3.0):
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
    def __init__(self, input_data, analysis_period=[a_long_time_ago, datetime.date.today()], equity=100.0, lookback=[250], confidence=0.95):
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
                x -= monthly_risk_free_rate
            
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
                x -= monthly_risk_free_rate
                
            rsq_x += (x - mean_x)*(x - mean_x)
            
        var_x = rsq_x / (n-1.0)
        
        return 12.0*mean_x, math.sqrt(12.0*var_x)
        
    def __CAGR__(self, equity, time):
        """
        A method to calculate the Compound Annual Growth Rate.
        """
        period_in_days = (time[1]-time[0]).days
        period_in_years = ( 1.0*period_in_days )/( 1.0*nominal_days_per_year )

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
            sum_x += (1.0*row)/(1.0*nominal_days_per_year) # i.e. trading years
            sum_y += math.log( input["Equity"][row] )
            n += 1
            
        mean_x = (1.0*sum_x)/(1.0*n)
        mean_y = (1.0*sum_y)/(1.0*n)
        
        res_xx = 0.0
        res_yy = 0.0
        res_xy = 0.0
        
        for row in row_range:
            x = (1.0*row)/(1.0*nominal_days_per_year)
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
            
            x -= monthly_risk_free_rate
            
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
            
            x -= monthly_risk_free_rate
            
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


# ------------------------------------------------------------
# End of file
# ------------------------------------------------------------
