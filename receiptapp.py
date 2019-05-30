#basic class-based tkinter template from 
#https://stackoverflow.com/a/17470842 
import tkinter as tk
import receipt2json as receipt
import parserTJ as tj
from PIL import Image, ImageTk

COLOR_KEY = {#line tag:color
        'catg':'#ccffcc',#category 
        'coup':'#e5ccff',#coupon    (tuple)
        'date':'#ffffcc',#date value
        'errr':'#ffcccc',#error     (tuple)
        'foot':'#ccccff',#footer
        'fsum':'#ffe5cc',#balance (doesnt match sum of prices)
        'head':'#ccccff',#header
        'item':'#e5ffcc',#item w/ price (tuple)
        'none':'#e0e0e0',#discarded line
        'rate':'#ccffff',#rate pricing
        'tsum':'#cce5ff',#balance (matches sum of prices)
    }

STORE_KEY = {
        'safeway': receipt.parseSafeway,
        'traderjoes': tj.parseTJ,
        'costco': receipt.parseSafeway,
        'newleaf': receipt.parseSafeway
    }

def parseByStore(store,lines):
    return STORE_KEY[store](lines)

BIG_FONT = '-*-lucidatypewriter-medium-r-*-*-*-120-*-*-*-*-*-*'
SMALL_FONT = '-*-lucidatypewriter-medium-r-*-*-*-100-*-*-*-*-*-*'

class Entrypane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.parent = parent
        
        self.active_name = tk.StringVar()
        self.active_price = tk.StringVar()
        self.active_cat = tk.StringVar()

        self.item_sframe1 = tk.Frame(self)
        self.tag_list = [*COLOR_KEY.keys()]
        self.tag_str = tk.StringVar()
        self.tag_str.set(self.tag_list[0])
        self.tag_menu = tk.OptionMenu(self.item_sframe1, self.tag_str, 
                *self.tag_list)
        self.tag_menu.config(font=SMALL_FONT)

        self.name_entry = tk.Entry(self.item_sframe1, 
                textvariable=self.active_name,
                width = 40, font=BIG_FONT)
        self.item_sframe2 = tk.Frame(self)
        self.price_entry = tk.Entry(self.item_sframe2, 
                textvariable=self.active_price,
                width = 7, font=BIG_FONT)
        self.item_sframe3 = tk.Frame(self)
        self.cat_entry = tk.Entry(self.item_sframe3, 
                textvariable=self.active_cat,
                width = 12, font=BIG_FONT)

        self.update_bt = tk.Button(self.item_sframe3, text='Update Line',
                font=SMALL_FONT, command=self.change_line)

        self.sum_str = tk.StringVar()
        self.sum_label = tk.Label(self.item_sframe2, textvariable=self.sum_str,
                font=BIG_FONT)

        self.item_sframe1.pack(side='top', fill='x')
        self.name_entry.pack(side='right')
        self.tag_menu.pack(side='left')

        self.item_sframe2.pack(side='top', fill='x')
        self.price_entry.pack(side='right')
        self.sum_label.pack(side='left')

        self.item_sframe3.pack(side='top', fill='x')
        self.cat_entry.pack(side='right')
        self.update_bt.pack(side='left')

    def change_line(self):
        print(self.parent.data_list.curselection())
        try:
            #raises exception if nothing is selected
            index = self.parent.data_list.curselection()[0]
            tag, item = self.parent.parsed_lines[index]
        except:
            index = None
        #load the line into entry fields
        if (index != self.parent.active_item and index is not None):
            self.tag_str.set(tag)
            if type(item) is tuple:
                self.load_name(item)
                self.load_price(item)
                self.load_cat(item)
            else:
                self.load_name(item)
                self.active_price.set('')
                self.active_cat.set('')
            self.parent.active_item = index
        else:
        #update the line from entry fields
            index = self.parent.active_item
            tag = self.tag_str.get()
            if tag == 'item':
                self.update_item(index)
                #self.update_name(index)
                #self.update_price(index)
                #self.update_cat(index)
            if tag == 'catg':
                self.active_name.set('')
                self.active_price.set('')
                self.update_cat(index)

    def load_price(self, item):
        _, price, _ = item
        self.active_price.set(str(price))

    def load_name(self,item):
        if type(item) is tuple:
            name, _, _ = item
        else:
            name = item
        self.active_name.set(str(name))

    def load_cat(self,item):
        _, _, cat = item
        self.active_cat.set(cat)

    def update_item(self,index):
        '''
        update the name,price,cat in self.parsed_lines and update the line 
        at selection index using vals in entry fields
        '''
        #update the item's info from fields
        #_, item = self.parent.parsed_lines[index]
        name = self.active_name.get()
        price = int(self.active_price.get())
        cat = self.active_cat.get()
        #if type(item) is tuple:
        #    name, _, category = item
        #else:
        #    name = "None"
        self.parent.parsed_lines.update(
                    {index: ('item', (name, price, cat))})
            #self.data_list.delete(index)
        print(self.parent.parsed_lines[index])
        self.parent.update_line(index, *self.parent.parsed_lines[index])
        self.parent.check_receipt()
        #update the fields with item info

    def update_name(self,index):
        '''
        '''
        #index = self.parent.data_list.curselection()[0]
        tag, item = self.parent.parsed_lines[index]
        #update the item's info from fields
        if index == self.parent.active_item:
            name = self.active_name.get()
            if type(item) is tuple:
                _, price, cat = item
                self.parent.parsed_lines.update(
                        {index: (tag, (name, price, cat))})
                #self.data_list.delete(index)
                #self.parent.check_receipt()
            else:
                self.parent.parsed_lines.update(
                        {index: (tag, name)})
                #self.data_list.delete(index)
            self.parent.update_line(index, *self.parent.parsed_lines[index])
        #update the fields with item info
        else:
            #self.parent.active_item = index
            if type(item) is tuple:
                name, _, _ = item
            else:
                name = item
            self.active_name.set(name)

    def update_cat(self,index):
        '''
        '''
        #index = self.parent.data_list.curselection()[0]
        tag, item = self.parent.parsed_lines[index]
        #update the item's info from fields
        if index == self.parent.active_item:
            cat = self.active_cat.get()
            if type(item) is tuple:
                name, price, _ = item
                self.parent.parsed_lines.update(
                        {index: (tag, (name, price, cat))})
                #self.data_list.delete(index)
                #self.parent.check_receipt()
            elif tag == 'catg':
                self.parent.parsed_lines.update(
                        {index: (tag, cat)})
                #self.data_list.delete(index)
            self.parent.update_line(index, *self.parent.parsed_lines[index])

        #update the fields with item info
        else:
            #self.parent.active_item = index
            if type(item) is tuple:
                _, _, cat = item
            elif tag == 'catg':
                cat = item 
            self.active_cat.set(cat)

