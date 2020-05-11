# Receipt Scanner

An application that allows the user to scan receipts and display their spending data on a dashboard.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites
1. Please install Python 3.5+
2. Assure that you have Tesseract 4.0 installed on your device: `https://github.com/tesseract-ocr/tesseract`

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



## Authors

* **Calvin Houser** - [Xeroxcat](https://github.com/xeroxcat)
* **Rebecca Duong** - [reduong](https://github.com/reduong)
* **Rebecca Bui** - [rubui](https://github.com/rubui)


