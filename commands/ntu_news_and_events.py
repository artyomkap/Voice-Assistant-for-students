import requests
from bs4 import BeautifulSoup
import lxml
import datetime

from num2words import num2words


def get_news():
    link = 'https://www.ntu.ac.uk/studenthub/news?collection=ntu~sp-students-news&query=!nullsearch&start_rank=1&sort=date'

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36',
    }


    r = requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text,'lxml')
    news_div = soup.find('div', class_='news-search-featured')
    list_of_news = news_div.find_all('article', 'news-search-item featured')
    news_list = []
    index = 0
    for item in list_of_news:
        title_h2 = item.find('h2', class_='news-search-item-title').text
        published_date = item.find('div', class_='news-search-item-date').text
        day = int(published_date.split('/')[0])
        month = published_date.split('/')[1]
        month_name = datetime.datetime.strptime(month, '%m').strftime('%B')
        formatted_date = f"{num2words(day, ordinal=True).capitalize()} of {month_name}"
        paragraphs = item.find_all('p')
        article_text = ''.join(paragraph.text for paragraph in paragraphs)
        index += 1
        formatted_index = num2words(index, ordinal=True)
        news_list.append(f"NEWS: {formatted_index}, Published: {formatted_date}, Title is {title_h2} Article: {article_text}")
    return news_list


def get_events():
    link = 'https://www.ntu.ac.uk/about-us/events/current-students-events'

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36',
    }

    r = requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    listings = soup.find('ul', class_='listing off-no-spacing flex-row featured-news-articles')
    list_of_listings = listings.find_all('li',
                                         class_='result clearfix small-12 medium-12 large-4 columns featured-news-article-pinned') + \
                       listings.find_all('li',
                                         class_='result clearfix small-12 medium-6 large-4 columns featured-news-article-featured')
    list_of_events = []
    for item in list_of_listings:
        title = item.find('h2', class_='result-title skim-bottom skim-top').text.strip()
        date = item.find('span', class_='event-start-date').text
        day = int(date.split(' ')[0])
        month_name = date.split(' ')[1]
        year = int(date.split(' ')[2])
        formatted_date = f"{num2words(day, ordinal=True).capitalize()} of {month_name} in {num2words(year)}"
        paragraphs = item.find_all('p')
        article_text = ''.join(paragraph.text for paragraph in paragraphs)
        list_of_events.append(f"Event: {title}, on {formatted_date}")
    return list_of_events