class Datapane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent,width=280)
        
        self.parent = parent

        self.file_frame = tk.Frame(self)
        self.item_frame = Entrypane(self)

        self.data_list = tk.Listbox(self, font=BIG_FONT)
        
        self.active_item = -1

        self.save_bt = tk.Button(self.file_frame, text='Save List', 
                state=tk.DISABLED,
                font=SMALL_FONT, command=self.save_list)
        
        self.pack_propagate(0)
        
        self.file_frame.pack(side='top', fill='x')
        self.save_bt.pack(side='right')

        self.data_list.pack(side='top', fill='both', expand=True)
        
        self.item_frame.pack(side='top', fill='x')
    

    def parse_file(self, path='./img'):
        img_path = self.parent.filepane.sel_file_str.get()
        self.data_list.delete(0,tk.END)

        lines = receipt.tesseractImage(path + '/' + img_path).splitlines()
        store = receipt.matchHeader(lines)

        self.parsed_lines = parseByStore(store,lines)


        #self.parsed_lines = receipt.parseSafeway(lines)

        self.update_pane()

    def update_line(self,idx,tag,line):
        if type(line) is tuple:
            item = ' ## '.join([str(i) for i in line])
        else: item = str(line)
        line_entry = ' '.join((str(idx).rjust(4),tag,item))

        while self.data_list.size() < idx:
            self.data_list.insert(tk.END, '')

        if self.data_list.get(idx) != '':
            #print('update ',self.data_list.get(idx))
            self.data_list.delete(idx)
        self.data_list.insert(idx, line_entry)
        self.data_list.itemconfig(idx, background=COLOR_KEY[tag])

    def update_pane(self):
        self.balance_idx = -1
        for idx, (tag, line) in self.parsed_lines.items():
            self.update_line(idx, tag, line)
            if tag == 'tsum' or tag == 'fsum':
                self.balance_idx = idx
        self.check_receipt()

    def check_receipt(self):
        if self.balance_idx == -1:
            return

        price_sum = 0
        for idx, (tag, line) in self.parsed_lines.items():
            if type(line) is tuple and tag == 'item':
                #print(idx, tag, line, sep = '\t')
                if len(line) == 3:
                    _, price, _ = line
                else:
                    _, price = line
                price_sum += price
        _, entry = self.parsed_lines[self.balance_idx]
        if len(entry) == 3:
            name, total, cat = entry
        else:
            name, total = entry
        if price_sum == total:
            self.update_line(self.balance_idx, 'tsum', entry)
            self.save_bt.config(state=tk.NORMAL)
        else:
            self.update_line(self.balance_idx, 'fsum', entry)
            self.save_bt.config(state=tk.DISABLED)
        self.item_frame.sum_str.set('CURRENT SUM: '+str(price_sum))

    def save_list(self):
        #receipt.saveList(r_id,...)
        pass


