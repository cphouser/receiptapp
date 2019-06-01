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

def readHeaders(path='dat/stores.json'):
    """
    """
    if 'stores.json' in listdir(path='dat/'):
        #print('store header info loaded')
        with open(path) as f:
            header_dict = json.load(f)
        return header_dict
    else:
        #print('store header info not found')
        return None

def matchHeader(lines):
    real_lines = [line for line in lines[:20] if len(line) > 4]
    header_dict = readHeaders()
    
    store_matches = {}

    for store, head_lines in header_dict.items():
        store_match_v = 0
        for head_line in head_lines:
            fuzz_val = 0
            for line in real_lines:
                fp_ratio = fuzz.partial_ratio(head_line, line)
                #print(fp_ratio,line)
                fuzz_val = max(fp_ratio, fuzz_val)
            store_match_v += fuzz_val
            #print(fuzz_val)
        store_matches.update({store: store_match_v})
        #print(store_match, store)
    return max(store_matches.items(), key=operator.itemgetter(1))[0]

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

def readUsers(path='./dat'):
    user_list = []
    with open(path + '/people.csv', 'r', newline='') as f:
        reader = csv.reader(f, lineterminator='\n')
        for user_entry in reader:
            user_list.append(user_entry[0])
    return user_list

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

def acertainDateValue(date_string):
    """
    given a line, if a date exists in the format dd/mm/yy hh:mm, 
    return it as a datetime object.

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
        print(date_string)
        return None
    if year > 99 or month > 12 or day > 31 or hour > 23 or minute > 59:
        print(year,month,day,hour,minute)
        return None
    else: return datetime(year+CENTURY,month,day,hour,minute)

def lastDigit(string):
    """
    given a string, find the last (closest to end) numeric character
    and return the index. return -1 if no characters are numeric
    """
    for idx in range(-1, -len(string), -1):
        if string[idx].isdigit(): return len(string) + idx; 
        elif len(string) + idx == 0: return -1
    return -1

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
    
def parseLine1(line):
    #don't consider any line with less than 4 characters
    if len(line) < 4:
        return ('none', line)

    #if the line has two "/" and one ":", it might be the transaction date
    if line.count('/') == 2 and line.count(':') == 1:
        date = acertainDateValue(line)
        if date is not None:
            return ('date', date)
        else:
            return ('none', line)

    #try extracting a price from the right side
    name,price = separatePrice1(line)

    #if no price it might be a category
    if price is None:
        #exclude lines that include QTY
        fuz = fuzz.partial_ratio('QTY',name)
        if fuz > 60:
            return ('none', line)

        #safeway categories are uppercase
        if (all((i.isupper() if i.isalpha() else True) for i in line) 
                and fuzz.partial_ratio('SAFEWAY',name) < 75):
            return ('catg', line)

        #otherwise discard
        return ('none', line)

    #ignore if theres no item name
    elif name is None:
        return ('none', line)

    else: return tryPrice1(name, price)
    
def tryPrice1(name, price): 
    """
    given a separated name and price, check whether the price can be
    read as an int.
    """
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

def parseSafeway(lines):
    def excludeMatch(name):
        """
        check for keywords in item field
        """
        exclude_items = ['Regular Price','Card Savings']
        coupon_names = ['Store Coupon']
        list_end = 'BALANCE'
        if any(fuzz.ratio(string,name) > 80 for string in exclude_items):
            return 'none'
        if any(fuzz.ratio(string,name) > 80 for string in coupon_names):
            return 'coup'
        if fuzz.partial_ratio(list_end,name) > 90:
            return 'fsum'
        return 'item'

    #initiate flags for iterating over lines
    category_head = None
    ended = False

    #return lines as a dict, keyed by line number
    items = {}
    for line in lines:
        index = len(items)
        
        #discard all lines with less than two characters
        if len(line) <= 1:
            continue
        
        tag, item = parseLine1(line)
        #print(index, tag, item, sep='\t')
        if tag == 'date':
            items.update({index: ('date', item)})
            continue

        if ended is True:
            items.update({index: ('foot', line)})
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

def saveList(r_id, date, items):
    """
    NEEDS UPDATING - not currently used
    saves the receipt in the grocerylist file as a dict entry.
    """
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
    
def priceCheck(items):
    """
    DEPRECATED 
    attempts to correct read errors for price values
    """
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

if __name__ == '__main__':
    # Uncomment the line below to provide path to tesseract manually
    # pytesseract.pytesseract.tesseract_cmd = 'bin/tesseract'

    mode = sys.argv[1] if len(sys.argv) > 1 else None
    print(mode)
    #if len(sys.argv) > 1 and sys.argv[1] == '--help':
    #    print('Script searches the ./img directory for files')
    #    print('and for file history.txt , Script loads all files not listed')
    #    print('in history.txt and reads each as a grocery receipt image. ')
    #    print('The items and total are written to grocerylist.json as a')
    #    print('json array in the form: name, price, category, timestamp')
    #    sys.exit(1)
    #
    img_list, history_list = findImages()
    
    if mode == 'head':
        for img_path in img_list:
            print("*****",img_path,"*****")
            lines = tesseractImage('img/'+img_path).splitlines()
            for i in range(min(len(lines),15)):
                print(i, ":\t", lines[i])


    print('  Images to Scan:', *img_list, sep='\n')
    print('  Images in History File:', *history_list, sep='\n')
    receipt_dict = {}
    #for each image found in /img folder
    for img_path in img_list:
        print("*****",img_path,"*****")

        lines = tesseractImage('img/'+img_path).splitlines()
        
        line_dict = parseSafeway(lines)

        for idx,(tag,item) in line_dict.items():
            if type(item) is tuple:
                name, price, cat = item
                print(idx, tag, price, name, cat, sep=':\t')
            else:
                print(idx, tag, item, sep=':\t')

       # 
       # balance, items = priceCheck(items)
       # receipt_date = None

       # if len(dates) > 1 and not all(date == dates[0] for date in dates):
       #     while True:
       #         print('Multiple date values found.')
       #         for index,date in enumerate(dates): 
       #             print('['+str(index)+'] ',date)
       #         num = int(input("Line number of the correct date:"))
       #         if num >= 0 and num < len(dates): 
       #             dates = [date]; break 
       # elif len(dates) >= 1 and all(date == dates[0] for date in dates):
       #     receipt_date = dates[0]
       # else: #dates = []
       #     while receipt_date is None:
       #         print('No date value found. If you have a date enter it here')
       #         date = input('in form mm/dd/yy hh:mm (else leave blank) =>')
       #         if len(date) > 1:
       #             try:
       #                 receipt_date = datetime.strptime(date,
       #                         '%m/%d/%y %H:%M') 
       #             except ValueError:
       #                 print("couldn't parse input date") 
       #         else: receipt_date = datetime.min
       # 
       # receipt_id = ''.join(filter(lambda x: x.isdigit(), str(receipt_date)))\
       #         +str(balance)
       # receipt_dict.update({receipt_id:(receipt_date,balance,items,img_path)})
       # print(receipt_dict[receipt_id])

       # with open('img/history.csv', 'a') as f:
       #     writer = csv.writer(f, lineterminator='\n')
       #     writer.writerow([img_path])
            
            
    
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
