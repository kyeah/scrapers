import asyncio
import certifi
import json
import requests
import robobrowser
from getpass import getpass

cert = certifi.where()
login_url = "https://login.ezproxy.lib.utexas.edu/login?qurl=https%3a%2f%2futexas.kanopystreaming.com%2fcatalog"
catalog_url = "https://utexas-kanopystreaming-com.ezproxy.lib.utexas.edu/catalog/?space=videos&page={}&rows=20&sort=most-popular"

def login():
    browser = robobrowser.RoboBrowser()
    browser.open(login_url, verify=cert)

    form = browser.get_form()
    form['user'] = input("User: ")
    form['pass'] = getpass("Pass: ")
    browser.submit_form(form, verify=cert)
    return browser

@asyncio.coroutine
def scrape_titles(browser, page):
    browser.open(catalog_url.format(page), verify=cert)
    titles = browser.select('.title')
    json_titles = [{'title': el.text, 'href': el.get('href')} for el in titles]
    return json_titles

def main():

    browser = login()

    futures = []
    for i in range(0, 765):
        future = asyncio.ensure_future(scrape_titles(browser, i))
        futures.append(future)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))
    loop.close()

    flattened = [item for future in futures for item in future.result()]
    with open('titles.txt', 'w') as outfile:
        json.dump(flattened, outfile)

if __name__ == '__main__':
    main()
