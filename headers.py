import sys
import json
from os import listdir
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import receipt2json as receipt
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

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else None
    print(mode)
    header_dict = readHeaders()
    for key,lines in header_dict.items():
        print(key)
        for line in lines:
            print("-", line)

    img_list, history_list = receipt.findImages()
    img_list.extend(history_list)
    for file in img_list:
        lines = receipt.tesseractImage('img/'+file).splitlines()
        print(matchHeader(lines), file, sep='\t')

