#!/usr/bin/python
# Filename : getYahooFinanceData.py

import datetime, urllib

today = datetime.date.today()
ages_ago = datetime.date(1897, 1, 1) # the year J.J. Thomson discovered the electron.

# a list of indices { "yahoo label" : "index description" }
indices = { "FTSE"  : "London FTSE 100 index" ,
            "FCHI"  : "Paris CAC 40"          ,
            "CCSI"  : "Cairo EGX 70 index"    }

for index in indices.keys():

    url_query = """\
http://ichart.finance.yahoo.com/table.csv?s=%sE%s&d=%i&e=%i&f=%i&g=d&a=%i&b=%i&c=%i&ignore=.csv\
""" % ("%5", # following yahoo's standard query string
       index, # yahoo's code for this index
       today.month, today.day, today.year, 
       ages_ago.month, ages_ago.day, ages_ago.year) 

    file_name = "%s.csv" % index

    urllib.urlretrieve(url_query, file_name)

# End of file

