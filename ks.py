import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from time import sleep
import json
import datetime

BASE_URL = "https://www.kommersant.ru"

def parse_articles(url, seen_urls):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    articles = []
    article_elements = soup.find_all("article", class_="uho rubric_lenta__item js-article")
    
    for element in article_elements:
        title = element["data-article-title"]
        date = element.find("p", class_="uho__tag").get_text(strip=True)
        article_url = urljoin(BASE_URL, element["data-article-url"])
        
        if article_url not in seen_urls:
            seen_urls.add(article_url)
            articles.append({"title": title, "date": date, "url": article_url})
    
    return articles

def fetch_article_content(article_url):
    response = requests.get(article_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    intro_paragraphs = soup.find_all("p", class_="doc__text doc__intro")
    intro = " ".join(p.get_text(strip=True) for p in intro_paragraphs)
    
    content_paragraphs = soup.find_all("p", class_="doc__text")
    
    content = " ".join(p.get_text(strip=True) for p in content_paragraphs)
    
    full_content = intro + "\n\n" + content if intro else content
    return full_content

def main():
    begin_date = datetime.datetime.strptime("2025-01-24", "%Y-%m-%d")
    url_template = urljoin(BASE_URL, "/archive/rubric/2/day/{}/")
    
    all_articles = []
    seen_urls = set()
    
    while begin_date.date() <= datetime.datetime.today().date():
        current_url = url_template.format(begin_date.strftime("%Y-%m-%d"))
        print(f"Парсинг статей за дату: {begin_date.strftime('%Y-%m-%d')}")
        
        try:
            response = requests.get(current_url)
            if response.status_code != 200:
                print(f"Страница для {begin_date.strftime('%Y-%m-%d')} не найдена, переходим к следующему дню")
            else:
                articles = parse_articles(current_url, seen_urls)
                daily_articles = []
                
                for article in articles:
                    print(f"Парсим статью: {article['title']}")
                    
                    article["url"] = article["url"].replace("/day/", "/")
                    
                    article_content = fetch_article_content(article["url"])
                    article["content"] = article_content
                    daily_articles.append(article)
                    
                    print(f"Дата: {article['date']}\nСодержание: {article['content']}\n")
                    sleep(1)
                
                if daily_articles:
                    with open("articles.json", "a", encoding="utf-8") as file:
                        json.dump(daily_articles, file, ensure_ascii=False, indent=4)
                        file.write("\n")
                    print(f"Статьи за {begin_date.strftime('%Y-%m-%d')} записаны в файл")
        
        except Exception as e:
            print(f"Ошибка при парсинге {begin_date.strftime('%Y-%m-%d')}: {e}")
        
        finally:
            begin_date += datetime.timedelta(days=1)
    
    print("Парсинг завершен")

if __name__ == "__main__":
    main()