class Fileops(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.parent = parent
        self.refresh_bt = tk.Button(self, text='Refresh File List',
                font=SMALL_FONT)
        self.read_bt = tk.Button(self, text='Read Selected File',
                font=SMALL_FONT, command=self.read_file)
        #read_bt.bind('<Button-1>', parent.filepane.update_view())
        self.readall_bt = tk.Button(self, text='Read All', font=SMALL_FONT)
        self.history_ch = tk.Checkbutton(self, text='Ignore history.csv',
                font=SMALL_FONT) 
        self.user_list = receipt.readUsers()
        #print(*self.user_list,sep="\n")
        self.user_str = tk.StringVar()
        self.user_str.set(self.user_list[0])
        self.user_menu = tk.OptionMenu(self, self.user_str, *self.user_list)
        self.user_menu.config(font=SMALL_FONT)
        self.user_bt = tk.Button(self, text="tag with user:", font=SMALL_FONT)#,
        #        command=self.parent.filepane.tag_file)
        
        self.refresh_bt.pack(side='left')
        self.read_bt.pack(side='left')
        self.readall_bt.pack(side='left')
        self.history_ch.pack(side='left')
        self.user_menu.pack(side='right')
        self.user_bt.pack(side='right')
        #.pack(side='left')

    def read_file(self):
        self.parent.filepane.update_view()
        self.parent.datapane.parse_file()


class Filepane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.parent = parent
        self.pack_propagate(0)

        files_str = tk.StringVar(); files_str.set(self.read_files())
        self.sel_file_str = tk.StringVar(); 
        self.file_list = tk.Listbox(self, selectmode=tk.BROWSE, 
                listvariable=files_str, font=SMALL_FONT)
        self.file_list.activate(0)
        #self.sel_file_str.set(self.file_list.get(tk.ACTIVE))
        self.sel_file_idx = 0 
        
        self.file_view = tk.Label(self)
        self.file_label = tk.Label(self, textvariable=self.sel_file_str,
                font=BIG_FONT)
        #self.read_image(self.file_view,self.sel_file_str.get())
        self.file_list.pack(side='top', fill='x')
        self.file_label.pack(side='top')
        self.file_view.pack(side='top', fill='both', expand=True)

    def read_files(self, path='./img'):
        new_imgs, old_imgs = receipt.findImages(path)
        new_imgs = sorted([i.replace(' ','\\ ') for i in new_imgs])
        old_imgs = sorted([i.replace(' ','\\ ') for i in old_imgs])
        img_str = ' '.join(new_imgs + old_imgs)
        return img_str

    def read_image(self, img_widget, filename, path='./img'):
        if filename is not None:
            image = Image.open(path + '/' + filename)
            img_width = self.file_view.winfo_width()
            img_height = self.file_view.winfo_height()
            print(img_width,img_height)
            image.thumbnail((img_width,img_height))
            photo = ImageTk.PhotoImage(image)
            img_widget.config(image=photo)
            img_widget.image = photo

    def update_view(self):
        #print(self.file_list.get(tk.ACTIVE))
        self.file_list.itemconfig(self.sel_file_idx, 
                background=COLOR_KEY['none'])
        if len(self.file_list.curselection()) > 0:
            self.sel_file_idx = self.file_list.curselection()[0]
        else: self.sel_file_idx = 0
        self.sel_file_str.set(self.file_list.get(self.sel_file_idx))
        self.file_list.itemconfig(self.sel_file_idx, 
                background=COLOR_KEY['head'])
        self.read_image(self.file_view,self.sel_file_str.get())

    def tag_file(self):
        filename = self.sel_file_str.get()
        user_tag = self.parent.fileops.user_str.get()
        filename += '***' + user_tag
        #self.


class FilepaneApplication(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.filepane = Filepane(self)
        self.datapane = Datapane(self)
        self.fileops = Fileops(self)

        self.fileops.pack(side="top", fill="x")
        self.datapane.pack(side="right", fill="both", expand=True)
        self.filepane.pack(side="left", fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = FilepaneApplication(root)
    app.pack(side="top", fill="both", expand=True)
    root.update()

    app.fileops.read_file()

    root.mainloop()
