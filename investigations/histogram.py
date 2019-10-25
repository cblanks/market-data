#!/usr/bin/python 
# Filename: histogram.py

author = "Chris Blanks"
version = 1.0

import math

class Histogram():
    """
    A simple histogram class.
    """
    # attributes

    # private
    def __init__(self, name = "Hist", xmin = 0.0, xmax = 1.0, nbins = 20):
        """
        Initialise the histogram object.
        """
        self.data = []
        self.name = name
        self.xmin = xmin
        self.xmax = xmax
        self.nbins = nbins
        self.bin_width = (self.xmax - self.xmin) / self.nbins
        self.bin_low = []
        for i in range(0, self.nbins):
            self.bin_low.append(i*self.bin_width + xmin)

    # public
    def fill(self, dataset):
        """
        Fill the histogram with data.
        """
        for i in self.bin_low:
            y = 0
            for j in dataset:
                if j>=i and j<(i+self.bin_width):
                    y+=1

            #print y
            self.data.append(y)

    def drawInTerminal(self, log=False):
        """
        Draw the histogram (on a log scale) to stdout.
        """
        # Write the histogram title
        print self.name

        # Find histogram maximum
        ymax = 0
        for i in self.data:
            if i>ymax:
                ymax = i

        # convert to log maximum
        if log:
            print ymax, 
            ymax = int(math.log(ymax))
            print ymax
        
        # Draw the histogram data
        for i in range(0, ymax):
            test = ymax-i
            print test, "\t",
            for j in self.data:
                
                if log:
                    if not j==0:
                        j = math.log(j)
                
                if test<=j:
                    print "*",
                else:
                    print " ",

            print " "

        # Draw the x-axis
        print "\t",
        for i in range(0, self.nbins) :
            if i==0:
                print 0,
            elif i==(self.nbins-1):
                print 1,
            else:
                print '.',

