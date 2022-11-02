from xmlrpc.client import ResponseError
from django.http import JsonResponse
from datetime import date
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import csv ,operator ,json
import os
import glob
from nsepy.derivatives import get_expiry_date
from datetime import timedelta
from nsepy import get_index_pe_history
from nsepy import get_history
from nsepy import history
import json

@api_view(['GET'])
def getExpiryDatesList(request):
    
    expiryDates = []
    currentYear = todays_date = date.today().year
    currentMonth = todays_date = date.today().month
    for monthCheck in range(currentMonth,13):
        expiry = get_expiry_date(year=currentYear, month=monthCheck)
        dates = list(expiry)
        expiryDates = expiryDates + dates
    expiryDates.sort()
    datejson = json.dumps(expiryDates, indent=4, sort_keys=True, default=str)
    
    return Response(datejson)

@api_view(['GET'])
def getOptionOI(request,symbol,expiryDate):

    dfPE = pd.DataFrame()    
    dfCE = pd.DataFrame()
    
    currentYear = int(date.today().year)
    currentMonth = int(date.today().month)
    currentDate = int(date.today().day)
    previous_close = round(get_history(symbol=symbol, start=date(currentYear,currentMonth,currentDate) + timedelta(days=-2), end=date(currentYear,currentMonth,currentDate))["Close"].iloc[0])
    
    for price in range(5*round(previous_close*.85/5),5*round(previous_close*1.15/5),5):
        stock_opt = get_history(symbol=symbol,
                            start=date(currentYear,currentMonth,currentDate) + timedelta(days=-60),
                            end=date(currentYear,currentMonth,currentDate),
                            option_type="PE",
                            strike_price=price,
                            expiry_date=date(int(expiryDate[0:4]),int(expiryDate[5:7]),int(expiryDate[8:10])))
        dfPE = dfPE.append(stock_opt)
    dfPE = dfPE.drop(['Option Type','Expiry','Symbol','Strike Price','Open','High','Low','Close','Last','Settle Price','Number of Contracts','Turnover','Premium Turnover','Underlying'], axis=1)
    dfPE = dfPE.groupby('Date').sum()
    dfPE = dfPE[dfPE['Open Interest'] > 0]
    dfPE = (json.loads(dfPE.to_json(orient='table')))["data"]
    
    for price in range(5*round(previous_close*.85/5),5*round(previous_close*1.15/5),5):
        stock_opt = get_history(symbol=symbol,
                            start=date(currentYear,currentMonth,currentDate) + timedelta(days=-60),
                            end=date(currentYear,currentMonth,currentDate),
                            option_type="CE",
                            strike_price=price,
                            expiry_date=date(int(expiryDate[0:4]),int(expiryDate[5:7]),int(expiryDate[8:10])))
        dfCE = dfCE.append(stock_opt)
    dfCE = dfCE.drop(['Option Type','Expiry','Symbol','Strike Price','Open','High','Low','Close','Last','Settle Price','Number of Contracts','Turnover','Premium Turnover','Underlying'], axis=1)
    dfCE = dfCE.groupby('Date').sum()
    dfCE = dfCE[dfCE['Open Interest'] > 0]
    dfCE = (json.loads(dfCE.to_json(orient='table')))["data"]
    
    return Response({"PE" : dfPE , "CE" : dfCE})