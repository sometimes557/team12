import requests
import time
import random
import csv
from bs4 import BeautifulSoup

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0'
]

# 设置请求头
headers = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.amazon.com/',
    'Connection': 'keep-alive',
    'cookie': 'csm-sid=121-5133778-1652741; x-amz-captcha-1=1754669623699695; x-amz-captcha-2=bqaMz+R8CaPAfvMuftg6sA==; session-id=140-3422624-9946365; i18n-prefs=USD; ubid-main=131-3565042-2868846; at-main=Atza|IwEBIFUKW6O1ICzQav5TFbZBUfmuT-JnqPctietLroyXQ9Z05iBIMCaEc62ycVBMSqfssJj7ZWBUNghjkXZEAxQWHQihinW5vFoO9etzISupymUxWSgb1zb1Pv7YppgYD3oOvgPnDF9XAaGPrCng6OmQ7UTTWVtan2vFhRR3xXqA8QmVy8eBpWq3Nzj8S9bpKXfaq1oGXa-8Jf4jQah9iTmHNPq9bwDv-gGqjHf4FryMgyTc5Q; sess-at-main="zb2M0Vw5AtyDjLm7LmebVUp/czxzZen2PayeVVG1bj8="; sst-main=Sst1|PQE3sWIIQluSbRF_TotW7UpOCQxvSRqeIStAzHcJtEzc1HPzEC45ZX8MAZOqDa5zCmT4RYp4WkivIj9eZIfUe6_rwCSgbVKRu0rWVB4UVl9DitQ5o6Qu8m5ysMYCfy0-4gmL2qsLuyYaRA5jAc7pG5Px2z72zob7JSKgrsxQyexg0EHEKw8kIly5JNPA031zP2ESVrwtewYg3HWRJamiCd53BSeYNQEGybdYdXnp9J9KSs0pxAccLB94GMUKwbvzpAXpajTk0avZVJ0R6KdODkl6QPgmy-efkcqR4lTIodQrUqs; session-id-time=2082787201l; lc-main=en_US; session-token=bVkq8w3UpszouRlxO1GQF5H1w+lAYBWQ0xmjzbA/vAf8sLIXToR/qnx8lY/Zq9nJgScxoTulzGP4h8GcnydKT27CGROKeyAAxkF7xD/lQrajQPjkYzoIlyyZpsF4dTLtBI/yUSUW2hJJ1jyVKG6cu6f7AfZXYcU3Spqu07mckE40EqECBkeYcjRdJdM/BlgOt/FOSv8xEb5vV0nPzgI3zZKrKpN+Bj24L57FPoo/S8xNyaWYlWOt02AGht3JdB/TtkiFLs+sI2Yd95pWNBxCIabS+Qq8BHfWN6fV4jLC+Hsd5nuB/yIkl+C/TegsrVlwAf3I27msGpHzcdPC5btTD53T0vVLKDtr5xxCJHMlFmI4z/X30ByzAkXFtJUpW2jo; x-main="yUGmFQN@5K?dTGM1Y6HCvFPcmVxGRJnrn@aA1VsFZGmOrmPABYfnmcBTE40feDlk"; sp-cdn="L5Z9:CN"; skin=noskin; rxc=AGBIg3HbWn7VKRI7hVs; aws-waf-token=8126667e-de5a-4dfa-b5b7-223a165f7bd1:AgoAujoEvsymAAAA:cSzLUrrx7GqeHemQE/aNNkQSNqAUNEIH7N36bxAOfJrdeqEX4OQ9/UJ4QdBUZOINcxM/ZHUbIeNyx59OF+Jys8Xy8YMug7OEsoVP4tPMm3bfu/y1Uy3Z7DFa7ZalGNkz/aXneb0mlHk3akYiAkZ2gtPLOgXR1prU9j7DE60nsP19klw/doAiJc1wzah+YJPUVw==; csm-hit=tb:1MHREJ0Z1FYYRMKHGCNF+s-8PCGS3Z23YY9DQCNPZ2P|1754960003546&t:1754960003546&adb:adblk_no'
}


def search_amazon_products(keyword, max_pages=1):
    product_data = []
    session = requests.Session()
    session.headers.update(headers)

    for page in range(1, max_pages + 1):
        print(f"搜索第 {page} 页...")
        url = f"https://www.amazon.com/s?k={keyword}&page={page}"

        try:
            # 发送请求
            response = session.get(url, timeout=10)

            # 调试信息
            print(f"状态码: {response.status_code}")
            print(f"内容长度: {len(response.content)} bytes")

            # 检测机器人验证
            if 'api-services-support@amazon.com' in response.text or 'Robot Check' in response.text:
                print("警告: 可能触发了机器人检测")

            # 保存原始HTML
            html_filename = f"amazon_search_{keyword}_page{page}.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"已保存HTML到 {html_filename}")

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取产品ID和标题
            title_containers = soup.find_all('div', {'data-cy': 'title-recipe'})
            print(f"找到 {len(title_containers)} 个产品容器")

            for container in title_containers:
                # 获取产品ID
                product_id = None
                parent_div = container.find_parent('div', {'data-asin': True})
                if parent_div:
                    product_id = parent_div['data-asin']

                # 获取标题
                title = None
                title_tag = container.select_one('h2[class*="a-size-"]')
                if title_tag:
                    title = title_tag.get_text(strip=True)

                # 新增：获取图片URL
                image_url = None
                if parent_div:
                    # 查找图片容器
                    image_container = parent_div.find('div', class_='s-product-image-container')
                    if image_container:
                        # 查找图片标签
                        img_tag = image_container.find('img', class_='s-image')
                        if img_tag and 'src' in img_tag.attrs:
                            image_url = img_tag['src']
                        elif img_tag and 'data-src' in img_tag.attrs:
                            # 有时图片URL存储在data-src属性中
                            image_url = img_tag['data-src']

                if product_id:
                    product_data.append({
                        'product_id': product_id,
                        'title': title or 'N/A',
                        'image_url': image_url or 'N/A'  # 新增图片URL字段
                    })
                    print(f"提取产品: {title} (ID: {product_id})")
                    if image_url:
                        print(f"图片URL: {image_url}")

            # 随机延迟，避免被封禁
            delay = random.uniform(2, 4)
            print(f"等待 {delay:.2f} 秒...\n")
            time.sleep(delay)

        except Exception as e:
            print(f"请求错误: {str(e)}")
            break

    return product_data


def save_to_csv(data, filename='amazon_product_ids.csv'):
    if not data:
        print("没有数据可保存")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        # CSV头部添加标题字段（新增image_url）
        fieldnames = ['product_id', 'title', 'image_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in data:
            writer.writerow(item)

    print(f"已保存 {len(data)} 条产品数据到 {filename}")


if __name__ == "__main__":
    search_keyword = input("请输入搜索关键词: ").strip()
    if not search_keyword:
        search_keyword = "iphone"
        print(f"未输入关键词，使用默认关键词: {search_keyword}")

    products = search_amazon_products(search_keyword, max_pages=1)
    save_to_csv(products)
    print("程序完成")