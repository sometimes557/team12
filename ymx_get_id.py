import requests
import time
import random
import csv
from bs4 import BeautifulSoup

# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.amazon.com/',
    'Connection': 'keep-alive',
    'cookie': 'csm-sid=121-5133778-1652741; x-amz-captcha-1=1754669623699695; x-amz-captcha-2=bqaMz+R8CaPAfvMuftg6sA==; session-id=140-3422624-9946365; i18n-prefs=USD; ubid-main=131-3565042-2868846; id_pkel=n1; id_pk=eyJuIjoiMSIsImFmIjoiMSIsImNjIjoiMSJ9; session-token="/0o6GwEhQIDcXtGeHTn4Y9QzcjDT/wn4/Pwnd3gHZ/KZeoYrCX/+8etuewLKBV1a2ak0QZXIvnerjjMfdu0Jq4g5fufiskmEV2z79ltkp3XrCTMf6foVT8nK0s/RYKtY3GHIqQT2MyKDKDSV5FISF+bNVdT0fErliSBXjq4NpEIa/gBKbsCaiuZ1r0LzkHTS6/Ng9YEdqM0vCSCbkKd5yQwJ+ci96Q3uHcGmf6sXZZTgifDQTBORafoZkcVZK2JtDCMXo+qsl7AIj2KVsftB88BjF3tUy6vvA3Bp5si/rhfrdrYQ8THbLY1+pVsrS6kVMrB9Bu+kDmUiUirQo4ewUpymj9GmuEoRFs3AIAx4xoSdR2oeXw63Eg=="; x-main="ZGxT@3nf2P6mxAedbdgXlnojqFwiV0m?1IVQqxqh?f4wMs4bjf125dZaIMwxIUMZ"; at-main=Atza|IwEBIFUKW6O1ICzQav5TFbZBUfmuT-JnqPctietLroyXQ9Z05iBIMCaEc62ycVBMSqfssJj7ZWBUNghjkXZEAxQWHQihinW5vFoO9etzISupymUxWSgb1zb1Pv7YppgYD3oOvgPnDF9XAaGPrCng6OmQ7UTTWVtan2vFhRR3xXqA8QmVy8eBpWq3Nzj8S9bpKXfaq1oGXa-8Jf4jQah9iTmHNPq9bwDv-gGqjHf4FryMgyTc5Q; sess-at-main="zb2M0Vw5AtyDjLm7LmebVUp/czxzZen2PayeVVG1bj8="; sst-main=Sst1|PQE3sWIIQluSbRF_TotW7UpOCQxvSRqeIStAzHcJtEzc1HPzEC45ZX8MAZOqDa5zCmT4RYp4WkivIj9eZIfUeRFs3AIAx4xoSdR2oeXw63Eg=="; x-main="ZGxT@3nf2P6mxAedbdgXlnojqFwiV0m?1IVQqxqh?f4wMs4bjf125dZaIMwxIUMZ"; at-main=Atza|IwEBIFUKW6O1ICzQav5TFbZBUfmuT-JnqPctietLroyXQ9Z05iBIMCaEc62ycVBMSqfssJj7ZWBUNghjkXZEAxQWHQihinW5vFoO9etzISupymUxWSgb1zb1Pv7YppgYD3oOvgP nDF9XAaGPrCng6OmQ7UTTWVtan2vFhRR3xXqA8QmVy8eBpWq3Nzj8S9bpKXfaq1oGXa-8Jf4jQah TmHNPq9bwDv-gGqjHf4FryMgyTc5Q; sess-at-main="zb2M0Vw5AtyDjLm7LmebVUp/czxzZen2PayeVVG1bj8="; sst-main=Sst1|PQE3sWIIQluSbRF_TotW7UpOCQxvSRqeIStAzHcJtEzc1HPzEC45ZX8MAZOqDa5zCmT4RYp4WkivIj9eZIfUe6_rwCSgbVKRu0rWVB4UVl9DitQ5o6Qu8m5ysMYCfy0-4gmL2qsLuyYaRA5jAc7pG5Px2z72zob7JSKgrsxQyexg0EHEKw8kIly5JNPA031zP2ESVrwtewYg3HWRJamiCd53BSeYNQEGybdYdXnp9J9KSs0pxAccLB94GMUKwbvzpAXpajTk0avZVJ0R6KdODkl6QPgmy-efkcqR4lTIodQrUqs; session-id-time=2082787201l; lc-main=en_US; csm-hit=tb:9KRJTN1KEQR5HPBWMK3X+s-9KRJTN1KEQR5HPBWMK3X|1754662802149&t:1754662802149&adb:adblk_no; rxc=AG1e+PzuCY6aSn2+Ef4'
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

                if product_id:
                    product_data.append({
                        'product_id': product_id,
                        'title': title or 'N/A'
                    })
                    print(f"提取产品: {title} (ID: {product_id})")

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
        # CSV头部添加标题字段
        fieldnames = ['product_id', 'title']
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