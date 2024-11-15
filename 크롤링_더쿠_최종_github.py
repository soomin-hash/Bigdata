import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import json
import re

# 댓글을 리스트로 저장하는 함수
def get_comments_list(driver):
    comments_list = []
    actions = ActionChains(driver)

    while True:
        try:
            # '더 보기' 버튼 클릭
            show_more_button = driver.find_element(By.CSS_SELECTOR, 'div.show_more.comment_header')
            actions.move_to_element(show_more_button).click().perform()
            time.sleep(random.uniform(0.3, 0.7))  # 무작위 대기
        except:
            break  # 더 이상 '더 보기' 버튼이 없으면 종료

    # 모든 댓글 수집
    comment_items = driver.find_elements(By.CSS_SELECTOR, 'li.fdb_itm.clear')
    for comment in comment_items:
        try:
            comment_text = comment.find_element(By.CSS_SELECTOR, 'div.xe_content').text
            comments_list.append(comment_text)
        except:
            continue

    return comments_list

# WebDriver 설정
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
data = []

# 현재 날짜와 -7일까지 설정
today = datetime.now()
end_date = today - timedelta(days=7)
page = 1

while True:
    # 더쿠 페이지 방문
    driver.get(f"https://theqoo.net/hot?page={page}")
    print(f"페이지 {page} 크롤링 중...")

    # 게시물 목록을 가져옴
    post_elements = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.bd_lst tbody.hide_notice tr'))
    )

    for post_element in post_elements:
        try:
            # 공지글 건너뛰기
            if 'notice' in post_element.get_attribute('class'):
                continue

            # 게시물 제목과 URL 가져오기
            title_element = post_element.find_elements(By.CSS_SELECTOR, '.title a')
            if not title_element:
                continue

            title = title_element[0].text
            post_url = title_element[0].get_attribute("href")

            # 게시물 날짜 처리
            post_date_text = post_element.find_element(By.CSS_SELECTOR, '.time').text

            # 현재 날짜 형식(시간 표시)과 날짜 형식 구분
            if ":" in post_date_text:  # 오늘 날짜인 경우
                post_date = today
            elif len(post_date_text) == 8:  # 연도가 포함된 경우
                post_date = datetime.strptime(post_date_text, '%y.%m.%d')
            else:  # 월.일 형식인 경우
                post_date = datetime.strptime(post_date_text, '%m.%d').replace(year=today.year)

            # 기간 벗어나면 크롤링 종료
            if post_date < end_date:
                driver.quit()
                print("크롤링이 완료되었습니다.")
                break

            # 카테고리와 조회수 가져오기
            category = post_element.find_element(By.CSS_SELECTOR, '.cate').text if post_element.find_elements(By.CSS_SELECTOR, '.cate') else "N/A"
            views_text = post_element.find_element(By.CSS_SELECTOR, '.m_no').text.replace(",", "")
            views = int(views_text) if views_text.isdigit() else 0
            comment_count = post_element.find_elements(By.CSS_SELECTOR, '.far.fa-comment-dots')
            comments_count = comment_count[0].text if comment_count else "0"

            # 새로운 탭에서 게시물 페이지 열기
            driver.execute_script("window.open(arguments[0]);", post_url)
            driver.switch_to.window(driver.window_handles[-1])

            # 콘텐츠 및 댓글 가져오기
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.rhymix_content.xe_content')))
            content = driver.find_element(By.CSS_SELECTOR, 'div.rhymix_content.xe_content').text

            comments = get_comments_list(driver)

            # 데이터 리스트에 추가
            data.append({
                "ID": "theqoo-" + re.search(r'(?<=hot/)\d+', post_url).group(),
                "community": "theqoo",
                "category": category,
                "title": title,
                "post_date": post_date.strftime('%Y-%m-%d %H:%M'),
                "view": views,
                "comments_count": len(comments),
                "link": post_url,
                "content": content,
                "comments": comments
            })

            # 탭 닫고 메인 페이지로 이동
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(random.uniform(0.8, 1.5))  # 무작위 대기

        except Exception as e:
            print(f"오류 발생: {e}")
            if "429" in str(e):
                print("서버 요청 제한 발생(429), 잠시 대기 중...")
                time.sleep(2)

    # 날짜 범위를 초과하면 종료
    if post_date < end_date:
        break

    page += 1  # 다음 페이지로 이동

# JSON 파일에 한 번에 저장
with open("date_range_data.json", "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

# WebDriver 종료
print("모든 데이터가 date_range_data.json 파일에 저장되었습니다.")
driver.quit()