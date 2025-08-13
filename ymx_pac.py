from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import requests
import os

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0'
]


headers = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.amazon.com/',
    'Connection': 'keep-alive',
    'cookie': 'csm-sid=121-5133778-1652741; x-amz-captcha-1=1754669623699695; x-amz-captcha-2=bqaMz+R8CaPAfvMuftg6sA==; session-id=140-3422624-9946365; i18n-prefs=USD; ubid-main=131-3565042-2868846; at-main=Atza|IwEBIFUKW6O1ICzQav5TFbZBUfmuT-JnqPctietLroyXQ9Z05iBIMCaEc62ycVBMSqfssJj7ZWBUNghjkXZEAxQWHQihinW5vFoO9etzISupymUxWSgb1zb1Pv7YppgYD3oOvgPnDF9XAaGPrCng6OmQ7UTTWVtan2vFhRR3xXqA8QmVy8eBpWq3Nzj8S9bpKXfaq1oGXa-8Jf4jQah9iTmHNPq9bwDv-gGqjHf4FryMgyTc5Q; sess-at-main="zb2M0Vw5AtyDjLm7LmebVUp/czxzZen2PayeVVG1bj8="; sst-main=Sst1|PQE3sWIIQluSbRF_TotW7UpOCQxvSRqeIStAzHcJtEzc1HPzEC45ZX8MAZOqDa5zCmT4RYp4WkivIj9eZIfUe6_rwCSgbVKRu0rWVB4UVl9DitQ5o6Qu8m5ysMYCfy0-4gmL2qsLuyYaRA5jAc7pG5Px2z72zob7JSKgrsxQyexg0EHEKw8kIly5JNPA031zP2ESVrwtewYg3HWRJamiCd53BSeYNQEGybdYdXnp9J9KSs0pxAccLB94GMUKwbvzpAXpajTk0avZVJ0R6KdODkl6QPgmy-efkcqR4lTIodQrUqs; session-id-time=2082787201l; lc-main=en_US; session-token=bVkq8w3UpszouRlxO1GQF5H1w+lAYBWQ0xmjzbA/vAf8sLIXToR/qnx8lY/Zq9nJgScxoTulzGP4h8GcnydKT27CGROKeyAAxkF7xD/lQrajQPjkYzoIlyyZpsF4dTLtBI/yUSUW2hJJ1jyVKG6cu6f7AfZXYcU3Spqu07mckE40EqECBkeYcjRdJdM/BlgOt/FOSv8xEb5vV0nPzgI3zZKrKpN+Bj24L57FPoo/S8xNyaWYlWOt02AGht3JdB/TtkiFLs+sI2Yd95pWNBxCIabS+Qq8BHfWN6fV4jLC+Hsd5nuB/yIkl+C/TegsrVlwAf3I27msGpHzcdPC5btTD53T0vVLKDtr5xxCJHMlFmI4z/X30ByzAkXFtJUpW2jo; x-main="yUGmFQN@5K?dTGM1Y6HCvFPcmVxGRJnrn@aA1VsFZGmOrmPABYfnmcBTE40feDlk"; sp-cdn="L5Z9:CN"; skin=noskin; rxc=AGBIg3HbWn7VKRI7hVs; aws-waf-token=8126667e-de5a-4dfa-b5b7-223a165f7bd1:AgoAujoEvsymAAAA:cSzLUrrx7GqeHemQE/aNNkQSNqAUNEIH7N36bxAOfJrdeqEX4OQ9/UJ4QdBUZOINcxM/ZHUbIeNyx59OF+Jys8Xy8YMug7OEsoVP4tPMm3bfu/y1Uy3Z7DFa7ZalGNkz/aXneb0mlHk3akYiAkZ2gtPLOgXR1prU9j7DE60nsP19klw/doAiJc1wzah+YJPUVw==; csm-hit=tb:1MHREJ0Z1FYYRMKHGCNF+s-8PCGS3Z23YY9DQCNPZ2P|1754960003546&t:1754960003546&adb:adblk_no'
}


def scrape_amazon_reviews(product_id, product_title, max_pages=5):
    base_url = f"https://www.amazon.com/product-reviews/{product_id}"
    reviews = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}/?pageNumber={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 修改评论容器选择器：从div改为li
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
            date = date_elem.text.strip().replace('Reviewed in the United States on ', '') if date_elem else 'N/A'

            review_data = {
                'product_id': product_id,
                'product_title': product_title,
                'username': username,
                'rating': rating,
                'title': title,
                'body': body,
                'date': date
            }
            reviews.append(review_data)
        # 添加随机延迟避免被反爬
        time.sleep(random.uniform(2, 4))

    return pd.DataFrame(reviews)


if __name__ == "__main__":
    try:
        # 从CSV文件读取产品ID和标题
        products_df = pd.read_csv('amazon_product_ids.csv')
        print(f"从amazon_product_ids.csv读取到 {len(products_df)} 个产品")

        for index, row in products_df.iterrows():
            product_id = row['product_id']
            product_title = row['title']
            print(f"\n正在处理产品: {product_title} (ID: {product_id})")

            # 增加调试信息：检查请求是否正常
            test_url = f"https://www.amazon.com/product-reviews/{product_id}/?pageNumber=1"
            test_response = requests.get(test_url, headers=headers)
            print(f"测试请求状态码：{test_response.status_code}")  # 200表示正常
            print(f"响应内容长度：{len(test_response.text)}")  # 若过小可能被反爬

            # 检查是否被亚马逊识别为机器人
            if "robot" in test_response.text.lower() or "captcha" in test_response.text.lower():
                print("警告：请求可能被亚马逊反爬机制拦截（检测到机器人验证）")

            # 保存原始HTML用于分析页面结构
            html_filename = f"amazon_test_page_{product_id}.html"
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(test_response.text)
            print(f"原始页面HTML已保存到 {html_filename}，可用于检查选择器是否有效")

            # 爬取评论
            reviews_df = scrape_amazon_reviews(product_id, product_title, max_pages=2)

            # 新增：立即保存到CSV（追加模式）
            file_exists = os.path.isfile('amazon_reviews.csv')
            reviews_df.to_csv('amazon_reviews.csv',
                            mode='a' if file_exists else 'w',  # 存在则追加，否则新建
                            header=not file_exists,            # 仅首次写入表头
                            index=False,
                            encoding='utf-8')

            print(f"成功爬取并保存 {len(reviews_df)} 条评论")
            time.sleep(random.uniform(2, 4))

        print("\n所有产品评论爬取完成")
    except FileNotFoundError:
        print("错误: 未找到amazon_product_ids.csv文件，请先运行ymx_pac.py生成产品ID文件")
    except Exception as e:
        print(f"处理过程中出现错误：{str(e)}")