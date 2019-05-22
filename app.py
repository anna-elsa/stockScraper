# coding= utf-8

from flask import Flask, request, render_template # used for web application features
from bs4 import BeautifulSoup # used for html parsing
import requests # used for url requests
import re
import xlrd # reads excel files
import locale # used for number formatting
locale.setlocale(locale.LC_ALL, 'en_US')

app = Flask(__name__)
 
# Global variable - SEC website url
secUrl = 'https://www.sec.gov'

@app.route('/', methods = ['GET', 'POST'])
def home():
	try:
		if request.method == 'POST':
			ticker = request.form['ticker'].upper()
			print ticker
			totalAssets, totalLiab, totalEquity, units = scrape(ticker)
			return render_template('home.html', ticker = ticker, units = units, totalAssets = totalAssets, totalLiab = totalLiab, totalEquity = totalEquity)
		else:
			return render_template('home.html')
	except Exception as e:
		return render_template('home.html', error = 'There was an error. This stock information may not be currently available.')

def scrape(ticker):
	try:
		url = 'https://www.sec.gov/cgi-bin/browse-edgar?CIK='+ticker+'&Find=Search&owner=exclude&action=getcompany'
		request = requests.get(url)
		
		if re.findall("No matching Ticker Symbol.", request.content):
			return

		# Find url for 10-K report & navigate there
		soup = BeautifulSoup(request.content, "html.parser")	
		table = soup.find('table',{'class':'tableFile2'})
		interactiveDataUrl = soup.find("td", text="10-K").findNext("td").find_all('a')[1].get('href')
		
		# Find url for financial statements excel file
		request = requests.get(secUrl+interactiveDataUrl)
		soup = BeautifulSoup(request.content, "html.parser")
		excelUrl = soup.find("td").find_all('a')[1].get('href')

		# Download the financial statements
		request = requests.get(secUrl+excelUrl)
		output = open('10K.xls', 'wb')
		output.write(request.content)
		output.close()

		loc = ("/Users/anna/Dropbox/Python/scraper/10K.xls") 
	  
		# To open Workbook 
		wb = xlrd.open_workbook(loc)
		
		# Locate Balance Sheet
		sheets = wb.sheet_names()
		index = findIndex(sheets, "Consolidated Balance Sheets") 
		print index
		if index == 999:
			index = findIndex(sheets, "CONSOLIDATED BALANCE SHEETS") 
		if index == 999:
			index = findIndex(sheets, "CONSOLIDATED BALANCE SHEET")
		if index == 999:
			index = findIndex(sheets, "Consolidated Balance Sheet") 
		
		balanceSheet = wb.sheet_by_index(index)

		# Determine if numbers are in thousands, millions, billions, etc.
		header = balanceSheet.cell_value(0,0)
		units = header.split('$')[2]

		# Generate the first column of the Balance Sheet (rownames)
		col = []
		for i in range(balanceSheet.nrows): 
			col.append(balanceSheet.cell_value(i, 0).encode('utf-8'))
		
		# Use findIndex to find the row numbers where our data of interest is
		assetIndex = findIndex(col, "Total assets")
		liabIndex = findIndex(col, "Total liabilities")
		equityIndex = findIndex(col, "Total stockholders’ equity")
		if equityIndex == 999:
			equityIndex = findIndex(col, "Total shareholders’ equity")
		if equityIndex == 999:
			equityIndex = findIndex(col, "Total shareholders' equity")
		if equityIndex == 999:
			equityIndex = findIndex(col, "Total equity")


		tempAssets = balanceSheet.row_values(assetIndex)[1]
		tempLiab = balanceSheet.row_values(liabIndex)[1]
		tempEquity = balanceSheet.row_values(equityIndex)[1]

		totalAssets = "$"+locale.format("%d", tempAssets, grouping=True)
		totalLiab = "$"+locale.format("%d", tempLiab, grouping=True)
		totalEquity = "$"+locale.format("%d", tempEquity, grouping=True)

		return totalAssets, totalLiab, totalEquity, units
	except Exception as e:
		return e


def findIndex(l, name):
	# l - a list of names 
	# Name - A string that will be matched to values in the list
	# findIndex function finds a specific "name" in a list of names and returns the index in which 
	# that name occurs. 

	counter = -1
	matchFound = 0

	for lname in l:
		counter = counter + 1
		if lname == name:
			matchFound = 1
			break

	if matchFound == 0:
		return 999
	else:
		return counter

# Debug Mode
if __name__ == '__main__':
	app.run(debug = True)


