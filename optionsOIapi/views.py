from datetime import date, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import csv ,operator ,json, glob, warnings, os
from nsepy.derivatives import get_expiry_date
from nsepy import get_index_pe_history, get_history, history

warnings.simplefilter('ignore')

@api_view(['GET'])
def getExpiryDatesList(request):
    
    # expiry date list to store all expiry dates of futures and options till year end
    expiryDates = []

    # retrieving current month and year
    currentYear = todays_date = date.today().year
    currentMonth = todays_date = date.today().month

    # iterating through expiry dates for every month and appending in fianl list that is expiryDates
    for monthCheck in range(currentMonth,13):
        # expiry variable is a set of datetime variables of several expiry dates
        expiry = get_expiry_date(year=currentYear, month=monthCheck)
        
        # converting the set to a list
        dates = list(expiry)
        
        #appending the dates to final list that is expiryDates 
        expiryDates = expiryDates + dates
    
    # sorting the final list
    expiryDates.sort()

    # converting all datetime values in list to string and storing it as dictionaries and appending these to a list which is later returned.
    expiryDatesList=[]
    for i in range(len(expiryDates)):
        expiryDatesList.append({"date": str(expiryDates[i])})
    
    return Response(expiryDatesList)

@api_view(['GET'])
def getOptionOI(request,symbol,expiryDate):

    # creating dataframes for put and call options
    dfPE = pd.DataFrame()    
    dfCE = pd.DataFrame()
    
    # gives current date, month and year
    currentYear = int(date.today().year)
    currentMonth = int(date.today().month)
    currentDate = int(date.today().day)

    # get closing price of that ticker for the previous trading session
    previous_close = round(get_history(symbol=symbol, start=date(currentYear,currentMonth,currentDate) + timedelta(days=-4), end=date(currentYear,currentMonth,currentDate))["Close"].iloc[0])
    
    # running the Strike price from 85% to 115% of current price of the ticker and rounded off to nearest 5
    for price in range(5*round(previous_close*.85/5),5*round(previous_close*1.15/5),5):

        # retrieving historical OI data for each strike price in the above for loop
        stock_opt = get_history(symbol=symbol,
                            start=date(currentYear,currentMonth,currentDate) + timedelta(days=-60),
                            end=date(currentYear,currentMonth,currentDate),
                            option_type="PE",
                            strike_price=price,
                            expiry_date=date(int(expiryDate[0:4]),int(expiryDate[5:7]),int(expiryDate[8:10])))
        
        # we put dfPE = dfPE.append() again because append only returns new DataFrame, doesn't change the old one
        dfPE = dfPE.append(stock_opt)
    
    # dropping off non relevant columns from Put Option's DataFrame
    dfPE = dfPE.drop(['Option Type','Expiry','Symbol','Strike Price','Open','High','Low','Close','Last','Settle Price','Number of Contracts','Turnover','Premium Turnover','Underlying'], axis=1)
    
    # group entries by date and sum the OI and change in OI
    dfPE = dfPE.groupby('Date').sum()

    # only keep those entries where OI is positive and remove strike prices where there is no OI available
    dfPE = dfPE[dfPE['Open Interest'] > 0]

    # convert the dataframe the a json object
    dfPE = (json.loads(dfPE.to_json(orient='table')))["data"]
    
    # running the Strike price from 85% to 115% of current price of the ticker and rounded off to nearest 5
    for price in range(5*round(previous_close*.85/5),5*round(previous_close*1.15/5),5):

        # retrieving historical OI data for each strike price in the above for loop
        stock_opt = get_history(symbol=symbol,
                            start=date(currentYear,currentMonth,currentDate) + timedelta(days=-60),
                            end=date(currentYear,currentMonth,currentDate),
                            option_type="CE",
                            strike_price=price,
                            expiry_date=date(int(expiryDate[0:4]),int(expiryDate[5:7]),int(expiryDate[8:10])))
        
        # we put dfPE = dfPE.append() again because append only returns new DataFrame, doesn't change the old one
        dfCE = dfCE.append(stock_opt)

    # dropping off non relevant columns from Call Option's DataFrame
    dfCE = dfCE.drop(['Option Type','Expiry','Symbol','Strike Price','Open','High','Low','Close','Last','Settle Price','Number of Contracts','Turnover','Premium Turnover','Underlying'], axis=1)
    
    # group entries by date and sum the OI and change in OI
    dfCE = dfCE.groupby('Date').sum()

    # only keep those entries where OI is positive and remove strike prices where there is no OI available
    dfCE = dfCE[dfCE['Open Interest'] > 0]

    # convert the dataframe the a json object
    dfCE = (json.loads(dfCE.to_json(orient='table')))["data"]
    
    # return it as a dictionary with the keys of Put and Call Options as PE and CE respectively and their respective values as their DataFrames
    return Response({"PE" : dfPE , "CE" : dfCE})

@api_view(['GET'])
def getFutureOI(request,symbol,expiryDate):

    # Creating dataframe for returning Open Interest of Ticker Futures Date Wise.
    df = pd.DataFrame()
    
    # Getting current Date, Month and Year
    currentYear = int(date.today().year)
    currentMonth = int(date.today().month)
    currentDate = int(date.today().day)
    
    # Getting Historical Data for Future OI from nsepy library 
    stock_opt = get_history(symbol=symbol,
                        start=date(currentYear,currentMonth,currentDate) + timedelta(days=-60),
                        end=date(currentYear,currentMonth,currentDate),
                        futures = True,
                        # converting date string to datetime format
                        expiry_date=date(int(expiryDate[0:4]),int(expiryDate[5:7]),int(expiryDate[8:10])))

    # Dropping non relevant attributes allow date, OI and change in OI
    df = stock_opt.drop(['Expiry','Symbol','Open','High','Low','Close','Last','Settle Price','Number of Contracts','Turnover','Underlying'], axis=1)
    
    # orient is set to tables to group all data together date wise, which gives schema and data and then we take the data part
    df = (json.loads(df.to_json(orient='table')))["data"]

    return Response({"Futures" : df})
    