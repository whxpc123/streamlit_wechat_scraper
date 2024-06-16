import time
import pandas as pd
import streamlit as st
from requests_html import HTMLSession
from io import BytesIO

# Streamlit 页面配置
st.title('WeChat Article Scraper')
keyword = st.text_input('Enter search keyword', 'AI绘画')
num_pages = st.number_input('Enter number of pages to scrape', min_value=1, max_value=20, value=5)
start_button = st.button('Start Scraping')

def fetch_articles(query, num_pages):
    base_url = "https://weixin.sogou.com/weixin"
    params = {
        'type': 2,
        'query': query,
        'page': 1
    }
    
    session = HTMLSession()
    data = []
    
    for page in range(1, num_pages + 1):
        params['page'] = page
        response = session.get(base_url, params=params)
        response.html.render()
        
        # 保存页面内容到文件，以便调试
        with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(response.html.html)
        
        articles = response.html.find('div.txt-box')
        
        if not articles:
            st.write(f"No articles found on page {page}. Please check debug_page_{page}.html for details.")
            continue
        
        for index, article in enumerate(articles):
            try:
                title_element = article.find('h3 a', first=True)
                title = title_element.text.strip()
                link = title_element.attrs['href']
                summary = article.find('p.txt-info', first=True).text.strip()
                source_element = article.find('div.s-p a', first=True)
                source = source_element.text.strip() if source_element else 'N/A'
                
                data.append({
                    'Title': title,
                    'Summary': summary,
                    'Link': link,
                    'Source': source
                })
                
                st.write(f"Processed article {index + 1} on page {page}")
            except Exception as e:
                st.write(f"Error extracting article {index + 1} on page {page}: {e}")
                
        time.sleep(2)  # 防止请求过快被封IP

    return data

if start_button:
    st.write(f"Starting to scrape articles for keyword: {keyword} on {num_pages} pages...")
    articles_data = fetch_articles(keyword, num_pages)
    
    if not articles_data:
        st.write("No articles found.")
    else:
        # 保存数据到Excel文件
        current_time = time.strftime("%Y%m%d%H%M%S")
        file_name = f"AI_微信_{current_time}.xlsx"
        df = pd.DataFrame(articles_data)

        # 将 DataFrame 保存到 BytesIO 对象中
        towrite = BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)

        # 提供文件下载链接
        st.download_button(label='📥 Download Excel File',
                           data=towrite,
                           file_name=file_name,
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
