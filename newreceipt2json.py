from datetime import datetime
from fuzzywuzzy import fuzz

# THE START OF THE SECTION: FUNCTIONS BORROWED FROM RECEIPT2JSON WRITTEN BY CALVIN
# -----------------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------------
# THE END OF THE SECTION: FUNCTIONS BORROWED FROM RECEIPT2JSON WRITTEN BY CALVIN

'''
Rebecca D:
Added a couple of lines to the acertainDateValue function written by Calvin
So it can extract the seconds in the date value for grocery outlet receipts 
and will work on newleaf recipts as well
NOTE: The changes I made will be commented
'''
def acertainDateValue(date_string):
    """
    given a line, if a date exists in the format dd/mm/yy hh:mm, 
    return it as a datetime object.

    """
    # Delete all the non-numeric chars in the given date_string
    for c in date_string:
        if c.isalpha():
            date_string = date_string.replace(c, '')
    date_string =  date_string.replace(': ', '')

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
        second = -1

        # if the second colon exists, try to get the seconds 
        if l > 0:
            try:
                second = int(date_string[l+1:l+3])
                if second > 59:
                    second = 0
            except:
                second = 0
    else:
        print(date_string)
        return None
    if year > 99 or month > 12 or day > 31 or hour > 23 or minute > 59 or second == 0:
        # If seconds does not exists, then only print year, month, day, hour, and minute
        if second == 0:
            print(year,month,day,hour,minute)
        else:
            print(year,month,day,hour,minute,second)
        return None
    elif second > 0: 
        return datetime(year+CENTURY,month,day,hour,minute,second)
    else: return datetime(year+CENTURY,month,day,hour,minute)

'''
Rebecca D:
Extract the date from the given string of trader joes and costco receipts
'''
def acertainDateValue2(date_string):
    
    #print(date_string)

    # If the string contains two dashes then the date exists in the format of mm/dd/yyyy
    i = date_string.find('/')
    j = date_string.find('/', i+1)

    # If the string contains two ampersands then the date exists in the format of mm-dd-yyyy
    l = date_string.find('-')
    m = date_string.find('-', i+1)


    # Find the location where the colon exists
    # This is where the time will be
    o = date_string.find(':')
    p = date_string.find(':', o+1)
    #print(l)

    # If there exists a colon but the two chars before and after the colon are not
    # numeric, then there's no hour and minutes 
    # Record the date only
    if o > 0:
        if not(date_string[o+1:o+3].isdigit() or date_string[o-2:o].isdigit()):
            date_string = date_string[0:o-3]
            #print(date_string)

    # If there exists a second colon but the two chars before and after the colon are not
    # numeric, then there's no minutes and seconds
    if p > 0:
        if(date_string[p+1:p+3].isdigit() == False):
            date_string = date_string[0:p]
            #print(date_string)

    # Find how many colons are left
    k = date_string.count(':')

    # Use the function, strptime(), from the datetime library to get the date
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

'''
Rebecca D:
Parse each given line from the trader joes and costco receipts
Return appropriate tags for each item
'''
def parseLine2(row):
    time_change = 0

    # ignore all rows with less than 4 chars
    if(len(row) < 4):
        return('none', row)
    
    # if row contain 2 ampersands or 2 dashes, then this line might
    # include a date value 
    if(row.count('-') == 2 or row.count('/') == 2):
        if 'PM' in row:
            time_change = 1
        
        # take away the non-numeric chars preceding the date
        if not(row[0].isnumeric()):
            for c in row:
                if(c.isnumeric()):
                    break
                row = row.strip(c)
            print(row)
        
        # only keep the part of the row that contains the date, month, year, 
        # hours, minutes, or seconds
        if row.count(':') == 0:
            row = row[0:10]
        elif row.count(':') == 1:
            row = row[0:16]
        elif row.count(':') == 2:
            row = row[0:18]
        
        date = acertainDateValue2(row)
        
        # change the time into 24-hr time format
        if time_change:
           date = date.replace(hour = date.hour + 12)
        #print(date)
        return ('date', date)

    # THIS SECTION APPLIES ONLY TO TRADER JOES
    # -------------------------------------------------------------------------
    if(fuzz.partial_ratio('TRADER JOES', row) >= 91):
        #print(line)
        return ('head', 'Trader Joes')
    
    if('OPEN' and 'DAILY' in row):
        return('head', row)

    if('FLOZ' in row or '@' in row):
        return('none', row)
    #---------------------------------------------------------------------------
    
    # THIS SECTION APPLIES ONLY TO COSTCO
    #---------------------------------------------------------------------------
    #print(fuzz.partial_ratio('Costco', 'Cosrco'))
    if fuzz.partial_ratio('Costco', row) > 80 or 'WHOLESALE' in row:
        return ('head', row)

    if row.count('(') == 1 and row.count(')') == 1:
        return('head', row)
    # --------------------------------------------------------------------------

    if any(c.islower() for c in row) and '.' not in row:
        #print(row)
        return ('head', row)

    # extract the price on the right side
    name, price = separatePrice1(row)

    # If there is a name and a price, then this may be an item
    # Else, a non-item
    if all(val is not None for val in [name, price]):
        return tryPrice1(name, price)
    else:
        return ('none', (name, price))

