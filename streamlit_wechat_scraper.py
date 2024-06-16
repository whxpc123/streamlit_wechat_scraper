import time
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

# Streamlit 页面配置
st.title('WeChat Article Scraper')
keyword = st.text_input('Enter search keyword', 'AI绘画')
num_pages = st.number_input('Enter number of pages to scrape', min_value=1, max_value=20, value=5)
start_button = st.button('Start Scraping')

def download_image(img_url, image_count):
    try:
        # 检查是否是base64编码的图片
        if img_url.startswith('data:image'):
            # 提取base64数据
            base64_data = img_url.split(',')[1]
            img_data = base64.b64decode(base64_data)
            # 保存图片
            with open(f"AIGC/{image_count}.jpg", "wb") as file:
                file.write(img_data)
        else:
            # 下载普通图片
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                img_data = response.content
                # 验证图片数据（使用常见的图片格式进行验证）
                if not img_data.startswith(b'\xff\xd8') and not img_data.endswith(b'\xff\xd9') and \
                   not img_data.startswith(b'\x89PNG') and not img_data.endswith(b'IEND\xaeB`\x82'):
                    raise DownloadException("Invalid image data")
                # 保存图片
                with open(f"AIGC/{image_count}.jpg", "wb") as file:
                    file.write(img_data)
            else:
                raise DownloadException(f"Failed to download image {image_count}: HTTP {response.status_code}")
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to download image {image_count}: {str(e)}\n")
        raise DownloadException(f"Failed to download image {image_count}: {str(e)}")

if start_button:
    st.write(f'Starting to scrape articles for: {keyword}')

    # 构造搜索 URL
    search_url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}&ie=utf8"

    data = []
    try:
        for page in range(1, num_pages + 1):
            url = f"{search_url}&page={page}"
            response = requests.get(url)
            if response.status_code != 200:
                st.error(f"Failed to retrieve search results: HTTP {response.status_code}")
                raise Exception(f"Failed to retrieve search results: HTTP {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', class_='txt-box')

            for index, article in enumerate(articles):
                try:
                    st.write(f"Processing article {index + 1} on page {page}")
                    title_element = article.find('h3')
                    title = title_element.text
                    link = title_element.find('a')['href']
                    summary = article.find('p', class_='txt-info').text

                    # 有些文章可能没有来源信息，需要进行检查
                    source_element = article.find('div', class_='s-p')
                    source = source_element.text if source_element else 'N/A'

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
