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
# mod it by adding second
def acertainDateValue(date_string):
    """
    given a line, if a date exists in the format dd/mm/yy hh:mm, 
    return it as a datetime object.

    """
    CENTURY = 2000
    i = date_string.find('/')
    j = date_string.find('/',i+1)
    k = date_string.find(':')
    l = date_string.find(':', k+1)
    
    if date_string[i+1:i+3] == date_string[j-2:j]:
        month = int(date_string[i-2:i])
        day = int(date_string[j-2:j])
        year = int(date_string[j+1:j+3])
        hour = int(date_string[k-2:k])
        minute = int(date_string[k+1:k+3])
        
        if l is not None:
            second = int(date_string[l+1:l+3])
    else:
        return None
    if year > 99 or month > 12 or day > 31 or hour > 23 or minute > 59 or second > 59:
        return None
    elif l is not None: 
        return datetime(year+CENTURY,month,day,hour,minute,second)
    else:
        return datetime(year+CENTURY,month,day,hour,minute,second)

def parseLine5(line):
    #don't consider any line with less than 4 characters
    if len(line) < 4:
        return ('none', line)

    #if the line has two "/" and one ":", it might be the transaction date
    if line.count('/') == 2 and line.count(':') == 2:
        date = acertainDateValue(line)
        return ('date', date)

    if (any(i.islower() for i in line) and '.' not in line):
            return ('catg', line)

    #try extracting a price from the right side
    name,price = separatePrice1(line)

    #if no price it might be a category
    if price is None:
        '''
        #exclude lines that include QTY
        fuz = fuzz.partial_ratio('QTY',name)
        if fuz > 60:
            return ('none', line)
        '''
        #safeway categories are uppercase
        #if (any(not i.isupper() for i in line)):
         #   return ('catg', line)

        #otherwise discard
        return ('none', line)

    #ignore if theres no item name
    elif name is None or '@' in line:
        return ('none', line)

    else: return tryPrice1(name, price)

def parseGO(lines):
    # rebecca: deleted some lines
    def excludeMatch(name):
        """
        check for keywords in item field
        """
        list_end = 'BALANCE'
        if fuzz.partial_ratio(list_end,name) > 90:
            return 'fsum'
        return 'item'

    #initiate flags for iterating over lines
    category_head = None
    ended = False
    end_header = False

    #return lines as a dict, keyed by line number
    items = {}
    for line in lines:
        index = len(items)
        
        #discard all lines with less than two characters
        if len(line) <= 1:
            continue
        
        tag, item = parseLine5(line)
        #print(index, tag, item, sep='\t')

        if all(i.isdigit() or i.isspace() for i in line):
            end_header = True

        if tag == 'date':
            items.update({index: ('date', item)})
            continue

        elif ended is True:
            items.update({index: ('foot', line)})
            continue

        if not end_header:
            items.update({index: ('head', line)})
            continue

        if tag == 'catg':
            category_head = item
            items.update({index: ('catg', item)})
            continue

        if category_head is None: 
            items.update({index: ('head', line)})
            continue
        
        if tag == 'errr':
            items.update({index: ('errr', (*item, category_head))})
            continue

        if type(item) is tuple:
            name, _ = item
            not_item = excludeMatch(name)
            if not_item == 'fsum':
                items.update({index: ('fsum', (*item, 'SUM'))})
                ended = True
            elif not_item == 'item':
                if 'TAX' in name:
                    items.update({index: ('item', (*item, 'TAX'))})
                else:
                    items.update({index: ('item', (*item, category_head))})
            else:
                items.update({index: (not_item, (*item, category_head))})
        else:
            items.update({index: (tag, item)})
    return items


if __name__ == '__main__':
	
	img_list, history_list = findImages()

	#for i in range(0, len(img_list)):
	#	print((i, img_list[i]))

	# Grocery Outlet receipt indicies: 23,24

	test = tesseractImage('img/'+ img_list[24]).splitlines()
	empty = 0
	#for i in test:
	#	if i.isspace() or len(i) <= 1:
	#		empty += 1
	#	else:
	#		print(i)
	#print(len(test))
	#print(empty)

	parsed = parseGO(test)

	#print(parsed)

	for i in parsed:
		print(parsed[i])
	print(len(parsed))