import asyncio
import certifi
import json
import requests
import robobrowser
import shutil
import sys
from getpass import getpass

cert = certifi.where()
base_url = "https://utexas-kanopystreaming-com.ezproxy.lib.utexas.edu"
login_url = "https://login.ezproxy.lib.utexas.edu/login?qurl=https%3a%2f%2futexas.kanopystreaming.com%2fcatalog"
catalog_url = "https://utexas-kanopystreaming-com.ezproxy.lib.utexas.edu/catalog/?space=videos&page={}&rows=20&sort=most-popular"

output_filename = "titles.json"

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

@asyncio.coroutine
def scrape_info(browser, title, href):
    browser.open(href, verify=cert)
    info = browser.select('#tab-desc')[0]
    description = '\n\n'.join([p.text for p in info.find_all('p')])
    clips = browser.select('#playlist-clips .clip-container.clip.asset')
    features = info.find_all('li')
    if not clips:
        [runtime, year] = features[0].find('span').text.split(', ')
        title['runtime'] = runtime
        title['year'] = year
    else:
        clip_names = [clip.find(class_='clip-title').text for clip in clips]
        runtimes = [clip.find(class_='clip-running-time').text for clip in clips]
        yops = [clip.get('data-yop') for clip in clips]
        title['clips'] = [{'title': clip_names[i],
                           'runtime': runtimes[i],
                           'year': yops[i]}
                          for i in range(0, len(clips))]
        
    filmmakers = [a.text for a in features[1].find_all('a')]
    languages = [a.text for a in features[-1].find_all('a')]
    title['description'] = description
    title['filmmakers'] = filmmakers
    title['languages'] = languages

    if len(features) > 3:
        ft = [a.text for a in features[2].find_all('a')]
        title['features'] = ft
    
    return title

def update_titles(browser):
    futures = []
    for i in range(0, 765):
        future = asyncio.ensure_future(scrape_titles(browser, i))
        futures.append(future)    

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))
    loop.close()

    flattened = [item for future in futures for item in future.result()]
    return flattened

def update_info(browser):
    with open(output_filename, 'r') as outfile:
        items = json.load(outfile)
        futures = [asyncio.ensure_future(scrape_info(browser, item, base_url + item['href']))
                   for item in items]
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(futures))
        loop.close()

        extracted = [future.result() for future in futures]
        return extracted

def main():
    
    if len(sys.argv) < 2:
        print("Usage: python app.py (titles | info)")
        sys.exit(0)

    browser = login()
    
    titles = []
    if sys.argv[1] == "titles":
        titles = update_titles(browser)
    else:
        titles = update_info(browser)

    shutil.copyfile(output_filename, '.{}'.format(output_filename))
    with open(output_filename, 'w') as outfile:
        json.dump(titles, outfile)

if __name__ == '__main__':
    main()
