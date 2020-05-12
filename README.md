# Receipt Scanner

An application that allows the user to scan receipts and display their spending data on a dashboard.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites
1. Please install Python 3.5+
2. Assure that you have Tesseract 4.0 installed on your device: `https://github.com/tesseract-ocr/tesseract`
3. Install or have access to Jupyter `https://jupyter.org/install`

### Installing
1. Start by cloning our project with git clone `https://github.com/rubui/receiptapp.git`
2. Then, install the following packages:
  * fuzzywuzzy through `pip install fuzzywuzzy`
  * pytesseract through `pip install pytesseract` , for more information refet to https://pypi.org/project/pytesseract/

### Using Receipt Scanner
**Currently our Parsers only support Costso, Trader Joe's, Safeway, Grocery Outlet, and New Leaf Market.**
# Uploading your receipts and name
1. Take a photo of your receipt, the clearer the image the better!
2. Copy photos over to the /img folder 
3. Add new users by editing people.xlxs file found in the /dat folder
4. Run receiptapp.py to extract and parse the receipt data, this will open a user interface which can then be used to edit any information the parser might not have correctly scanned in



# How to edit incorrectly extracted test with the tkinter GUI
After running receiptapp.py the GUI below should appear. Using this GUI the user should be able to make any needed adjustments to any incorrect information extracted and parsed. Here are some of the following features.

1. **Viewing a Receipt** On the top left of the interface, are all the receipt examined by receiptapp.py that was put into the /img folder. By selecting the receipt and hitting the "Read selected file" button, users can examine a side by side of the receipt image and the data that was parsed and categorized.

2. **Tagging a User** On the top right, users are given the option to tag the owner of the receipt by changing the user from the dropdown menu and selecting "tag with user"

3. **Adjusting the Parser to the Correct Store** To the left of the area where the user can adjust the date and time of purchase, in the case the wrong grocery store was identified, users my select the correct grocery store and hit "reparse" from the drop down menu to have the correct parser run on the receipt.

4. **Adjusting any Incorrect Categories or Text** On the bottom right of the interface, adjustments to any inccorectly parsed or extracted text can be made manually by selecting the incorrect line, hitting "update line" and making any necessary adjustments to the category of the line, the text, or for items, the price, as shown below. 

5. **Save List** By hitting save list, all adjustments made should be saved to grocerylist.json found in the /dat folder

# Viewing Spending Data and Trends
Once all necessary adjustments have been made, open jupyter notebook and run the GroceryReceiptDashBoard.ipynb. This should generate graphs titled:
1. "grocery_monthly_per_person.html" to view each useres monthly spending habits
2. "grocery_top_ten_per_person.html" to view the top ten items frequently purchased by each user
3  "total_group_barchart.html" to view aggregated user data

## Authors

* **Calvin Houser** - [Xeroxcat](https://github.com/xeroxcat)
* **Rebecca Duong** - [reduong](https://github.com/reduong)
* **Rebecca Bui** - [rubui](https://github.com/rubui)


