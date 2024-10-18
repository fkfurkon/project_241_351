import sys
sys.path.insert(0,'chromedriver.exe')
import re
import os
from flask import Flask, render_template, request ,jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
import time

# setup chrome options
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--headless') # ensure GUI is off
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--disable-dev-shm-usage')

# set path to chromedriver as per your configuration
chromedriver_autoinstaller.install()


app = Flask(__name__)
port = "7777"

@app.route('/')
def index():
    return "<h1>Test API</h1>"

@app.route('/api',methods=['GET'])
def api():
    if request.method == 'GET':
        message = request.args.get('msg')

        url1 = "https://www.ais.th/consumers/store/phones?category=plp-tab-"

        # if message in ['Apple', 'OPPO', 'vivo', 'Xiaomi', 'Samsung'] :
        if len(message.split('/')) == 2 :
            # set the target URL
            message = message.split('/')
            print(message[0])
            if message[0] == 'tablets':
                url1 = url1.replace("phones", "tablets")
            else :
                url1 = 'https://www.ais.th/consumers/store/phones?category=plp-tab-'

            print(url1)
            url = url1+message[1].lower()
            # set up the webdriver
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            driver.implicitly_wait(10)  # Wait for the page to load
            html = driver.page_source
            mysoup = BeautifulSoup(html, "html.parser")
            all_elements = mysoup.find_all("div",{"class":"sc-cLFqLo gtyzXw"}) # MuiCardContent-root card-content css-1qw96cp
            scrap = []
            for element in all_elements:
                title_product = element.find("a", class_="product-name")
                href = 'https://www.ais.th'+title_product.get('href')
                price = element.find("p", class_="MuiTypography-root MuiTypography-body1 product-discount css-fpfjc4")
                img = element.find('img', {'class': 'MuiCardMedia-root MuiCardMedia-media MuiCardMedia-img css-rhsghg'})
                scrap.append({
                    'title': title_product.text,
                    'price': 'ราคาเริ่มต้น'+price.text if price else "N/A",  # Handle cases where title_date might be None
                    'link' : href,
                    'img' : 'https://www.ais.th'+img['src']
                })
            return jsonify(scrap)
        
        elif message:
            url = message
            # set up the webdriver
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            driver.implicitly_wait(10)  # Wait for the page to load
            html = driver.page_source
            mysoup = BeautifulSoup(html, "html.parser")
            all_elements = mysoup.find_all("div",{"class":"MuiGrid-root MuiGrid-container Uj0v1C1XEXwF3QB9BaBF css-1d3bbye"})
            scrap = []
            for element in all_elements:
                # title_product = element.find("a", class_="product-name")
                scrap.append({
                    'promotion': element.text
                })
            return jsonify(scrap)
                    
        else :
            # set the target URL
            url = "https://www.ais.th/consumers/store/phones"
            # set up the webdriver
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            driver.implicitly_wait(10)  # Wait for the page to load
            html = driver.page_source
            mysoup = BeautifulSoup(html, "html.parser")
            all_elements = mysoup.find_all("div",{"class":"MuiCardContent-root card-content css-1qw96cp"})
            scrap = []
            for element in all_elements:
                title_product = element.find("a", class_="product-name")
                href = 'https://www.ais.th'+title_product.get('href')
                price = element.find("p", class_="MuiTypography-root MuiTypography-body1 product-discount css-fpfjc4")
                scrap.append({
                    'title': title_product.text,
                    'price': 'ราคาเริ่มต้น'+price.text if price else "N/A",  # Handle cases where title_date might be None
                    'link' : href
                })
            return jsonify(scrap)


# Start the Flask server 
# Run the Flask server normally
if __name__ == '__main__':
    app.run(port=port)  # You can specify host='0.0.0.0' if you want to allow access from outside