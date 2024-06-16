import time
import base64
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

class DownloadException(Exception):
    pass

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
    # 初始化存储数据的列表
    data = []

    # 爬取指定页数的数据
    for page in range(1, num_pages + 1):
        try:
            # 生成请求 URL
            url = f"https://weixin.sogou.com/weixin?query={keyword}&type=2&page={page}"
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('div.txt-box')

            for index, article in enumerate(articles):
                try:
                    st.write(f"Processing article {index + 1} on page {page}")
                    title_element = article.select_one('h3 a')
                    title = title_element.text
                    link = title_element['href']
                    summary = article.select_one('p.txt-info').text

                    source_element = article.select_one('div.s-p')
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
            st.write(f"Error finding articles on page {page}: {e}")
            break

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
