#!/usr/bin/python
# Filename : returnsAnalysis.py

"""
An analysis project usign ROOT and RooFit to study returns from a trading strategy.
Contains the following class definitions:
o 'TBC'
"""

# dependencies --------------------------------------------------
import math, os
from yahooFinance import csvDataset, project_dir
from ROOT import gROOT, gStyle, TCanvas, TH1F, TF1, TMath
from ROOT import RooFit, RooArgList, RooDataHist, RooRealVar, RooGaussian, RooBreitWigner, RooVoigtian, RooPlot


# atttributes ---------------------------------------------------
author = "Chris Blanks"
version = 1.0


# macro ---------------------------------------------------------
gROOT.SetStyle( "Plain" )
gStyle.SetOptFit(1011)

canv = TCanvas("c1","c1",200,10,700,500)
csvdata = csvDataset("%s/analysis/FTSE_Donchian.csv" % project_dir )
data = csvdata.__getCsvData__()

name = ["returns", "logReturns"]
n_bins = 100
for i in range(0, len(name)):
    hist = TH1F("hist",name[i],n_bins, -0.1, 0.1)

    for j in range(1, len(data["Equity"])):
        x0 = data["Equity"][j-1]
        x1 = data["Equity"][j]
        if not x0==x1 and type(x0) is float:
            r = 0.0
            if name[i]=="logReturns":
                r = math.log(x1/x0)
            else:
                r = 1.0 - (x1/x0)
            
            hist.Fill( r )
        
    hist.Draw()
    """
    #model = TF1("g", "[0]*TMath::Gaus(x, [1], [2])")
    #model = TF1("g", "[0]*TMath::BreitWigner(x, [1], [2])")
    model = TF1("g", "[0]*TMath::Voigt(x, [2], [1])")
    model.SetParameter(0, hist.Integral())
    model.SetParameter(1, 0.0)
    model.SetParameter(2, 0.01)
    hist.Fit(model)
    
    """
    x = RooRealVar("x","x",-1000.0,1000.0)
    roodata = RooDataHist("roodata", "equity dataset", RooArgList(x), hist)
    frame = x.frame()
    
    mass = RooRealVar("mass","mass",0.0,-10.0,10.0)
    width = RooRealVar("width","width",0.01,-10.0,10.0)
    s = RooRealVar("s","s",0.005,-10.0,10.0)
    #model = RooGaussian("gaus", "gaus", x, mass, width)
    #model = RooBreitWigner("bw", "bw", x, mass, width)
    model = RooVoigtian("voigt", "voigt", x, mass, width, s)

    fit_result = model.fitTo(roodata, RooFit.Save())
    
    roodata.plotOn(frame)
    #roodata.statOn(frame)
    model.plotOn(frame)
    model.paramOn(frame, roodata)
    frame.Draw()
    chisq = frame.chiSquare()
    ndf = n_bins
    print "------> Fit Quality:", TMath.Prob(chisq, ndf)
    
    canv.Update()
    canv.SaveAs("%s.png" % name[i] )

    del hist

