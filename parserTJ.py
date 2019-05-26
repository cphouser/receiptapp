#adapted from example:
#https://www.learnopencv.com/deep-learning-based-text-recognition-ocr-using-tesseract-and-opencv/
import cv2
import sys
#requires Tesseract 4.0 installed
import pytesseract
import json
import csv
from os import listdir
from datetime import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re

# BORROW
def findImages(img_dir='./img'):
    img_files_list = listdir(path=img_dir)

    history_list = []
    if 'history.csv' in img_files_list:
        img_files_list.remove('history.csv')
        with open(img_dir + '/history.csv', 'r', newline='') as f:
            reader = csv.reader(f, lineterminator='\n')
            for history_entry in reader:
                if history_entry[0] in img_files_list:
                    history_list.append(history_entry[0])
                    img_files_list.remove(history_entry[0])
                    #print(history_entry,' removed from img_files_list')
    else:
        pass
        #print('no history file found')
    return img_files_list,history_list

# BORROW
def tesseractImage(filepath):
    """
    run tesseract ocr on image at filepath, return text as string
    """
    # Read image from disk
    im = cv2.imread(filepath, cv2.IMREAD_COLOR)

    # Run tesseract OCR on image
    # '-l eng'  for using the English language
    # '--oem 1' for using LSTM OCR Engine
    if sys.platform.startswith('win32'):
        pytesseract.pytesseract.tesseract_cmd = \
                'C:\\Program Files\\Tesseract-OCR\\tesseract'#windows dir
    elif sys.platform.startswith('linux'):
        pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'

    text = pytesseract.image_to_string(im, config='-l eng --oem 1 --psm 3')
    return text

# MOD IT
def acertainDateValue(date_string):
    """
    given a line, if a date exists in the format dd/mm/yy hh:mm, 
    return it as a datetime object.

    """
    #date = datetime.strptime(date_string, "%m-%d-%Y %H:%M")
    #date = datetime.strptime(date_string, '%m/%d/%Y')
    
    
    i = date_string.find('/')
    j = date_string.find('/', i+1)
    k = date_string.count(':')

    if all(dash is not None for dash in [i, j]):
    	if k == 0:
    		date = datetime.strptime(date_string, "%m/%d/%Y")
    	elif k == 1:
    		date = datetime.strptime(date_string, "%m/%d/%Y %H:%M")
    	elif k == 2:
    		date = datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S")
    else:
    	if k == 0:
    		date = datetime.strptime(date_string, "%m-%d-%Y")
    	elif k == 1:
    		date = datetime.strptime(date_string, "%m-%d-%Y %H:%M")
    	elif k == 2:
    		date = datetime.strptime(date_string, "%m-%d-%Y %H:%M:%S")
    return date
    


# BORROW
def lastDigit(string):
    """
    given a string, find the last (closest to end) numeric character
    and return the index. return -1 if no characters are numeric
    """
    for idx in range(-1, -len(string), -1):
        if string[idx].isdigit(): return len(string) + idx; 
        elif len(string) + idx == 0: return -1
    return -1

# BORROW
def firstDigit(string):
    """
    given a string which ends in some number of numeric characters, 
    find the first (closest to beginning) numeric character of these
    and return its index
    """
    for idx in range(-1, -len(string), -1):
        #print('>>',idx,string[idx])
        if string[idx].isdigit(): continue
        else: return len(string) + idx + 1
    else: return 0

# BORROW
def priceAsInt1(price_string):
    """
    convert safeway price strings to int where value is number of cents
    """
    #convert comma to period and find last period (closest to end)
    price_string = price_string.replace(',','.')
    i = price_string.rfind('.')
    #if there are no numbers to the right of the period, find the next
    #to last period
    if i == len(price_string) - 1 or not price_string[i+1].isdigit():
        price_string = price_string[:i]
        i = price_string.rfind('.')
    
    #find the last whitespace (before the period if it exists)
    j = price_string[:i].rfind(' ') if i != -1 \
            else price_string.rfind(' ')

    #find the last digit in the string, return -1 if it does not exist
    k = lastDigit(price_string)
    if k == -1: return None

    #if there is no whitespace, find the first digit iterating backwards
    #from the last digit
    if j == -1: j = firstDigit(price_string[:k])

    #if there isn't a period, treat isolated string of digits as the intprice
    if i == -1:
        if price_string[j:k+1].isdigit(): return int(price_string[j:k+1])
        else: 
            i = firstDigit(price_string[:k])
            #print(price_string,'**',i,'**',k)
            return int(price_string[i:k+1])

    #treat digits left of period as dollars, right of period as cents
    dollars = ''
    cents = ''
    for digit in (price_string[j+1:i]):
        if digit.isdigit(): dollars += digit
    for digit in (price_string[i+1:i+3]):
        if digit.isdigit(): cents += digit

    #return total cents
    return int(dollars)*100 + int(cents)

