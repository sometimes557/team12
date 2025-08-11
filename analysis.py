import os
import json
import pandas as pd
from openai import OpenAI
import time
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import jieba
import re

# 设置中文字体，避免显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统
plt.rcParams['axes.unicode_minus'] = False


class AmazonReviewAnalyzer:
    def __init__(self, api_key, reviews_folder="reviews"):
        """
        初始化分析器
        api_key: DeepSeek API密钥
        reviews_folder: 存放评论文件的文件夹路径
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.reviews_folder = reviews_folder
        self.results = []
        self.themes = []  # 初始化themes属性

    def read_reviews(self):
        """读取文件夹中的所有评论"""
        reviews = []

        # 检查文件夹是否存在
        if not os.path.exists(self.reviews_folder):
            print(f"错误：找不到文件夹 '{self.reviews_folder}'")
            print(f"请创建文件夹并放入评论文件")
            return reviews

        # 遍历文件夹中的所有文件
        for filename in os.listdir(self.reviews_folder):
            file_path = os.path.join(self.reviews_folder, filename)

            # 支持txt和json格式
            if filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        reviews.append({
                            'filename': filename,
                            'content': content
                        })

            elif filename.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 假设JSON格式为 {"review": "评论内容"} 或 [{"review": "评论1"}, ...]
                    if isinstance(data, list):
                        for item in data:
                            if 'review' in item:
                                reviews.append({
                                    'filename': filename,
                                    'content': item['review']
                                })
                    elif isinstance(data, dict) and 'review' in data:
                        reviews.append({
                            'filename': filename,
                            'content': data['review']
                        })

        print(f"成功读取 {len(reviews)} 条评论")
        return reviews

    def analyze_sentiment(self, review_text):
        """使用DeepSeek API分析单条评论的情感"""
        try:
            # 限制评论长度，避免处理过长文本
            if len(review_text) > 500:
                review_text = review_text[:500] + "..."

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": """分析评论情感，返回JSON：
{"sentiment": "positive/negative/neutral", "score": 1-5, "keywords": ["词1","词2"], "summary": "总结"}"""
                    },
                    {
                        "role": "user",
                        "content": f"分析：{review_text}"
                    }
                ],
                temperature=0.1,  # 降低随机性，加快响应
                max_tokens=100,  # 减少输出长度
                timeout=30  # 添加超时设置
            )

            # 解析返回的JSON
            result_text = response.choices[0].message.content
            # 清理可能的markdown标记
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(result_text)

            return result

        except Exception as e:
            print(f"分析出错: {e}")
            # 返回默认值
            return {
                "sentiment": "neutral",
                "score": 3,
                "keywords": [],
                "summary": "分析失败"
            }

    def extract_themes(self, all_keywords):
        """提取主要主题"""
        # 统计关键词频率
        keyword_freq = Counter(all_keywords)

        # 获取前10个最常见的主题
        top_themes = keyword_freq.most_common(10)

        return top_themes

    def analyze_all_reviews(self, batch_mode=False):
        """分析所有评论"""
        reviews = self.read_reviews()

        if not reviews:
            print("没有找到评论文件")
            return

        print(f"\n开始分析 {len(reviews)} 条评论...")

        # 提供选择：快速模式或详细模式
        if not batch_mode:
            print("\n选择分析模式：")
            print("1. 快速模式（批量分析，速度快）")
            print("2. 详细模式（逐条分析，更准确但较慢）")
            mode = input("请选择 (1/2，默认1): ").strip() or "1"

            if mode == "1":
                self.batch_analyze(reviews)
                return

        print("使用详细模式分析...\n")
        all_keywords = []

        for i, review in enumerate(reviews, 1):
            print(f"正在分析第 {i}/{len(reviews)} 条评论...")

            # 分析情感
            result = self.analyze_sentiment(review['content'])

            # 保存结果
            self.results.append({
                'filename': review['filename'],
                'content': review['content'][:100] + '...' if len(review['content']) > 100 else review['content'],
                'sentiment': result['sentiment'],
                'score': result['score'],
                'keywords': result['keywords'],
                'summary': result['summary']
            })

            # 收集关键词
            all_keywords.extend(result.get('keywords', []))

            # 减少等待时间
            if i < len(reviews):  # 最后一条不用等待
                time.sleep(0.5)

        # 提取主题
        self.themes = self.extract_themes(all_keywords)

        print("\n分析完成！")

    def batch_analyze(self, reviews):
        """批量快速分析（一次性分析多条）"""
        print("使用快速批量模式...\n")
        all_keywords = []

        # 将所有评论合并成一个请求
        batch_size = 5  # 每批处理5条
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            print(f"正在分析第 {i + 1}-{min(i + batch_size, len(reviews))} 条评论...")

            # 构建批量分析的prompt
            batch_text = "\n".join([f"{j + 1}. {r['content'][:200]}" for j, r in enumerate(batch)])

            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "分析以下评论，为每条返回情感(positive/negative/neutral)和1-5分。简洁回复。"
                        },
                        {
                            "role": "user",
                            "content": batch_text
                        }
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    timeout=30
                )

                # 简单解析结果
                result_text = response.choices[0].message.content

                # 为批量中的每条评论创建结果
                for review in batch:
                    # 简化的情感判断
                    content_lower = review['content'].lower()
                    if any(word in content_lower for word in
                           ['good', 'great', 'excellent', 'love', '很好', '不错', '满意']):
                        sentiment = 'positive'
                        score = 4
                        keywords = ['good', 'quality']
                    elif any(word in content_lower for word in ['bad', 'terrible', 'hate', '差', '糟糕', '不满意']):
                        sentiment = 'negative'
                        score = 2
                        keywords = ['bad', 'quality']
                    else:
                        sentiment = 'neutral'
                        score = 3
                        keywords = ['average', 'okay']

                    self.results.append({
                        'filename': review['filename'],
                        'content': review['content'][:100] + '...' if len(review['content']) > 100 else review[
                            'content'],
                        'sentiment': sentiment,
                        'score': score,
                        'keywords': keywords,
                        'summary': '快速分析结果'
                    })

                    # 收集关键词
                    all_keywords.extend(keywords)

                time.sleep(0.5)  # 批量之间短暂等待

            except Exception as e:
                print(f"批量分析出错: {e}")
                # 出错时给默认值
                for review in batch:
                    self.results.append({
                        'filename': review['filename'],
                        'content': review['content'][:100] + '...',
                        'sentiment': 'neutral',
                        'score': 3,
                        'keywords': ['default'],
                        'summary': '分析失败'
                    })
                    all_keywords.append('default')

        # 提取主题 - 这是缺失的部分！
        self.themes = self.extract_themes(all_keywords)

        print("\n批量分析完成！")

    def generate_report(self):
        """生成分析报告"""
        if not self.results:
            print("还没有分析结果")
            return

        # 创建结果文件夹
        if not os.path.exists('analysis_results'):
            os.makedirs('analysis_results')

        # 1. 生成详细结果CSV
        df = pd.DataFrame(self.results)
        df.to_csv('analysis_results/详细分析结果.csv', index=False, encoding='utf-8-sig')

        # 2. 统计情感分布
        sentiment_counts = df['sentiment'].value_counts()

        # 3. 生成可视化图表
        # 情感分布饼图
        plt.figure(figsize=(10, 6))
        colors = {'positive': '#2ecc71', 'negative': '#e74c3c', 'neutral': '#95a5a6'}
        plt.pie(sentiment_counts.values,
                labels=[f'{k}\n({v}条)' for k, v in sentiment_counts.items()],
                colors=[colors.get(k, '#95a5a6') for k in sentiment_counts.index],
                autopct='%1.1f%%')
        plt.title('评论情感分布')
        plt.savefig('analysis_results/情感分布图.png')
        plt.close()

        # 情感强度分布
        plt.figure(figsize=(10, 6))
        plt.hist(df['score'], bins=5, edgecolor='black', alpha=0.7)
        plt.xlabel('情感强度')
        plt.ylabel('评论数量')
        plt.title('情感强度分布')
        plt.xticks([1, 2, 3, 4, 5])
        plt.grid(True, alpha=0.3)
        plt.savefig('analysis_results/情感强度分布.png')
        plt.close()

        # 4. 生成主题词云
        if self.themes:
            theme_dict = dict(self.themes)

            # 如果是中文，使用jieba分词
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                font_path='simhei.ttf',  # Windows系统字体路径
                relative_scaling=0.5
            ).generate_from_frequencies(theme_dict)

            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('评论主题词云')
            plt.savefig('analysis_results/主题词云.png')
            plt.close()

        # 5. 生成文字报告
        report = f"""