'''
Rebecca D:
Added and deleted a couple of lines to the parseLine1 function written by Calvin
So it can parse the line for the grocery outlet receipts
'''
def parseLine3(line):
    #don't consider any line with less than 4 characters
    if len(line) < 4:
        return ('none', line)

    #if the line has two "/" and two ":", it might be the transaction date
    if line.count('/') == 2 and line.count(':') == 2:
        date = acertainDateValue(line)
        if date is not None:
            return ('date', date)
        else:
            return ('none', line)

    if (any(i.islower() for i in line) and '.' not in line):
            return ('catg', line)

    #try extracting a price from the right side
    name,price = separatePrice1(line)

    #if no price, discard it
    if price is None:
        return ('none', line)

    #ignore if theres no item name or contain an @ in the name
    elif name is None or '@' in line:
        return ('none', line)

    else: return tryPrice1(name, price)

'''
Rebecca D:
Parse each given line from the new leaf receipts
Return appropriate tags for each item
'''
def parseLine4(row):
    time_change = 0

    if len(row) < 4:
        return ('none', row)

    if(row.count('-') == 2 or row.count('/') == 2):
        date = acertainDateValue(row)

        if 'PM' or 'pm' in row and date is not None:
            date = date.replace(hour = date.hour + 12)

        return ('date', date) if date is not None else ('none', row)

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
            #print(i)
            tag = 'none'
            item = line

        if tag == 'errr':
            items.update({index: (tag, (*item, None))})
            continue
            
        if not end:
            if tag == 'item':
                if 'SUBTOTAL' in item[0]:
                    tag = 'none'
                    item = line
                elif fuzz.ratio('TOTAL', item[0]) == 100:
                    tag = 'fsum'
                elif 'TAX' in item[0]:
                	items.update({index: (tag, (*item, 'TAX'))})
                	continue
                else:
                    items.update({index: (tag, (*item, None))})
                    continue
            if tag == 'none':
                #print(fuzz.partial_ratio('Store #', 'Stare #193 - (831) 425-d149'))
                if(fuzz.partial_ratio('Store #', item) > 85):
                    tag = 'head'
                else:
                    items.update({index: (tag, item)})
                    continue
            if tag == 'head':
                items.update({index: (tag, item)})
                continue
            if tag == 'fsum':
                items.update({index: (tag, (*item, 'SUM'))})
                end = True
                continue
        else:
            if tag == 'date':
                items.update({index: (tag, item)})
                continue
            else:
                if type(item) is tuple:
                    if item[1] is None:
                        item = item[0]
                    elif item[0] is None:
                        item = item[1]
                    else:
                        item = item[0] + str(item[1])
                items.update({index: ('foot', item)})
    
    return items

def parseCostco(lines):
    end = False
    end_head = False
    found_tax = 0
    subtotal = 0
    items = {} 
    
    for line in lines:

        index = len(items)

        if len(line) <= 1 or line.isspace():
            continue
        
        try:
            tag, item = parseLine2(line)
        except:
            #print("Invalid Data Passed in")
            #print(i)
            tag = 'none'
            item = line

        if tag == 'date':
            items.update({index: (tag, item)})
            continue
       
        if(item[0] is not None):
            if 'TOTAL' in item[0]:
                if(fuzz.ratio('SUBTOTAL', item[0]) == 100):
                    tag = 'none'
                    subtotal = int(item[1])
                elif 'TAX' in item[0]:
                    tag = 'foot'
                elif 'ITEM' not in item[0]:
                    items.update({index: ('fsum', (*item, 'SUM'))})
                    end = True
                    continue

        if (found_tax and subtotal > 0) and 'TOTAL' in item:
                total = found_tax + subtotal
                items.update({index: ('fsum', ('TOTAL', total, 'SUM'))})
                end = True
                continue
        
        if tag == 'errr':
            items.update({index: (tag, (*item, None))})
            continue
        
        #print(fuzz.partial_ratio('SE Member', 'SR Member 111847974436'))
        if fuzz.partial_ratio('SE Member', item) > 80:
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
                    found_tax = int(item[1])
                    items.update({index: (tag, (*item, 'TAX'))})
                    continue
                else: 
                	items.update({index: (tag, (*item, None))})
                	continue
            if tag == 'head':
                if end_head:
                    tag = 'none'
            items.update({index: (tag, item)})
    
    return items

'''
Rebecca D:
Added and deleted a couple of lines to the parseSafeway function written by Calvin
So it can parse grocery outlet receipts instead of safeway receipts
Those with comments are the ones that have changes made by Rebecca D.
'''
def parseGO(lines):
    # Rebecca D: deleted some lines here as it doesn't applies to GO receipts
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
        
        tag, item = parseLine3(line)
        #print(index, tag, item, sep='\t')

        # Reach the end of the header of the receipt if true
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
                items.update({index: (tag, (*item, 'SUM'))})
                end = True
                continue
        elif found_tax and 'TOTAL' in item:
                tag = 'errr'
                end = True

        if tag == 'errr':
            items.update({index: (tag, (*item, None))})
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
                    items.update({index: (tag, (*item, 'TAX'))})
                    continue
                else:
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