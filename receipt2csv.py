#adapted from example:
#https://www.learnopencv.com/deep-learning-based-text-recognition-ocr-using-tesseract-and-opencv/

import cv2
import sys
#requires Tesseract 4.0 installed
import pytesseract
import csv
import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def isolateDate(date_candidates):
    def acertainValue(date_string):
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
        else: return datetime.datetime(year+2000,month,day,hour,minute)

    dates = []
    for candidate in date_candidates:
        date = acertainValue(candidate)
        if date is not None:
            dates.append(date)

    if len(dates) > 1 and not all(date == dates[0] for date in dates):
        while True:
            print("Multiple date values found.")
            for index,date in enumerate(dates): print('['+str(index)+'] ',date)
            num = int(input("Line number of the correct date:"))
            if num >= 0 and num < len(dates): return dates[num]
    else: return dates[0] if len(dates) > 0 else None



 
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('script requires at least one image file passed as argument')
        sys.exit(1)
    
    #for each image path given as argument
    for i in range(1,len(sys.argv)):
        img_path = sys.argv[i]
        
        # Uncomment the line below to provide path to tesseract manually
        pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'

        # Define config parameters.
        # '-l eng'  for using the English language
        # '--oem 1' for using LSTM OCR Engine
        config = ('-l eng --oem 1 --psm 3')

        # Read image from disk
        im = cv2.imread(img_path, cv2.IMREAD_COLOR)

        # Run tesseract OCR on image
        text = pytesseract.image_to_string(im, config=config)
        lines = text.splitlines()

        # Check each line for a price (at least 4 numeric characters at end)
        category_head = ''
        items = []
        date_candidates = []
        for line in lines:
            letter_flag = 0
            price = ''
            name = ''
            if len(line) < 6:
                continue
            #if the line has two "/" and one ":", it might be the transaction date
            if line.count('/') == 2 and line.count(':') == 1:
                date_candidates.append(line)
                continue
            #iterate backwards through the string for first alphabet character
            for i in range(-1, -len(line), -1):
                if line[i].isalpha():
                    #detect first alphabet character
                    if letter_flag == 0:
                        letter_flag = i
                        continue
                    #if second alphabet char is less than 4 
                    #chars left of the first there isn't a price
                    if letter_flag == -1 and -(i - letter_flag) < 4:
                        #consider line as heading (no price)
                        category_head = line
                        break
                        #name = line; price = ' '
                    else:
                        #consider line as item (name,price pair)
                        if i+1 == letter_flag:
                            name = line[:i+2]; price = line[i+2:]
                        else: name = line[:i+1]; price = line[i+1:]
                    break
            #fix accidental read of period as comma
            price = price.replace(',','.')
            regular = fuzz.ratio('Regular Price',name)
            cardsav = fuzz.ratio('Card Savings',name)
            if (regular > 80 or cardsav > 80):
                #print('discarding ',line)
                #print("RP? :", regular, " CS? :", cardsav)
                continue
            if category_head.isupper() and len(name) > 1: 
                items.append((name,price,category_head))

        date = isolateDate(date_candidates)
        #print(date)
        for index,(name,*tup) in enumerate(items):
            print(name,*tup,date)
            #print(fuzz.partial_ratio('BALANCE',name))
            if fuzz.partial_ratio('BALANCE',name) > 90:
                items = items[:index+1]
                break

        #snippet adapted from "Github Gist - write tuples to csv"
        #https://gist.github.com/agoops/dd3ec3821438b695f7c462877a0fbeb4
        with open(img_path[:-4]+'.csv', 'w') as f:
            writer = csv.writer(f , lineterminator='\n')
            for tup in items:
                writer.writerow((*tup,date))
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