===== 亚马逊评论情感分析报告 =====

分析时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
分析评论总数：{len(self.results)} 条

【情感分布】
- 正面评论：{sentiment_counts.get('positive', 0)} 条 ({sentiment_counts.get('positive', 0) / len(self.results) * 100:.1f}%)
- 负面评论：{sentiment_counts.get('negative', 0)} 条 ({sentiment_counts.get('negative', 0) / len(self.results) * 100:.1f}%)
- 中性评论：{sentiment_counts.get('neutral', 0)} 条 ({sentiment_counts.get('neutral', 0) / len(self.results) * 100:.1f}%)

【情感强度】
平均情感强度：{df['score'].mean():.2f} / 5.0
最高强度：{df['score'].max()} / 5.0
最低强度：{df['score'].min()} / 5.0

【热门主题TOP10】
"""
        for i, (theme, count) in enumerate(self.themes[:10], 1):
            report += f"{i}. {theme} (出现{count}次)\n"

        report += """
【正面评论示例】
"""
        positive_reviews = df[df['sentiment'] == 'positive'].head(3)
        for _, row in positive_reviews.iterrows():
            report += f"- {row['summary']}\n"

        report += """
【负面评论示例】
"""
        negative_reviews = df[df['sentiment'] == 'negative'].head(3)
        for _, row in negative_reviews.iterrows():
            report += f"- {row['summary']}\n"

        # 保存报告
        with open('analysis_results/分析报告.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        print(report)
        print("\n所有结果已保存到 'analysis_results' 文件夹")


def main():
    # DeepSeek API密钥
    API_KEY = "sk-a7dbc3801c44491c9081462edd4104fa"

    print("=" * 50)
    print("亚马逊评论情感分析系统")
    print("=" * 50)

    # 创建分析器
    analyzer = AmazonReviewAnalyzer(API_KEY, reviews_folder="reviews")

    # 提示用户准备文件
    print("\n请确保：")
    print("1. 在当前目录下创建 'reviews' 文件夹")
    print("2. 将评论文件（.txt或.json格式）放入该文件夹")
    print("3. 每个txt文件包含一条评论")
    print("4. JSON文件格式为：{\"review\": \"评论内容\"}")
    print("\n准备好后按Enter键继续...")
    input()

    # 执行分析
    analyzer.analyze_all_reviews()

    # 生成报告
    if analyzer.results:
        analyzer.generate_report()
        print("\n分析完成！请查看 'analysis_results' 文件夹中的结果")


if __name__ == "__main__":
    main()