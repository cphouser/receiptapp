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
        return -1
    def firstDigit(string):
        for idx in range(-1, -len(string), -1):
            #print('>>',idx,string[idx])
            if string[idx].isdigit(): continue
            else: return len(string) + idx + 1
        else: return 0

    price_string = price_string.replace(',','.')
    i = price_string.rfind('.')
    if i == len(price_string) - 1 or not price_string[i+1].isdigit():
        price_string = price_string[:i]
        i = price_string.rfind('.')
        
    j = price_string[:i].rfind(' ') if i != -1 \
            else price_string.rfind(' ')
    k = lastDigit(price_string)
    if k == -1: return None
    if j == -1: j = firstDigit(price_string[:k])
    if i == -1:
        if price_string[j:k+1].isdigit(): return int(price_string[j:k+1])
        else: 
            i = firstDigit(price_string[:k])
            #print(price_string,'**',i,'**',k)
            return int(price_string[i:k+1])
    dollars = ''
    cents = ''
    for digit in (price_string[j+1:i]):
        if digit.isdigit(): dollars += digit
        
    for digit in (price_string[i+1:i+3]):
        if digit.isdigit(): cents += digit
    return int(dollars)*100 + int(cents)

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
        pytesseract.pytesseract.tesseract_cmd = ''#windows dir
    elif sys.platform.startswith('linux'):
        pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'

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
                if letter_flag > -3 and -(i - letter_flag) < 4:
                    if all((i.isupper() if i.isalpha() else True) for i in line):
                        return (line,None) 
                    else: break
                else:
                    split = i+2 if i+1 == letter_flag else i+1
                    if len(line[split:]) > 2:
                        return (line[:split], line[split:])
                    else: break
        return (None,line)

    if len(line) < 4:
        #print(' \'',line,'\' (less than 4 characters)')
        return (None,None,None,None)
    #if the line has two "/" and one ":", it might be the transaction date
    if line.count('/') == 2 and line.count(':') == 1:
        return (None,None,None,acertainDateValue(line))
    name,price = separatePrice(line)
    if price is None: return (None,None,name,None)
    elif name is None:
        #print('DISCARDED \'',line,'\' (no item)')
        return (price,None,None,None)
    else: return (name,price,None,None)
    
def priceCheck(items):
    def checkRatio(price,total_diff):
        return fuzz.ratio(str(price + total_diff),str(price))
    
    #needs more work
    _, balance, _ = items.pop()
    price_list = [item[1] for item in items]
    price_sum = sum(price_list)
    print("balance is: ", balance, " sum(price_list) is: ", price_sum)
    if price_sum == balance: 
        print("prices correct!") 
        return balance, items
    elif price_sum > balance:
        for index, price in enumerate(price_list):
            all_others = price_sum - price
            if all_others == balance:
                print(price, "should be removed from sum")
                items.pop(index)
                price_list.pop(index)
                break
            possible_price = balance - all_others
            #print("without ",price , ", sum(price_list) is: ", all_others,
            #        " (should it be ", possible_price, "?)")
            if str(possible_price) in str(price):
                print(price, " should be ", possible_price)
                print("at ",index,": ",items[index][0])#,items[index][2])
                items[index] = (items[index][0],possible_price,items[index][2])
                break;
        #if good corrections exits, then
        return balance, items
    else:
        total_diff = balance - price_sum
        ratios = [checkRatio(price,total_diff) for price in price_list]
        for index,(name,price,_) in enumerate(items):
            print('['+str(index)+'] '+name,price,
                    '('+str(price + total_diff)+' ?',
                    'similarity:'+str(ratios[index])+')', sep='\t')
        while True:
            wrong_num = int(input('select which price to correct:'))
            if wrong_num in range(len(items)):
                items[wrong_num] = (items[wrong_num][0],
                        items[wrong_num][1]+total_diff,items[wrong_num][2])
                break
            else:
                print(wrong_num,type(wrong_num))
                print([range(len(items))])
        return balance, items

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