# BORROW
def separatePrice1(line):
    """
    look for at least 4 non-alphabet characters near the end of the 
    """
    letter_flag = 0
    for i in range(-1, -len(line), -1):
        if line[i].isalpha():
            #detect first alphabet character
            if letter_flag == 0: letter_flag = i; continue

            #if second alphabet char is less than 4 
            #chars left of the first there isn't a price
            if letter_flag > -3 and -(i - letter_flag) < 4:
                return (line,None) 
            else:
                split = i+2 if i+1 == letter_flag else i+1
                if len(line[split:]) > 2:
                    return (line[:split], line[split:])
                else: break

    #can't find an item
    return (None,line)

# BORROW
def tryPrice1(name, price): 
    
    #given a separated name and price, check whether the price can be
    #read as an int.
    
    try:
        int_price = priceAsInt1(price)
    except ValueError:
        print('Could not parse ', price, ' as int')
        return ('errr', (name, price))
    else:
        if int_price is None:
            return ('errr', (name, price))
        else:    
            return ('item', (name, int_price))

def parseLine2(row):
	if(len(row) < 4):
		return('none', row)
	
	if(row.count('-') == 2 and row.count(':') == 1):
		row = row[0:16]
		date = acertainDateValue(row)
		#print(date)
		return ('date', date)
	#elif(row.count('/') == 2 and row.count(':') == 2):
	#	row = row[0:18]
	#	#print(row)
	#	date = acertainDateValue(row)
	#	return ('date', date)
	elif(row.count('/') == 2):
		row = row[0:10]
		#print(row)
		date = acertainDateValue(row)
		#print(date)
		return ('date', date)
	
	if(fuzz.partial_ratio('TRADER JOES', row) >= 91):
		#print(line)
		return ('head', 'Trader Joes')
	
	if('OPEN' and 'DAILY' in row):
		return('head', row)

	if('FLOZ' in row or '@' in row):
		return('none', row)
	
	if any(c.islower() for c in row):
		return ('head', row)
	
	name, price = separatePrice1(row)

	if all(val is not None for val in [name, price]):
		return tryPrice1(name, price)
	else:
		return ('foot', (name, price))

def parseTJ(lines):
	end = False
	items = {} 
	for line in lines:
		index = len(items)

		if len(line) <= 1:
			continue

		try:
			tag, item = parseLine2(line)
		except:
			#print("Invalid Data Passed in")
			#print(item)
			items.update({index: ('none', item)})

		if not end:
			if tag == 'item':
				#print(fuzz.ratio('CR', 'CRV'))
				if fuzz.ratio('CR', item[0]) >= 80:
					tag = 'none'
				elif fuzz.ratio('SUBTOTAL', item[0]) == 100:
					tag = 'subt'
				elif fuzz.ratio('TOTAL', item[0]) == 100:
					tag = 'tsum'
				else:
					items.update({index: (tag, item)})
			if tag == 'head':
				items.update({index: (tag, item)})
			#if tag == 'foot':
			#	items.update({index: ('foot', item)})
			if tag == 'none':
				items.update({index: (tag, item)})
			if tag == 'subt':
				items.update({index: (tag, item)})
			if tag == 'tsum':
				items.update({index: (tag, item)})
				end = True
		else:
			if tag == 'date':
				items.update({index: (tag, item)})
			else:
				items.update({index: ('foot', item)})
	
	return items

if __name__ == '__main__':
	    # Uncomment the line below to provide path to tesseract manually
	    # pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'
	    
	    img_list, history_list = findImages()
	    
	    #print('  Images to Scan:', *img_list, sep='\n')
	    #print('  Images in History File:', *history_list, sep='\n')
	    receipt_dict = {}
	    #for each image found in /img folder
	    one = tesseractImage('img/'+ img_list[24]).splitlines()
	    #print(one)
	    for i in one:
	    	print(i)

	    parsed = parseTJ(one)
	    for i in parsed:
	    	print(parsed[i])

	    #two = tesseractImage('img/'+ img_list[20]).splitlines()
	    #print(two)
	    #print(type(two))
	    #print(parseTJ(two))
	        
    


