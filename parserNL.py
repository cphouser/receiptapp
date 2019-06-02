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
import operator

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

#-----------------------------------------------------------------------------------

def acertainDateValue3(date_string):
    """
    given a line, if a date exists in the format dd/mm/yy hh:mm, 
    return it as a datetime object.

    """
    #date = datetime.strptime,(date_string, "%m-%d-%Y %H:%M")
    #date = datetime.strptime(date_string, '%m/%d/%Y')
    
    #print(date_string)
    i = date_string.find('/')
    j = date_string.find('/', i+1)

    l = date_string.find('-')
    m = date_string.find('-', i+1)


    o = date_string.find(':')
    p = date_string.find(':', o+1)
    #print(l)

    if o > 0:
        if(date_string[o+1:o+3].isdigit() == False):
            date_string = date_string[0:o-3]
            #print(date_string)
        if(date_string[o-2:o].isdigit() ==  False):
            date_string = date_string[0:o-3]
            #print(date_string)

    if p > 0:
        if(date_string[p+1:p+3].isdigit() == False):
            date_string = date_string[0:p]
            #print(date_string)

    k = date_string.count(':')

    if all(dash > 0 for dash in [i, j]):
        if k == 0:
            date = datetime.strptime(date_string, "%m/%d/%Y")
        elif k == 1:
            date = datetime.strptime(date_string, "%m/%d/%Y %H:%M")
            #date = change_to_24(time, date)
        elif k == 2:
            date = datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S")
            #date = change_to_24(time, date)
    elif all(amper > 0 for amper in [l, m]):
        if k == 0:
            date = datetime.strptime(date_string, "%m-%d-%Y")
        elif k == 1:
            date = datetime.strptime(date_string, "%m-%d-%Y %H:%M")
            #date = change_to_24(time, date)
        elif k == 2:
            date = datetime.strptime(date_string, "%m-%d-%Y %H:%M:%S")
            #date = change_to_24(time, date)
    
    return date

def parseLine4(row):
	time_change = 0

	if len(row) < 4:
		return ('none', row)

	if(row.count('-') == 2 or row.count('/') == 2):
		if 'PM' in row or 'pm' in row:
			time_change = 1
		# take away the non-numeric chars preceding the date
		if not(row[0].isnumeric()):
			for c in row:
				if(c.isnumeric()):
					break
				row = row.strip(c)
			#print(row)
		row.replace('Time: ', '')#print(row)

		if row.count(':') == 0:
			row = row[0:10]
		elif row.count(':') == 1:
			row = row[0:16]
		elif row.count(':') == 2:
			row = row[0:18]

		date = acertainDateValue3(row)
		#print(date)
		if time_change:
			date = date.replace(hour = date.hour + 12)
		#print(date)
		return ('date', date)

	if any(c.islower() for c in row) and '.' not in row:
		#print(row)
		return('head', row)
	
	if row.count('(') == 1 and row.count(')') == 1:
		return('head', row)
	
	name, price = separatePrice1(row)

	if all(val is not None for val in [name, price]):
		return tryPrice1(name, price)
	else:
		return ('none', (name, price))

# NOTE to self: just need to work on the date recognition
def parseNL(lines):
    end = False
    end_head = False
    found_tax = False
    items = {} 
    
    for line in lines:

        index = len(items)

        if len(line) <= 1 or line.isspace():
            continue
        #print(line)
        try:
        	tag, item = parseLine4(line)
        except:
            #print("Invalid Data Passed in")
            #print(i)
            tag = 'none'
            item = line

        #print((tag, item))
        if tag == 'date':
            items.update({index: (tag, item)})
            continue
       
        if(item[0] is not None):
        	if 'BALANCE' in item[0]:
        	   tag = 'fsum'
        
        if tag == 'fsum':
                items.update({index: (tag, item)})
                end = True
                continue
        elif found_tax and 'TOTAL' in item:
        		tag = 'errr'
        		end = True

        if tag == 'errr':
        	items.update({index: (tag, item)})
        	continue
        
        #print(fuzz.partial_ratio('SE Member', 'SR Member 111847974436'))
        if fuzz.partial_ratio('Your Checker', item) > 80:
        	tag = 'none'
        	end_head = True

        
        if end:
            if type(item) is tuple:
                if item[1] is None:
                    item = item[0]
                elif item[0] is None:
                    item = item[1]
                else:
                    item = item[0] + str(item[1])
            items.update({index: ('foot', item)})
            continue
        elif not end:
            if tag == 'item':
                if 'TAX' in item:
                    found_tax = True
                items.update({index: (tag, (*item, None))})
                continue
            if tag == 'none':
                if not end_head:
                    tag = 'head'
            if tag == 'head':
            	if end_head:
            		tag = 'none'
            items.update({index: (tag, item)})
    
    return items


if __name__ == '__main__':
	
	img_list, history_list = findImages()

	#for i in range(0, len(img_list)):
	#	print((i, img_list[i]))

	receipt_dict = {}

	# NewLeaf receipt indicies: 4-7, 47-48

	test = tesseractImage('img/'+ img_list[47]).splitlines()
	empty = 0
	#for i in test:
	#	if i.isspace() or len(i) <= 1:
	#		empty += 1
	#	else:
	#		print(i)
	#print(len(test))
	#print(empty)

	parsed = parseNL(test)

	#print(parsed)

	for i in parsed:
		print(parsed[i])
	print(len(parsed))