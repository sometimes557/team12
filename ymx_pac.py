import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.amazon.com/',
    'Connection': 'keep-alive',
    'cookie': 'csm-sid=121-5133778-1652741; x-amz-captcha-1=1754669623699695; x-amz-captcha-2=bqaMz+R8CaPAfvMuftg6sA==; session-id=140-3422624-9946365; i18n-prefs=USD; ubid-main=131-3565042-2868846; id_pkel=n1; id_pk=eyJuIjoiMSIsImFmIjoiMSIsImNjIjoiMSJ9; session-token="/0o6GwEhQIDcXtGeHTn4Y9QzcjDT/wn4/Pwnd3gHZ/KZeoYrCX/+8etuewLKBV1a2ak0QZXIvnerjjMfdu0Jq4g5fufiskmEV2z79ltkp3XrCTMf6foVT8nK0s/RYKtY3GHIqQT2MyKDKDSV5FISF+bNVdT0fErliSBXjq4NpEIa/gBKbsCaiuZ1r0LzkHTS6/Ng9YEdqM0vCSCbkKd5yQwJ+ci96Q3uHcGmf6sXZZTgifDQTBORafoZkcVZK2JtDCMXo+qsl7AIj2KVsftB88BjF3tUy6vvA3Bp5si/rhfrdrYQ8THbLY1+pVsrS6kVMrB9Bu+kDmUiUirQo4ewUpymj9GmuEoRFs3AIAx4xoSdR2oeXw63Eg=="; x-main="ZGxT@3nf2P6mxAedbdgXlnojqFwiV0m?1IVQqxqh?f4wMs4bjf125dZaIMwxIUMZ"; at-main=Atza|IwEBIFUKW6O1ICzQav5TFbZBUfmuT-JnqPctietLroyXQ9Z05iBIMCaEc62ycVBMSqfssJj7ZWBUNghjkXZEAxQWHQihinW5vFoO9etzISupymUxWSgb1zb1Pv7YppgYD3oOvgPnDF9XAaGPrCng6OmQ7UTTWVtan2vFhRR3xXqA8QmVy8eBpWq3Nzj8S9bpKXfaq1oGXa-8Jf4jQah9iTmHNPq9bwDv-gGqjHf4FryMgyTc5Q; sess-at-main="zb2M0Vw5AtyDjLm7LmebVUp/czxzZen2PayeVVG1bj8="; sst-main=Sst1|PQE3sWIIQluSbRF_TotW7UpOCQxvSRqeIStAzHcJtEzc1HPzEC45ZX8MAZOqDa5zCmT4RYp4WkivIj9eZIfUeRFs3AIAx4xoSdR2oeXw63Eg=="; x-main="ZGxT@3nf2P6mxAedbdgXlnojqFwiV0m?1IVQqxqh?f4wMs4bjf125dZaIMwxIUMZ"; at-main=Atza|IwEBIFUKW6O1ICzQav5TFbZBUfmuT-JnqPctietLroyXQ9Z05iBIMCaEc62ycVBMSqfssJj7ZWBUNghjkXZEAxQWHQihinW5vFoO9etzISupymUxWSgb1zb1Pv7YppgYD3oOvgP nDF9XAaGPrCng6OmQ7UTTWVtan2vFhRR3xXqA8QmVy8eBpWq3Nzj8S9bpKXfaq1oGXa-8Jf4jQah TmHNPq9bwDv-gGqjHf4FryMgyTc5Q; sess-at-main="zb2M0Vw5AtyDjLm7LmebVUp/czxzZen2PayeVVG1bj8="; sst-main=Sst1|PQE3sWIIQluSbRF_TotW7UpOCQxvSRqeIStAzHcJtEzc1HPzEC45ZX8MAZOqDa5zCmT4RYp4WkivIj9eZIfUe6_rwCSgbVKRu0rWVB4UVl9DitQ5o6Qu8m5ysMYCfy0-4gmL2qsLuyYaRA5jAc7pG5Px2z72zob7JSKgrsxQyexg0EHEKw8kIly5JNPA031zP2ESVrwtewYg3HWRJamiCd53BSeYNQEGybdYdXnp9J9KSs0pxAccLB94GMUKwbvzpAXpajTk0avZVJ0R6KdODkl6QPgmy-efkcqR4lTIodQrUqs; session-id-time=2082787201l; lc-main=en_US; csm-hit=tb:9KRJTN1KEQR5HPBWMK3X+s-9KRJTN1KEQR5HPBWMK3X|1754662802149&t:1754662802149&adb:adblk_no; rxc=AG1e+PzuCY6aSn2+Ef4'
}


def scrape_amazon_reviews(product_id, max_pages=5):
    base_url = f"https://www.amazon.com/product-reviews/{product_id}"
    reviews = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}/?pageNumber={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        for review in soup.find_all('li', {'data-hook': 'review'}):
            # 提取用户名
            username_elem = review.find('span', class_='a-profile-name')
            username = username_elem.text.strip() if username_elem else 'N/A'

            # 提取评分
            rating_elem = review.find('i', {'data-hook': 'review-star-rating'})
            rating = float(rating_elem.text.split()[0]) if rating_elem else 0.0

            # 提取标题
            title_elem = review.find('a', {'data-hook': 'review-title'})
            title = title_elem.text.strip() if title_elem else 'N/A'

            # 提取评论内容
            body_elem = review.find('span', {'data-hook': 'review-body'})
            body = body_elem.text.strip() if body_elem else 'N/A'

            # 提取日期
            date_elem = review.find('span', {'data-hook': 'review-date'})
            date = date_elem.text.strip() if date_elem else 'N/A'

            review_data = {
                'username': username,
                'rating': rating,
                'title': title,
                'body': body,
                'date': date
            }
            reviews.append(review_data)
        time.sleep(2)  # 降低请求频率

    return pd.DataFrame(reviews)


if __name__ == "__main__":
    test_product_id = "1593279280"  # 示例产品ID

    try:
        reviews_df = scrape_amazon_reviews(test_product_id, max_pages=2)

        print(f"成功爬取 {len(reviews_df)} 条评论")

        # 保存评论数据到CSV文件
        reviews_df.to_csv('amazon_reviews.csv', index=False, encoding='utf-8')
        print("评论数据已保存到 amazon_reviews.csv")

        # 增加调试信息：检查请求是否正常
        test_url = f"https://www.amazon.com/product-reviews/{test_product_id}/?pageNumber=1"
        test_response = requests.get(test_url, headers=headers)
        print(f"\n测试请求状态码：{test_response.status_code}")  # 200表示正常
        print(f"响应内容长度：{len(test_response.text)}")  # 若过小可能被反爬

        # 检查是否被亚马逊识别为机器人
        if "robot" in test_response.text.lower() or "captcha" in test_response.text.lower():
            print("警告：请求可能被亚马逊反爬机制拦截（检测到机器人验证）")

        # 保存原始HTML用于分析页面结构
        with open("amazon_test_page.html", "w", encoding="utf-8") as f:
            f.write(test_response.text)
        print("原始页面HTML已保存到 amazon_test_page.html，可用于检查选择器是否有效")

        if len(reviews_df) == 0:
            print("未爬取到数据，可能原因：")
            print("1. 页面结构变化，选择器失效")
            print("2. 被亚马逊反爬机制拦截")
            print("3. 产品ID无效或无评论")

    except Exception as e:
        print(f"测试过程中出现错误：{str(e)}")