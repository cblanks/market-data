from distutils.core import setup

setup( name             = "MarketDataProject" ,
       version          = "0.1" ,
       author           = "Christopher G. Blanks" ,
       author_email     = "chris.blanks@gmail.com" ,
       packages         = ["yahooFinance", "yahooFinance.test"] ,
       scripts          = ["bin/create_portfolio.py","bin/test_strategy.py"] ,
       url              = "http://pypi.python.org/pypi/TowelStuff/" ,
       license          = "LICENSE.txt" ,
       description      = "Useful towel-related stuff." ,
       long_description = open("README.txt").read() ,
       install_requires = [ "ROOT >= 5.32" ] )