def parseByCategory(lines):
    def excludeMatch(name):
        exclude_items = ['Regular Price','Card Savings']
        coupon_names = ['Store Coupon']
        list_end = 'BALANCE'
        if any(fuzz.ratio(string,name) > 80 for string in exclude_items):
            return 'none', name
        if any(fuzz.ratio(string,name) > 80 for string in coupon_names):
            return 'coup', name
        if fuzz.partial_ratio(list_end,name) > 90:
            return 'fsum', name
        return None
    def tryPrice(price): 
        try:
            int_price = acertainPriceValue(price)
            return int_price
        except ValueError:
            print('Could not parse ', price, ' as int')
            return None
    def appendPriced(items,index,tag,name,price,category):
        int_price = tryPrice(price)
        if int_price is None:
            items.update({index: ('errr', (name, price, category))})
        else:
            items.update({index: (tag, (name, int_price, category))})

    category_head = None
    items = {}
    ended = False
    for index, line in enumerate(lines):
        name,price,category,date = parseLine(line)
        if date is not None: 
            items.update({index: ('date', date)})
            continue
        if ended is True:
            items.update({index: ('foot', line)})
            continue
        if category is not None: category_head = category; continue
        if category_head is None: 
            items.update({index: ('head', line)})
            continue
        if name is not None and price is not None and len(name) > 1:
            not_item = excludeMatch(name)
            if not_item is not None:
                if not_item[0] == 'fsum':
                    appendPriced(items, index, *not_item, price, 'SUM')
                    ended = True
                else:
                    appendPriced(items, index, *not_item, price, category_head)
            elif 'TAX' in name:
                appendPriced(items, index, 'item', name, price, 'TAX')
            else:
                appendPriced(items, index, 'item', name, price, category_head) 
        elif name is not None:
            items.update({index: ('none', line)})
    return items

def saveList(r_id, date, items):
    receipt_dict_past = {}
    if 'grocerylist.json' in listdir(path='dat/'):
        print('existing receipt list found at grocerylist.json')
        with open('dat/grocerylist.json') as f:
            receipt_dict_past = json.load(f)
        for r_id in receipt_dict:
            if r_id in receipt_dict_past:
                if receipt_dict[r_id][2] == receipt_dict_past[r_id][2]:
                    print(r_id, ' already in file - items match (continuing)')
                    continue
                else:
                    print(r_id, ' already in file - item differences found')
                    while True:
                        in_action = input(
                            '\'o\':keep original \'n\':keep new \'v\':view') 
                        if in_action == 'o': receipt_dict.pop(r_id); break
                        elif in_action == 'n': break
                        elif in_action == 'v':
                            print('   VVV - SAVED VERSION - VVV')
                            print(receipt_dict_past[r_id][2])
                            print('    VVV - NEW VERSION - VVV')
                            print(receipt_dict[r_id][2])
    else:
        print('creating new list of recipt data at grocerylist.json')

    receipt_dict_past.update(receipt_dict)

    with open('dat/grocerylist.json', 'w') as f:
        json.dump(receipt_dict_past, f, indent=2, sort_keys=True, default=str)
    

if __name__ == '__main__':
    # Uncomment the line below to provide path to tesseract manually
    # pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print('Script searches the ./img directory for files')
        print('and for file history.txt , Script loads all files not listed')
        print('in history.txt and reads each as a grocery receipt image. ')
        print('The items and total are written to grocerylist.json as a')
        print('json array in the form: name, price, category, timestamp')
        sys.exit(1)
    
    img_list, history_list = findImages()
    
    print('  Images to Scan:', *img_list, sep='\n')
    print('  Images in History File:', *history_list, sep='\n')
    receipt_dict = {}
    #for each image found in /img folder
    for img_path in img_list:
        lines = tesseractImage('img/'+img_path).splitlines()

        idxs, items = parseByCategory(lines)

        balance, items = priceCheck(items)
        receipt_date = None

        if len(dates) > 1 and not all(date == dates[0] for date in dates):
            while True:
                print('Multiple date values found.')
                for index,date in enumerate(dates): 
                    print('['+str(index)+'] ',date)
                num = int(input("Line number of the correct date:"))
                if num >= 0 and num < len(dates): 
                    dates = [date]; break 
        elif len(dates) >= 1 and all(date == dates[0] for date in dates):
            receipt_date = dates[0]
        else: #dates = []
            while receipt_date is None:
                print('No date value found. If you have a date enter it here')
                date = input('in form mm/dd/yy hh:mm (else leave blank) =>')
                if len(date) > 1:
                    try:
                        receipt_date = datetime.strptime(date,
                                '%m/%d/%y %H:%M') 
                    except ValueError:
                        print("couldn't parse input date") 
                else: receipt_date = datetime.min
        
        receipt_id = ''.join(filter(lambda x: x.isdigit(), str(receipt_date)))\
                +str(balance)
        receipt_dict.update({receipt_id:(receipt_date,balance,items,img_path)})
        print(receipt_dict[receipt_id])

        with open('img/history.csv', 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow([img_path])
            
            
    
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
