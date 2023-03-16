#!/usr/bin/python3

import pandas_datareader as pdr
from datetime import datetime, date
import os, sys, copy
from pprint import pprint

class TColor:

  PINK      = '\033[95m'
  BLUE      = '\033[94m'
  GREEN     = '\033[92m'
  YELLOW    = '\033[93m'
  ORANGE    = '\033[91m'
  BOLD      = '\033[1m'
  UNDERLINE = '\033[4m'
  ENDC      = '\033[0m'
  LEFT      = '\033[D' #move one space to left?


class Stock( object ):

  week_days = [ 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN' ] 
  prev_month = 0 
  def __init__( self, summary ):
    self.summary = summary
    self.total   = []
    self.SMA_20  = []
    self.SMA_50  = []
    self.SMA_200 = []
    self.RSI     = []
    self.CMF     = []

  def percent_change( self, price_open, price_close ):
    ratio = 0.0
    if float( price_open ) > 0:
      ratio = ( float( price_close ) - float( price_open ) )/float( price_open )
    return round( ratio*100, 2 )

  def change( self, prev_close, close ):
    return float( prev_close ) - float( close )

  def calculate_base( self, data ):

    yester_chg = 0.0; prev_close = 0.0; diff = 0.0; yester_hi = 0.0; yester_lo = 0.0
    yester_HL = 0.0; prev_low = 0.0
    #for i, each_data in enumerate( reversed( data ) ):
    for i, each_data in enumerate( data ):

      if i == 0:
        prev_close  = each_data['Close']
        prev_low  = each_data['Low']
        yester_chg  = self.percent_change( prev_close, each_data['Open'] )
        yester_high = self.percent_change( prev_close, each_data['High'] )
        yester_low  = self.percent_change( prev_close, each_data['Low'] )
        yester_HL  = self.percent_change( prev_low, each_data['High'] )
      else:
        yester_chg  = self.percent_change( prev_close, each_data['Open'] )
        yester_high = self.percent_change( prev_close, each_data['High'] )
        yester_low  = self.percent_change( prev_close, each_data['Low'] )
        yester_HL  = self.percent_change( prev_low, each_data['High'] )
        prev_close  = each_data['Close']
        prev_low  = each_data['Low']

      base_arry = [ str( round( float(each_val),2) ) for each_val in [ each_data['Open'], \
		                each_data['Close'], each_data['High'], each_data['Low'], \
		                self.percent_change( each_data['Open'], each_data['Close'] ), yester_chg, yester_high, yester_HL, yester_low ] ]

      base_arry.insert( 0, each_data['Date'] )
      base_arry.insert( len(base_arry), each_data['Volume'] )
      self.total.append( base_arry )

  def calculate_CMF( self, data ):

    period = 14 
    cmf    = 0.0
    money_flow_arry = []
    volume_arry     = []
    money_flow_vol  = 0.0
    #for i, each_data in enumerate( reversed( data ) ):
    for i, each_data in enumerate( data ):

      denom     = self.change( each_data['High'], each_data['Low'] )
      numerator = self.change( each_data['Close'], each_data['Low'] ) - self.change( each_data['High'],  each_data['Close'] )

      if denom != 0.0:
        money_flow_multi = numerator/denom 
        money_flow_vol   = money_flow_multi*float( each_data['Volume'] ) 

       #print "CLOSE: ",each_data['Close'], " HIGH: ",each_data['High'], ' LOW: ',each_data['Low']
       #print "CLOSE-LOW: ", self.change( each_data['Close'], each_data['Low'] ), \
       #     " HIGH-CLOSE: ", self.change( each_data['High'], each_data['Close'] )
       #print "NUMERATOR: ",numerator, " DENOM: ",denom, ' MULTI: ',money_flow_multi
      if i <= period:
	      money_flow_arry.append( money_flow_vol )
	      volume_arry.append( float(each_data['Volume']) )

      if i < period:
        cmf = 0.0
        continue
      elif i == period:
        cmf = sum( money_flow_arry )/sum( volume_arry )
      elif i > period:
        money_flow_arry.pop(0) #pop the first value
        volume_arry.pop(0) #pop the first value
	money_flow_arry.append( money_flow_vol )
	volume_arry.append( float(each_data['Volume']) )
        cmf = sum( money_flow_arry )/sum( volume_arry )

      cmf = round( cmf, 2 )
      self.CMF.append( cmf )
 
  def calculate_SMA( self, data, indicator ):

    sma = 0.0; sma_list = []
    #for i, each_data in enumerate( reversed( data ) ):
    for i, each_data in enumerate( data ):

      if i <= indicator:
        sma_list.append( float(each_data['Close'] ) )

      if i < indicator:
        continue
      elif i == indicator:
        sma = sum( sma_list )/len( sma_list )
      elif i > indicator:
        sma_list.pop(0) #pop the first value
        sma_list.append( float(each_data['Close']) )
        sma = sum( sma_list )/len( sma_list ) 

      sma_r = round( sma, 2 )
      if indicator == 20:
        self.SMA_20.append( sma_r )
      elif indicator == 50:
        self.SMA_50.append( sma_r )
      elif indicator == 200:
        self.SMA_200.append( sma_r )

  def calculate_RSI( self, data ):

    period = 14
    prev_open = 0.0; prev_close = 0.0;
    up = 0; down = 0; RS = 0.0; prev_up = 0.0; prev_down = 0.0
    temp_up = 0.0; temp_dn = 0.0
    up_list = []; down_list = []
    for i, each_data in enumerate( data ):

      if i == 0:
        prev_close = each_data['Close']
        continue

      diff = self.change( prev_close, each_data['Close'] )
      if i <= period and diff < 0:
        temp_up += abs( diff )
        up_list.append( temp_up )

      if i <= period and diff > 0:
        temp_dn += diff
        down_list.append( temp_dn )

      if i > period and diff > 0:
        down = ( prev_down*float(period - 1) + diff )/float(period)
        up   = ( prev_up*float(period - 1) )/float(period) #since diff is positive which is going down

      if i > period and diff < 0:
        up   = ( prev_up*float(period - 1) + abs(diff) )/float(period)
        down = ( prev_down*float(period - 1) )/float(period) #since diff is negative which is going up

      prev_close = each_data['Close']

      if i < period:
        continue
      elif i == period:
        up        = up_list[-1]/float(period)
        down      = down_list[-1]/float(period)
        RS        = up/down
        prev_down = down
        prev_up   = up
      elif i > period:
        RS        = up/down
        prev_down = down
        prev_up   = up

      RSI = round(100.0 - ( 100.0/(1.0 + RS)),2)
      self.RSI.append( RSI )

  def generate_footer( self ):

    print TColor.YELLOW
    if self.summary['FiftydayMovingAverage'] is not None:
      print('50-Day: {0:<5}'.format( round( float(self.summary['FiftydayMovingAverage']), 2 ) ))
    if self.summary['TwoHundreddayMovingAverage'] is not None:
      print('200-Day: {0:<5}'.format( round( float(self.summary['TwoHundreddayMovingAverage']), 2 ) ))
    if self.summary['AverageDailyVolume'] is not None:
      print('Avg Vol: {0:<5}'.format( round( float(self.summary['AverageDailyVolume']), 2 ) ))

    if self.summary['YearRange'] is not None:
      print('YearRange: {0:<5}'.format( self.summary['YearRange'] ) )
    if self.summary['OneyrTargetPrice'] is not None:
      print('1 YR Target Price: {0:<5}'.format( round( float(self.summary['OneyrTargetPrice']), 2 ) ))
    if self.summary['PERatio'] is not None:
      print('PE Ratio: {0:<5}'.format( self.summary['PERatio'] ) )
    if self.summary['MarketCapitalization'] is not None:
      print('MarketCap: {0:<5}'.format( self.summary['MarketCapitalization'] ) )
    print

    print
    if self.summary['EBITDA'] is not None:
      print('EBITDA: {0:<5}'.format( self.summary['EBITDA'] ) )
    if self.summary['PriceBook'] is not None:
      print('PriceBook: {0:<5}'.format( round( float(self.summary['PriceBook']), 2 ) ))
    if self.summary['BookValue'] is not None:
      print('BookValue: {0:<5}'.format( round( float(self.summary['BookValue']), 2 ) ))
    if self.summary['PriceSales'] is not None:
      print('PriceSales: {0:<5}'.format( round( float(self.summary['PriceSales']), 2 ) ))
    if self.summary['ShortRatio'] is not None:
      print('ShortRatio: {0:<5}'.format( round( float(self.summary['ShortRatio']), 2 ) ))
    if self.summary['DividendYield'] is not None:
      print('DividendYield: {0:<5}'.format( round( float(self.summary['DividendYield']), 2 ) ))
    if self.summary['DividendPayDate'] is not None:
      print('DividendPayDate: {0:<5}'.format( self.summary['DividendPayDate'] ) )
    if self.summary['EarningsShare'] is not None:
      print('EarningsShare: {0:<5}'.format( round( float(self.summary['EarningsShare']), 2 ) ))

    print
    if self.summary['EPSEstimateNextQuarter'] is not None:
      print('EPS Estimate Next QTR: {0:<5}'.format( round( float(self.summary['EPSEstimateNextQuarter']), 2 ) ))
    if self.summary['EPSEstimateCurrentYear'] is not None:
      print('EPS Estimate Current YR: {0:<5}'.format( self.summary['EPSEstimateCurrentYear'] ) )
    if self.summary['EPSEstimateNextYear'] is not None:
      print('EPS Estimate Next YR: {0:<5}'.format( round( float(self.summary['EPSEstimateNextYear']), 2 ) ))
    print TColor.ENDC

  def generate_header( self ):

    print(" {:<5} {:<11} {:<7} {:<7} {:<7} {:<7} {:>7} {:>9} {:>8} {:>8} {:>8} {:>11} {:>8} {:>8} {:>8} {:>8} {:>8} {}".format( \
	  'Day', 'Date', 'Open', 'Close', 'High', 'Low', 'Chg', 'ovrChg', 'ovrHi', 'overLH', 'ovrLo', 'Vol', '20_SMA','50_SMA','200_SMA','RSI', 'CMF', TColor.ENDC))

  def print_data( self, year, month, day, each_data, SMA_20, SMA_50, SMA_200, RSI, CMF ):

    p0 = None
    if RSI > 75:
      p0 = TColor.ORANGE
    elif RSI >= 65 and RSI < 75:
      p0 = TColor.PINK
    elif RSI >= 55 and RSI < 65:  
      p0 = TColor.YELLOW
    elif RSI >= 40 and RSI < 55:
      p0 = TColor.BOLD
    elif RSI >= 25 and RSI < 40:
      p0 = TColor.BLUE
    else:
      p0 = TColor.GREEN
    
    p1 = Stock.week_days[date(int(year),int(month),int(day)).weekday()] #day
    p2 = '-'.join([str(each_data[0].year),str(each_data[0].month),str(each_data[0].day)])  #date
    p3 = each_data[1]  #open
    p4 = each_data[2]  #close
    p5 = each_data[3]  #high 
    p6 = each_data[4]  #low 
    p7 = each_data[5]  #chg 
    p8 = each_data[6]  #ovrChg 
    p9 = each_data[7]  #ovrHi 
    p10 = each_data[8] #ovrLH 
    p11 = each_data[9] #ovrLo 
    p12 = each_data[10] #Vol 
    p13 = SMA_20       #20_SMA
    p14 = SMA_50       #50_SMA
    p15 = SMA_200      #200_SMA
    p16 = RSI          #RSI 
    p17 = CMF          #CMF
    p18 = TColor.ENDC  #back to console color
    print("{} {:<5} {:<11} {:<7} {:<7} {:<7} {:<7} {:>7}% {:>7}% {:>7}% {:>7}% {:>7}% {:>11} {:>8} {:>8} {:>8} {:>8} {:>8} {}".format( p0, p1, p2, p3, p4, p5, p6, p7, p8, \
	   p9, p10, p11, p12, p13, p14, p15, p16, p17, p18 ) )

  def display( self, weekday, each_data, SMA_20, SMA_50, SMA_200, RSI, CMF ):

    year,month,day = each_data[0].year,each_data[0].month,each_data[0].day

    if weekday == 'ALL':
      self.print_data( year, month, day, each_data, SMA_20, SMA_50, SMA_200, RSI, CMF )

    elif weekday == Stock.week_days[date(int(year),int(month),int(day)).weekday()]:
      self.print_data( year, month, day, each_data, SMA_20, SMA_50, SMA_200, RSI, CMF )

    #print 'PREV_MONTH: ',Stock.prev_month,' MONTH: ',int(month)
    if weekday == 'ALL' and date( int(year),int(month),int(day) ).weekday() == 4:
      print
    elif weekday != 'ALL':
      if Stock.prev_month == int(month):
        pass
      else:
        print
    Stock.prev_month = int(month)

def convert_to_date( unicode_object ):

  year, month, day = unicode_object.encode('utf-8').split('-')

  return date( int(year), int(month), int(day) )

def convert_to_array_of_dictionaries( data, dictOfDict ):

  arrayOfDicts = []
  for top_key, v in data.to_dict().iteritems():
    k = top_key.capitalize()
    for key, val in sorted( v.iteritems() ):
      #print 'KEY: ',key.date(), 'VAL: ',v[key]
      if convert_to_date( key ) in dictOfDict:
        dictOfDict[ convert_to_date( key ) ][ k ] = v[key]
      else:
        dictOfDict[ convert_to_date( key ) ] = { }
        dictOfDict[ convert_to_date( key ) ][k] = v[key]

  for k, v in sorted(dictOfDict.iteritems()):
    v['Date'] = k
    arrayOfDicts.append( v )
  return(arrayOfDicts)

def main():

  if len(sys.argv) <= 3 or len(sys.argv) >= 6:
    print "%s <stock_symbol> <date_from> <date_to> [ day ]" % sys.argv[0]
    print "e.g. %s AA 2015-12-01 2016-05-01 FRI"
    sys.exit(1)

  symbol    = sys.argv[1].strip()
  startdate = sys.argv[2].strip()
  enddate   = sys.argv[3].strip()
  weekday   = sys.argv[4] if len(sys.argv) == 5 else 'ALL'

  dictOfDict = { }

  from_year, from_month, from_day = startdate.split('-')
  to_year, to_month, to_day = enddate.split('-')

  start = datetime( int(from_year), int(from_month), int(from_day) )
  end   = datetime( int(to_year), int(to_month), int(to_day) )

  #raw_data = pdr.get_data_google( symbol, start, end )
  chunksize = 25
  raw_data = pdr.iex.daily.IEXDailyReader( symbol.upper(), start, end, chunksize )
  data = convert_to_array_of_dictionaries( raw_data.read(), dictOfDict )

  summary = None 
  h = Stock( summary )
  h.generate_header()
  h.calculate_base( data )
  for each_indicator in [ 20, 50, 200 ]:
    h.calculate_SMA( data, each_indicator )
  h.calculate_RSI ( data )
  h.calculate_CMF ( data )

  for i, each_list in enumerate(h.total):

    if i < 14:
      h.display( weekday, each_list, 0, 0, 0, 0, 0 )
    elif i >= 14 and i < 20:
      h.display( weekday, each_list, 0, 0, 0, h.RSI[ i - 14 ], 0 )
    elif i >= 20 and i < 50:
      h.display( weekday, each_list, h.SMA_20[ i - 20 ], 0, 0, h.RSI[ i - 14 ], h.CMF[ i - 20 ] )
    elif i >= 50 and i < 200:
      h.display( weekday, each_list, h.SMA_20[ i - 20 ], h.SMA_50[ i - 50 ], 0, h.RSI[ i - 14 ], h.CMF[ i - 20 ] )
    elif i >= 200:
      h.display( weekday, each_list, h.SMA_20[ i - 20 ], h.SMA_50[ i - 50 ], h.SMA_200[ i - 200 ], h.RSI[ i - 14 ], h.CMF[ i - 20 ] )

  h.generate_header()
  print TColor.BLUE
  print 'STOCK: ' + ''.join([ c.capitalize() for c in symbol ]),
  print TColor.ENDC
  #h.generate_footer()

if __name__ == '__main__': main()
