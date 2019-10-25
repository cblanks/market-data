#!/usr/bin/python
# Filename : startup.py

# dependencies -----------------------------------------------
import yahooFinance as yahoo
# ------------------------------------------------------------

# initialise dataset and print welcome message ---------------
print \
"""
====================================================
 \    /       |   |   _     _   ||   Financial data
  \  /  /\    |   |  / \   / \  ||   collection &
   \/  /  \   |___| |   | |   | ||   analysis.
   /  /____\  |   | |   | |   | ||
  /  /      \ |   |  \_/   \_/  |/   %s
 /            |   |             o    Version %.1f

The following saved datasets are listed in the 
'd' dictionary:
""" % (yahoo.author, yahoo.version)

d = yahoo.financeDatasetGroup()
d.summarise()

print \
"""
For usage information type 'help(yahoo)'.
====================================================
"""

# End of File
