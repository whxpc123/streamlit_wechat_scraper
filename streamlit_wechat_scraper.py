import time
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from io import BytesIO

# Streamlit 页面配置
st.title('WeChat Article Scraper')
keyword = st.text_input('Enter search keyword', 'AI绘画')
num_pages = st.number_input('Enter number of pages to scrape', min_value=1, max_value=20, value=5)
start_button = st.button('Start Scraping')

if start_button:
    # 初始化WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，不打开浏览器窗口
    options.add_argument('--no-sandbox')  # 在无沙箱模式下运行
    options.add_argument('--disable-dev-shm-usage')  # 禁用共享内存
    options.add_argument('--disable-gpu')  # 禁用GPU加速

    # 使用 webdriver-manager 安装 ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 目标网址
    url = "https://weixin.sogou.com/"

    # 打开目标网址
    driver.get(url)
    time.sleep(2)

    # 输入关键字
    search_box = driver.find_element(By.ID, 'query')
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.RETURN)

    # 等待搜索结果加载
    time.sleep(5)

    # 初始化存储数据的列表
    data = []

    # 爬取指定页数的数据
    for page in range(1, num_pages + 1):
        try:
            articles = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.txt-box'))
            )

            for index, article in enumerate(articles):
                try:
                    st.write(f"Processing article {index + 1} on page {page}")
                    title_element = article.find_element(By.CSS_SELECTOR, 'h3')
                    title = title_element.text
                    link = title_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    summary = article.find_element(By.CSS_SELECTOR, 'p.txt-info').text

                    # 有些文章可能没有来源信息，需要进行检查
                    source_element = article.find_elements(By.CSS_SELECTOR, 'div.s-p a')
                    source = source_element[0].text if source_element else 'N/A'

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

        # 翻页
        if page < num_pages:
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, '下一页'))
                )
                next_button.click()
                time.sleep(5)
            except Exception as e:
                st.write(f"Error clicking next page: {e}")
                break

    # 关闭浏览器
    driver.quit()

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
