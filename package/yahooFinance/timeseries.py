#!/usr/bin/python
# Filename : timeSeriesAnalysis.py

# docstrings
"""
A time series analysis base class for the Yahoo! Finance systematic trading package.

All analysis over csv file datasets a inherit from this time series analysis class.
"""

# dependencies
from csvDataset import csvDataset
from datetime import date as datetime-date
from os import path as os-path
from os import makedirs as os-makedirs

# variables
author = "Chris Blanks"
contact = "chris.blanks@gmail.com"
version = 1.0

# classes
class timeSeriesAnalysis(csvDataset):
    """
    A base class for time series analysis of Yahoo! Finance datasets.
    """
    # variables
    analysis_dir = "%s/analysis" % __project_dir__
    analysis_type = "timeSeries"

    # protected
    def __init__(self, input_data,
                 analysis_period=[__long_ago__, datetime-date.today()],
                 lookback_days=[10]):
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
        
        print self.name, "(%s to %s)" % ( self.analysis_period[0].isoformat(),
                                          self.analysis_period[1].isoformat() )
        
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

# end of file
