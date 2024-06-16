import time
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from io import BytesIO

# Streamlit 页面配置
st.title('WeChat Article Scraper')
keyword = st.text_input('Enter search keyword', 'AI绘画')
num_pages = st.number_input('Enter number of pages to scrape', min_value=1, max_value=20, value=5)
start_button = st.button('Start Scraping')

if start_button:
    st.write(f'Starting to scrape articles for: {keyword}')

    # 构造搜索 URL
    search_url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}&ie=utf8"

    data = []
    try:
        for page in range(1, num_pages + 1):
            url = f"{search_url}&page={page}"
            st.write(f"Scraping page {page}: {url}")
            response = requests.get(url)
            if response.status_code != 200:
                st.error(f"Failed to retrieve search results: HTTP {response.status_code}")
                raise Exception(f"Failed to retrieve search results: HTTP {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', class_='txt-box')

            if not articles:
                st.write(f"No articles found on page {page}")
                continue

            for index, article in enumerate(articles):
                try:
                    st.write(f"Processing article {index + 1} on page {page}")
                    title_element = article.find('h3')
                    title = title_element.text.strip()
                    link = title_element.find('a')['href']
                    summary = article.find('p', class_='txt-info').text.strip()

                    # 有些文章可能没有来源信息，需要进行检查
                    source_element = article.find('div', class_='s-p')
                    source = source_element.text.strip() if source_element else 'N/A'

                    data.append({
                        'Title': title,
                        'Summary': summary,
                        'Link': link,
                        'Source': source
                    })
                except Exception as e:
                    st.write(f"Error extracting article {index + 1} on page {page}: {e}")

    except Exception as e:
        st.error(f"Error occurred: {str(e)}")

    if data:
        # 保存数据到Excel文件
        current_time = time.strftime("%Y%m%d%H%M%S")
        file_name = f"AI_微信_{current_time}.xlsx"
        df = pd.DataFrame(data)

        # 将 DataFrame 保存到 BytesIO 对象中
        towrite = BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)

        # 提供文件下载链接
        st.download_button(label='📥 Download Excel File',
                           data=towrite,
                           file_name=file_name,
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        st.write('Scraping completed! You can download the results as an Excel file.')
    else:
        st.write("No data found.")
