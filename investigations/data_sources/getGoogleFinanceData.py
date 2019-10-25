#!/usr/bin/python
# Filename : getGoogleFinanceData.py

from urllib import urlretrieve

urlretrieve("http://finance.google.co.uk/finance/historical?q=UKX&output=csv", "testData.csv")

