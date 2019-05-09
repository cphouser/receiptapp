#basic class-based tkinter template from 
#https://stackoverflow.com/a/17470842 
import tkinter as tk
import receipt2json as receipt
from PIL import Image, ImageTk

class Datapane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.parent = parent

        self.data_list = tk.Listbox(self, selectmode=tk.SINGLE)
        self.data_list.pack(fill='both', expand=True)

    def parse_file(self, path='./img'):
        img_path = self.parent.filepane.file_str.get()
        self.data_list.delete(0,tk.END)

        lines = receipt.tesseractImage(path + '/' + img_path).splitlines()
        #parsed_lines = receipt.parseByCategory(lines)

        for line in lines:
            self.data_list.insert(tk.END, line)

        #items,dates,heads,foots,remainders = receipt.ParseByCategory(lines)


        

class Fileops(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.refresh_bt = tk.Button(self, text='Refresh File List')
        self.read_bt = tk.Button(self, text='Read Selected File',
                command=self.read_file)
        self.parent = parent
        #read_bt.bind('<Button-1>', parent.filepane.update_view())

        self.readall_bt = tk.Button(self, text='Read All')
        self.history_ch = tk.Checkbutton(self, text='Ignore history.csv')

        self.refresh_bt.pack(side='left')
        self.read_bt.pack(side='left')
        self.readall_bt.pack(side='left')
        self.history_ch.pack(side='left')
        #.pack(side='left')

    def read_file(self):
        self.parent.filepane.update_view()
        self.parent.datapane.parse_file()

class Filepane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.pack_propagate(0)

        files_str = tk.StringVar(); files_str.set(self.read_files())
        self.file_str = tk.StringVar(); 
        self.file_list = tk.Listbox(self, selectmode=tk.BROWSE, 
                listvariable=files_str)
        self.file_list.activate(0)
        self.file_str.set(self.file_list.get(tk.ACTIVE))

        self.file_view = tk.Label(self)
        self.file_label = tk.Label(self, textvariable=self.file_str)
        self.read_image(self.file_view,self.file_str.get())
        
        self.file_list.pack(side='top', fill='x')
        self.file_label.pack(side='top')
        self.file_view.pack(side='top')

    def read_files(self, path='./img'):
        new_imgs, old_imgs = receipt.findImages(path)
        new_imgs = [i.replace(' ','\\ ') for i in new_imgs]
        old_imgs = [i.replace(' ','\\ ') for i in old_imgs]
        img_str = ' '.join(new_imgs + old_imgs)
        return img_str

    def read_image(self, img_widget, filename, path='./img'):
        if filename is not None:
            image = Image.open(path + '/' + filename)
            image.thumbnail((400,800))
            photo = ImageTk.PhotoImage(image)
            img_widget.config(image=photo)
            img_widget.image = photo

    def update_view(self):
        #print(self.file_list.get(tk.ACTIVE))
        self.file_str.set(self.file_list.get(tk.ACTIVE))
        self.read_image(self.file_view,self.file_str.get())

class FilepaneApplication(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.filepane = Filepane(self)
        self.fileops = Fileops(self)
        self.datapane = Datapane(self)

        self.fileops.pack(side="top", fill="x")
        self.datapane.pack(side="right", fill="both", expand=True)
        self.filepane.pack(side="left", fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    FilepaneApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
