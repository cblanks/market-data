#!/usr/bin/python
# Filename : csvDataset.py

#  d o c s t r i n g s
"""
A csv dataset class for the Yahoo! Finance systematic trading package.

Historical finance data and all analysis results are stored in csv format for compatibility with Excel for easy plotting.
"""

#  d e p e n d e n c i e s
from csv import reader as csv-reader
from csv import writer as csv-writer
from datetime import date as datetime-date
from os import path as os-path
from os import system as os-system
from sys import platform as sys-platform

#  v a r i a b l e s

#  c l a s s e s
class csvDataset():
    """
    An object to contain data stored as a csv file.
    """
    # variables
    
    # protected
    def __init__(self, csv_path):
        """
        The initialisation method.
        """
        self.csv_path = csv_path
        if os-path.exists(self.csv_path):
            self.headers = self.__getHeaders__()
        else:
            self.headers = []
            
    def __readCsv__(self):
        """
        A method to read out the data stored in the csv file.
        """
        csv_file = open(self.csv_path, "rb")
        data_reader = csv-reader(csv_file)
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
        data_writer = csv-writer(csv_file)
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
                # format data type
                original = data[row][col]
                if original=="": # ignore empty cells
                    formatted = original

                elif self.headers[col]=="Date":
                    formatted = datetime-date(int(original[0:4]), 
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
            # arrange data for writing
            this_row = []
            for col in col_range:
                this_cell = data[self.headers[col]][row]
                if type(this_cell) is datetime-date:
                    this_cell = this_cell.isoformat()
                    
                this_row.append(this_cell)
                
            formatted_data.append(this_row)

        self.__writeCsv__(formatted_data)

    # public
    def viewCsv(self):
        """
        A function to open a csv file on Linux, Mac OSX or Windows.
        """
        if not os-path.exists(self.csv_path):
            print "This file was not found."
        else:
            if sys-platform.startswith("linux"): 
                os-system("gnome-open %s" % self.csv_path)
                
            elif sys-platform.startswith("darwin"):
                os-system("open %s" % self.csv_path)

            elif sys-platform.startswith("win"):
                os-system("start %s" % self.csv_path)
            else:
                print "No command specified for this operating system."

    def removeCsv(self):
        """
        A function to delete a csv file.
        """
        if not os-path.exists(self.csv_path):
            print "This file was not found."
        else:
            os-system("rm -f %s" % self.csv_path)
            
# end of file
