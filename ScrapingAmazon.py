import requests
from bs4 import BeautifulSoup
from fake_headers import Headers

import json
import csv
import re
import time
import random
proxies = []


class ScrapingAmazon():
    def __init__(self, keywords):
        self.session = requests.Session()
        self.url = f"https://www.amazon.co.uk/s?k={keywords.replace(' ', '+')}"
        self.products_asin = []

    def get_Asins(self):
        current_page = self.url
        while True:
            try:
                response = self.session.get(
                    current_page, headers=Headers(headers=True).generate())
                soup = BeautifulSoup(response.text, "lxml")
                items_box = soup.find("div", class_='s-search-results')
                #items = items_box.findAll("div", {"data-asin" : re.compile(r".*")})
                #items = items_box.findAll("div", {"data-asin" : True})
                items = items_box.find_all('div', recursive=False)
                for item in items:
                    if len(item['data-asin']):
                        self.products_asin.append(item['data-asin'])
            except Exception as ex:
                pass
            next_page = soup.find('a', class_='s-pagination-next')
            if(next_page):
                current_page = self.url + next_page['href']
                print(current_page)
            else:
                break

    def set_AsinFile(self, fileName="Asins.txt"):
        with open(fileName, 'w') as file:
            for asin in self.products_asin:
                file.write(asin + '\n')

    def get_AsinsFile(self, fileName="Asins.txt"):
        with open(fileName, 'r') as file:
            self.products_asin.extend([p.rstrip() for p in file])

    def productInfo(self, asin):
        url = f'https://www.amazon.co.uk/dp/{asin}'
        while True:
            proxy = {'http': random.choice(proxies)}
            response = requests.get(
                url, proxies=proxy, headers=Headers(headers=True).generate())
            if(response.status_code == 200):
                break  # Break Loop, this is successful Requests
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            product_info = {
                'Asin': asin,
                'Title': soup.find('span', id="productTitle").string.strip(),
                'Date': soup.find('table', id="productDetails_detailBullets_sections1").find_all('tr')[-1].td.text.strip()
                # 'reviews': self.productReview(asin) ## B0B6G5BGDR
            }
            #########################################################
            try:
                price = soup.find('div', id="corePrice_feature_div").div.span.find(
                    'span', class_="a-offscreen")
                price = price.text.replace('£', '').replace(',', '')
                product_info['Price'] = price
            except:
                product_info['Price'] = None
            #########################################################
            try:
                product_info['Sold by'] = soup.find(
                    'a', id="sellerProfileTriggerId").string
            except:
                product_info['Sold by'] = "Amazon"
            #########################################################
            try:
                product_info['Review Count'] = soup.find(
                    'div', {'data-hook': "total-review-count"}).span.text.strip().replace(' global rating', '').replace('s', '')
                product_info['Rating'] = soup.find(
                    'span', {'data-hook': "rating-out-of-text"}).string.replace(' out of 5', '')
            except:
                product_info['Review Count'] = "0"
                product_info['Rating'] = "0"
            print(product_info)
            return product_info
        except:
            return  # Weak Product

    def productReview(self, asin):
        url = f'https://www.amazon.co.uk/product-reviews/{asin}'
        try:
            while True:
                proxy = {'http': random.choice(proxies)}
                response = requests.get(url, proxies=proxy,
                                        headers=Headers(headers=True).generate())
                if(response.status_code == 200):
                    break
            soup = BeautifulSoup(response.text, 'lxml')
            reviews = soup.find_all('div', {'data-hook': "review"})
            product_reviews = []
            for review in reviews:
                product_review = {
                    'Rating': review.find('a', class_="a-link-normal").string.replace(" out of 5 stars", ""),
                    'Review Title': review.find('a', {'data-hook': "review-title"}).span.string
                }
                product_reviews.append(product_review)
            print(product_reviews)
            return product_reviews
        except Exception as ex:
            return []

    def to_Json(self, fileName='Products.json'):
        products = []
        # Change Format
        for asin in set(self.products_asin):
            products.append({
                asin: {
                    'Details': self.productInfo(asin),
                    'Review': self.productReview(asin)
                }
            })
        with open(fileName, 'w') as file:
            json.dump(products, file, indent=4)

    def to_CSV(self, fileName='Products.csv'):
        with open(fileName, 'w', newline='') as file:
            ## CSV_file = csv.writer(file, delimiter=',')
            writer = csv.DictWriter(file,
                                    fieldnames=['Asin', 'Title', 'Price', 'Sold by', 'Review Count', 'Rating', 'Date'])
            writer.writeheader()
            for asin in set(self.products_asin):
                p = self.productInfo(asin)
                ## CSV_file.writerow([asin, p['Title'], p['Price'], p['Sold by'], p['Review Count'], p['Rating']])
                if(p):
                    writer.writerow(p)

    def __del__(self):
        self.session.close()


def get_proxies(fileName="proxies.txt"):
    with open(fileName, 'r') as file:
        proxies.extend([p.rstrip() for p in file])


############################################################
startTime = time.time()

get_proxies()
amazon = ScrapingAmazon('laptop')
# amazon.get_Asins()
# amazon.set_AsinFile()

amazon.get_AsinsFile()
amazon.to_CSV()

print(f'Execution Time: {(time.time() - startTime):.3f} sec')
