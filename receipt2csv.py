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

def acertainPriceValue(price_string):
    def lastDigit(string):
        for idx in range(-1, -len(string), -1):
            if string[idx].isdigit(): return len(string) + idx; 
            elif len(string) + idx == 0: return -1
    def firstDigit(string):
        for idx in range(-1, -len(string), -1):
            if string[idx].isdigit(): continue
            else: return 

    price_string = price_string.replace(',','.')
    i = price_string.rfind('.')
    j = price_string[:i].rfind(' ') if i != -1 \
            else price_string.rfind(' ')
    k = lastDigit(price_string)
    if j == -1: j = 0
    if k == -1: return None
    if i == -1:
        if price_string[j:k+1].isdigit(): return int(price_string[j:k+1])
        else: i = firstDigit(price_string[:k]); return int(price_string[i:k+1]) 
    return int(price_string[j+1:i])*100 + int(price_string[i+1:i+3])

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
        for i in range(-1, -len(line), -1):
            if line[i].isalpha():
                #detect first alphabet character
                if letter_flag == 0: letter_flag = i; continue

                #if second alphabet char is less than 4 
                #chars left of the first there isn't a price
                if letter_flag == -1 and -(i - letter_flag) < 4:
                    if all((i.isupper() if i.isalpha() else True) for i in line):
                        return (line,None) 
                    else: break
                else:
                    split = i+2 if i+1 == letter_flag else i+1
                    return (line[:split], line[split:])
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
    
def priceCheck(items):
    _, balance, _ = items.pop()
    price_list = [item[1] for item in items]
    price_sum = sum(price_list)
    print("balance is: ", balance, " sum(price_list) is: ", price_sum)
    if price_sum == balance: 
        print("prices correct!") 
        return
    elif price_sum > balance:
        for price in price_list:
            all_others = price_sum - price
            if all_others == balance:
                print(price, "should be removed from sum")
            possible_price = balance - all_others
            print("without ",price , ", sum(price_list) is: ", all_others,
                    " (should it be ", possible_price, "?)")
            if str(possible_price) in str(price):
                print(price, " should be ", possible_price)
                break;
        #if good corrections exits, then
        return
    #else:

    for price in price_list:
        all_others = price_sum - price
        #print("all others ", all_others)
        possible_price = balance - all_others
        print("comparing ", price, " to ", possible_price)
        #if fuzz.ratio(str(possible_price),str(price)) > 80:
        #    print("correcting ", price, " to ", possible_price)
        #    price = possible_price
        #    break


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

        category_head = None
        items = []
        dates = []
        for line in lines:
            name,price,category,date = parseLine(line)
            if date is not None: dates.append(date); continue
            if category is not None: category_head = category; continue
            if name is not None and len(name) > 1:
                items.append((name,price,category_head)); continue
            #print('DISCARDING LINE \'',line,'\' (could not be parsed)')

        items_prime = []
        coupon_list = []
        for name,price,category in items:
            not_items = ['Regular Price','Card Savings']
            coupon_names = ['Store Coupon']
            list_end = ['BALANCE','TOTAL']
            if any(fuzz.ratio(string,name) > 80 for string in not_items):
                continue
            #print('comparing ', name,' to ',coupon_names[0],' fuzz ratio: ',
            #        fuzz.ratio(coupon_names[0],name))
            if any(fuzz.ratio(string,name) > 80 for string in coupon_names):
                coupon_list.append((name,price,category))
                continue
            if category is None: continue
            try:
                int_price = acertainPriceValue(price)
                print(name,'\t',int_price,'\t',category)
                items_prime.append((name,int_price,category))
            except ValueError:
                print('Could not parse ',price,' as int')
            if any(fuzz.partial_ratio(strng,name) > 90 for strng in list_end):
                print('ENDING LIST AT \'',name,'\''); break

        priceCheck(items_prime)

        if dates == []: #dates = [None]
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
