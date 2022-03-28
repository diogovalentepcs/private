import requests
from bs4 import BeautifulSoup
import pandas as pd
import cs

URL = "http://zipatlas.com/us/tx/austin/zip-78701.htm"
page = requests.get(URL)
pagetext = page.text

soup = BeautifulSoup(pagetext, 'html.parser')
soup.find_all('tr')
