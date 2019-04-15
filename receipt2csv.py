#adapted from example:
#https://www.learnopencv.com/deep-learning-based-text-recognition-ocr-using-tesseract-and-opencv/

import cv2
import sys
#requires Tesseract 4.0 installed
import pytesseract
import csv
from datetime import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def acertainDateValue(date_string):
    """
    if a date exists in the format dd/mm/yy hh:mm, return as a datetime.

    """
    CENTURY = 2000
    i = date_string.find('/')
    j = date_string.find('/',i+1)
    k = date_string.find(':')
    if date_string[i+1:i+3] == date_string[j-2:j]:
        month = int(date_string[i-2:i])
        day = int(date_string[j-2:j])
        year = int(date_string[j+1:j+3])
        hour = int(date_string[k-2:k])
        minute = int(date_string[k+1:k+3])
    else:
        return None
   
    if year > 99 or month > 12 or day > 31 or hour > 23 or minute > 59:
        return None
    else: return datetime(year+CENTURY,month,day,hour,minute)

def isolateDate(date_candidates):
    """
    Parses a list of potential date strings into a list of datetime objects.
    If more than one valid date is found, prompts user to select.
    """
    dates = []
    for candidate in date_candidates:
        date = acertainDateValue(candidate)
        if date is not None:
            dates.append(date)

    if len(dates) > 1 and not all(date == dates[0] for date in dates):
        while True:
            print("Multiple date values found.")
            for index,date in enumerate(dates): print('['+str(index)+'] ',date)
            num = int(input("Line number of the correct date:"))
            if num >= 0 and num < len(dates): return dates[num]
    else: return dates[0] if len(dates) > 0 else None

def tesseractImage(filepath):
    """
    run tesseract ocr on image at filepath, return text as string
    """
    # Read image from disk
    im = cv2.imread(filepath, cv2.IMREAD_COLOR)

    # Run tesseract OCR on image
    # '-l eng'  for using the English language
    # '--oem 1' for using LSTM OCR Engine
    text = pytesseract.image_to_string(im, config='-l eng --oem 1 --psm 3')
    return text

def parseLine(line):
    def separatePrice(line):
        """
        Check each line for a price (at least 4 numeric characters at end)
        """
        letter_flag = 0
        #iterate backwards through the string for first alphabet character
        for i in range(-1, -len(line), -1):
            if line[i].isalpha():
                #detect first alphabet character
                if letter_flag == 0: letter_flag = i; continue

                #if second alphabet char is less than 4 
                #chars left of the first there isn't a price
                if letter_flag == -1 and -(i - letter_flag) < 4:
                    #consider line as heading (no price)
                    return (line,None)

                else:
                    #consider line as item (name,price pair)
                    split = i+2 if i+1 == letter_flag else i+1
                    return (line[:split], line[split:])
                    #    name = line[:i+2]; price = line[i+2:]
                    #else: name = line[:i+1]; price = line[i+1:]
        return (None,line)

    if len(line) < 4:
        print('DISCARDED \'',line,'\' (less than 4 characters)')
        return (None,None,None,None)
    #if the line has two "/" and one ":", it might be the transaction date
    if line.count('/') == 2 and line.count(':') == 1:
        return (None,None,None,acertainDateValue(line))
    name,price = separatePrice(line)
    if price is None: return (None,None,name,None)
    elif name is None:
        print('DISCARDED \'',line,'\' (no item)')
        return (None,None,None,None)
    else: return (name,price,None,None)
    

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('script requires at least one image file passed as argument')
        sys.exit(1)
    
    # Uncomment the line below to provide path to tesseract manually
    pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'

    #for each image path given as argument
    for i in range(1,len(sys.argv)):
        img_path = sys.argv[i]
        lines = tesseractImage(img_path).splitlines()

        category_head = ''
        items = []
        dates = []
        for line in lines:
            name,price,category,date = parseLine(line)
            if date is not None: dates.append(date); continue
            if category is not None: category_head = category; continue
            if name is not None and len(name) > 1:
                items.append((name,price,category_head)) \
                        if category_head.isupper() \
                        else items.append((name,price,None)); continue
            #print('DISCARDING LINE \'',line,'\' (could not be parsed)')

        items_prime = []
        for name,*tup in items:
            not_items = ('Regular Price','Card Savings')
            list_end = ('BALANCE','TOTAL')
            if any(fuzz.ratio(string,name) > 80 for string in not_items):
                continue
            print(name,*tup)
            items_prime.append((name,*tup))
            if any(fuzz.partial_ratio(strng,name) > 90 for strng in list_end):
                print('ENDING LIST AT \'',name,'\''); break

        while dates == []: #dates = [None]
            print('No date value found. If you have a date enter it here')
            date = input('in the form mm/dd/yy hh:mm (else leave blank) =>')
            if len(date) > 1:
                try:
                    dates = [datetime.strptime(date, '%m/%d/%y %H:%M')]; break
                except ValueError:
                    print("couldn't correctly parse input date"); continue
            else: dates = [None]; break

        if len(dates) > 1 and not all(date == dates[0] for date in dates):
            while True:
                print('Multiple date values found.')
                for index,date in enumerate(dates): 
                    print('['+str(index)+'] ',date)
                num = int(input("Line number of the correct date:"))
                if num >= 0 and num < len(dates): 
                    dates = [date]; break 
        

        #snippet adapted from "Github Gist - write tuples to csv"
        #https://gist.github.com/agoops/dd3ec3821438b695f7c462877a0fbeb4
        with open(img_path[:-4]+'.csv', 'w') as f:
            writer = csv.writer(f , lineterminator='\n')
            for tup in items_prime:
                writer.writerow((*tup,dates[0]))
        '''
        #generate statistics for output
        titlecount = 0
        itemcount = 0
        for name,price in items:
            if price == ' ':
                titlecount += 1
            else:
                itemcount += 1
        
        print(img_path+' Read Completed')
        print('  '+str(len(lines))+' lines of text read')
        print('  '+str(titlecount)+' headings and '
                +str(itemcount)+' items/price pairs')
        print('  '+'output written to '+img_path[:-4]+'.csv')
    print(str(len(sys.argv)-1)+' images processed')
    print('using tesseract with options \''+config+'\'')
        '''
