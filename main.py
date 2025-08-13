import os
import json
import pandas as pd
from openai import OpenAI
import time
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
from datetime import datetime
import warnings
import concurrent.futures
import threading

warnings.filterwarnings('ignore')

# 设置中文字体
import platform

if platform.system() == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
elif platform.system() == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC']
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False


class CSVToReviewsConverter:
    """将CSV格式的亚马逊评论转换为分析系统可用的格式"""

    def __init__(self, csv_file_path, output_folder="reviews"):
        self.csv_file_path = csv_file_path
        self.output_folder = output_folder
        self.df = None

    def read_csv(self):
        """读取CSV文件"""
        try:
            self.df = pd.read_csv(self.csv_file_path, encoding='utf-8')
            print(f"✓ 成功读取CSV文件: {self.csv_file_path}")
            print(f"  共 {len(self.df)} 条评论")

            # 检查数据完整性
            print(f"  列名: {list(self.df.columns)}")

            # 显示几条样本数据
            if len(self.df) > 0:
                print(f"\n样本数据预览:")
                sample = self.df.iloc[0]
                print(f"  评分: {sample['rating']}")
                print(f"  标题: {sample['title'][:50]}...")
                print(f"  正文: {sample['body'][:100]}...")

            return True
        except Exception as e:
            print(f"❌ 读取CSV文件失败: {e}")
            return False

    def create_output_folder(self):
        """创建输出文件夹"""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"✓ 创建输出文件夹: {self.output_folder}/")
        else:
            # 清空已有的文件
            for file in os.listdir(self.output_folder):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.output_folder, file))
            print(f"✓ 清理输出文件夹: {self.output_folder}/")

    def convert_to_json_batch(self):
        """生成JSON批量文件 - 修复版"""
        print("正在转换为JSON文件...")

        reviews_list = []

        for idx, row in self.df.iterrows():
            # 确保正确提取每个字段
            try:
                # 清理和组合评论内容
                title = str(row['title']).strip() if pd.notna(row['title']) else ""
                body = str(row['body']).strip() if pd.notna(row['body']) else ""

                # 组合标题和正文
                if title and body:
                    review_content = f"{title}. {body}"
                elif body:
                    review_content = body
                elif title:
                    review_content = title
                else:
                    continue  # 跳过空评论

                # 创建评论对象
                review_obj = {
                    'review': review_content,
                    'rating': float(row['rating']) if pd.notna(row['rating']) else 3.0,
                    'username': str(row['username']) if pd.notna(row['username']) else "Anonymous",
                    'date': str(row['date']) if pd.notna(row['date']) else "",
                    'product_title': str(row['product_title']) if pd.notna(row['product_title']) else ""
                }

                reviews_list.append(review_obj)

            except Exception as e:
                print(f"处理第{idx}行时出错: {e}")
                continue

        print(f"  成功处理 {len(reviews_list)} 条有效评论")

        # 分批保存
        batch_size = 20  # 减小批次大小
        file_count = 0

        for i in range(0, len(reviews_list), batch_size):
            batch = reviews_list[i:i + batch_size]
            filename = f"reviews_batch_{file_count + 1:03d}.json"
            filepath = os.path.join(self.output_folder, filename)

            # 保存为JSON格式
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(batch, f, ensure_ascii=False, indent=2)

            file_count += 1

        print(f"✓ 已生成 {file_count} 个JSON文件")

        # 验证第一个文件
        first_file = os.path.join(self.output_folder, "reviews_batch_001.json")
        if os.path.exists(first_file):
            with open(first_file, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
                if sample_data and len(sample_data) > 0:
                    print(f"\n验证第一条评论:")
                    print(f"  评分: {sample_data[0].get('rating', 'N/A')}")
                    print(f"  内容长度: {len(sample_data[0].get('review', ''))} 字符")

        return True

    def generate_csv_summary(self):
        """生成CSV数据摘要"""
        if self.df is None or self.df.empty:
            return

        print("\n📊 CSV数据统计:")
        print(f"  - 总评论数: {len(self.df)}")

        # 评分分布
        rating_counts = self.df['rating'].value_counts().sort_index(ascending=False)
        print(f"\n  评分分布:")
        for rating, count in rating_counts.items():
            percentage = (count / len(self.df)) * 100
            bar = "█" * int(percentage / 2)
            print(f"    {rating:.1f}星: {count:3} 条 ({percentage:5.1f}%) {bar}")

        avg_rating = self.df['rating'].mean()
        print(f"\n  平均评分: {avg_rating:.2f}/5.0")

        # 检查评论内容
        self.df['review_length'] = self.df['body'].fillna('').str.len() + self.df['title'].fillna('').str.len()
        print(f"\n  评论长度:")
        print(f"    平均: {self.df['review_length'].mean():.0f} 字符")
        print(f"    最短: {self.df['review_length'].min()} 字符")
        print(f"    最长: {self.df['review_length'].max()} 字符")

    def convert(self):
        """执行转换"""
        if not self.read_csv():
            return False

        self.create_output_folder()
        self.generate_csv_summary()
        self.convert_to_json_batch()

        return True


class AmazonReviewAnalyzer:
    """亚马逊评论分析器"""

    def __init__(self, api_key, reviews_folder="reviews", use_api=False):
        self.api_key = api_key
        self.reviews_folder = reviews_folder
        self.results = []
        self.themes = []
        self.product_insights = {}
        self.use_api = use_api
        self.api_call_count = 0
        self.lock = threading.Lock()

        if use_api:
            try:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                print("✓ DeepSeek API客户端初始化成功")
            except Exception as e:
                print(f"⚠️ API初始化失败，切换到本地模式: {e}")
                self.use_api = False

    def read_reviews(self):
        """读取文件夹中的所有评论"""
        reviews = []

        if not os.path.exists(self.reviews_folder):
            print(f"文件夹 '{self.reviews_folder}' 不存在")
            return reviews

        file_count = 0
        for filename in os.listdir(self.reviews_folder):
            if filename.startswith('_'):
                continue

            file_path = os.path.join(self.reviews_folder, filename)

            if filename.endswith('.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if 'review' in item:
                                    reviews.append({
                                        'filename': filename,
                                        'content': item['review'],
                                        'rating': item.get('rating', None)
                                    })
                        file_count += 1
                except Exception as e:
                    print(f"读取文件 {filename} 时出错: {e}")

        if reviews:
            print(f"✓ 成功读取 {len(reviews)} 条评论（来自 {file_count} 个文件）")
        else:
            print(f"⚠️ 未找到有效的评论文件")

        return reviews

    def local_sentiment_analysis(self, text, rating=None):
        """改进的本地情感分析 - 考虑评分"""
        text_lower = text.lower()

        # 如果有评分信息，优先使用评分判断
        if rating is not None:
            if rating >= 4.5:
                base_sentiment = 'positive'
                base_score = 4.5
            elif rating >= 3.5:
                base_sentiment = 'positive'
                base_score = 4.0
            elif rating >= 2.5:
                base_sentiment = 'neutral'
                base_score = 3.0
            elif rating >= 1.5:
                base_sentiment = 'negative'
                base_score = 2.0
            else:
                base_sentiment = 'negative'
                base_score = 1.5
        else:
            base_sentiment = 'neutral'
            base_score = 3.0

        # 分析文本内容进行调整

        # 强烈正面短语
        strong_positive_phrases = [
            'highly recommend', 'absolutely love', 'perfect', 'amazing', 'excellent',
            'best purchase', 'very satisfied', 'works perfectly', 'five stars',
            'exceeded expectations', 'fantastic', 'outstanding', 'incredible'
        ]

        # 强烈负面短语
        strong_negative_phrases = [
            'very disappointed', 'waste of money', 'do not buy', 'terrible', 'horrible',
            'poor quality', 'broke', 'doesn\'t work', 'defective', 'worst',
            'not worth', 'avoid', 'scam', 'trash', 'garbage', 'awful',
            'returned', 'refund', 'broken', 'useless', 'cheap quality'
        ]

        # 中性短语
        neutral_phrases = [
            'okay', 'fine', 'decent', 'average', 'not bad', 'alright',
            'acceptable', 'fair', 'reasonable', 'so-so'
        ]

        # 检查强烈短语
        has_strong_positive = any(phrase in text_lower for phrase in strong_positive_phrases)
        has_strong_negative = any(phrase in text_lower for phrase in strong_negative_phrases)
        has_neutral = any(phrase in text_lower for phrase in neutral_phrases)

        # 调整情感判断
        if has_strong_negative:
            sentiment = 'negative'
            score = min(base_score - 1, 2.0)
        elif has_strong_positive:
            sentiment = 'positive'
            score = max(base_score + 0.5, 4.0)
        elif has_neutral:
            sentiment = 'neutral'
            score = 3.0
        else:
            # 计算一般正负词汇
            positive_words = ['good', 'great', 'nice', 'love', 'happy', 'satisfied', 'recommend', 'quality']
            negative_words = ['bad', 'poor', 'disappointed', 'issue', 'problem', 'wrong', 'not working']

            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            if negative_count > positive_count:
                sentiment = 'negative'
                score = min(base_score - 0.5, 2.5)
            elif positive_count > negative_count:
                sentiment = 'positive'
                score = max(base_score, 3.5)
            else:
                sentiment = base_sentiment
                score = base_score

        return {
            'sentiment': sentiment,
            'score': round(score, 1),
            'keywords': self.extract_keywords(text_lower),
            'pros': self.extract_pros(text_lower),
            'cons': self.extract_cons(text_lower),
            'summary': text[:100] + "..." if len(text) > 100 else text
        }

    def extract_keywords(self, text_lower):
        """提取关键词"""
        keywords = []
        important_words = ['quality', 'price', 'shipping', 'delivery', 'design',
                           'battery', 'screen', 'performance', 'value', 'packaging']
        for word in important_words:
            if word in text_lower:
                keywords.append(word)
        return keywords[:5] if keywords else ['product']

    def extract_pros(self, text_lower):
        """提取优点"""
        pros = []
        pros_patterns = {
            'good quality': ['good quality', 'high quality', 'well made', 'durable', 'solid', 'sturdy'],
            'fast delivery': ['fast shipping', 'quick delivery', 'arrived quickly', 'fast delivery'],
            'good value': ['good price', 'great value', 'worth the money', 'affordable'],
            'great design': ['beautiful', 'sleek', 'nice design', 'looks great'],
            'easy to use': ['easy to use', 'user friendly', 'intuitive', 'simple']
        }
        for pro, patterns in pros_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                pros.append(pro)
        return pros

    def extract_cons(self, text_lower):
        """提取缺点"""
        cons = []
        cons_patterns = {
            'poor quality': ['poor quality', 'cheap', 'flimsy', 'broke', 'fragile', 'low quality'],
            'shipping issues': ['late delivery', 'delayed', 'slow shipping', 'damaged', 'poor packaging'],
            'overpriced': ['expensive', 'overpriced', 'not worth', 'too much'],
            'technical issues': ['doesn\'t work', 'not working', 'defective', 'malfunction', 'glitch'],
            'poor design': ['uncomfortable', 'awkward', 'heavy', 'bulky']
        }
        for con, patterns in cons_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                cons.append(con)
        return cons

    def analyze_all_reviews(self):
        """分析所有评论 - 修复版"""
        reviews = self.read_reviews()
        if not reviews:
            return False

        print(f"\n开始分析 {len(reviews)} 条评论...")
        print("=" * 50)

        all_keywords = []
        all_pros = []
        all_cons = []

        # 逐条分析
        for i, review in enumerate(reviews):
            if (i + 1) % 10 == 0:
                print(f"正在分析第 {i + 1}/{len(reviews)} 条评论...")

            # 使用改进的本地分析，传入评分信息
            result = self.local_sentiment_analysis(
                review['content'],
                review.get('rating', None)
            )

            self.results.append({
                'filename': review.get('filename', 'unknown'),
                'content': review['content'][:100] + '...' if len(review['content']) > 100 else review['content'],
                'sentiment': result['sentiment'],
                'score': result['score'],
                'keywords': result['keywords'],
                'pros': result['pros'],
                'cons': result['cons'],
                'summary': result['summary'],
                'original_rating': review.get('rating', None)
            })

            all_keywords.extend(result['keywords'])
            all_pros.extend(result['pros'])
            all_cons.extend(result['cons'])

        # 提取主题
        self.themes = self.extract_themes(all_keywords)
        self.product_insights = {
            'pros': Counter(all_pros).most_common(10),
            'cons': Counter(all_cons).most_common(10)
        }

        print("\n✓ 分析完成！")

        # 输出统计
        df = pd.DataFrame(self.results)
        sentiment_counts = df['sentiment'].value_counts()

        print(f"\n情感分布:")
        total = len(self.results)
        for sentiment in ['positive', 'neutral', 'negative']:
            count = sentiment_counts.get(sentiment, 0)
            percentage = (count / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 2)
            print(f"  {sentiment:8}: {count:3} 条 ({percentage:5.1f}%) {bar}")

        print("=" * 50)

        return True

    def extract_themes(self, all_keywords):
        """提取主题"""
        keyword_freq = Counter(all_keywords)
        return keyword_freq.most_common(15)

    def generate_comprehensive_analysis(self):
        """生成综合分析报告"""
        if not self.results:
            return ""

        df = pd.DataFrame(self.results)
        total_reviews = len(self.results)
        sentiment_counts = df['sentiment'].value_counts()
        avg_score = df['score'].mean()

        # 获取原始评分的平均值
        original_ratings = [r['original_rating'] for r in self.results if r.get('original_rating')]
        avg_original_rating = sum(original_ratings) / len(original_ratings) if original_ratings else 0

        report = f"""
================================================================================
                        商品综合评价分析报告
================================================================================

【基本信息】
分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析模式：{'DeepSeek API分析' if self.use_api else '快速本地分析'}
分析评论数：{total_reviews} 条
原始平均评分：{avg_original_rating:.2f}/5.0 ⭐
分析平均评分：{avg_score:.2f}/5.0

【总体评价】
{'优秀' if avg_score >= 4.0 else '良好' if avg_score >= 3.5 else '一般' if avg_score >= 3.0 else '较差'}

【情感分布】
😊 正面评价：{sentiment_counts.get('positive', 0)} 条 ({sentiment_counts.get('positive', 0) / total_reviews * 100:.1f}%)
😐 中性评价：{sentiment_counts.get('neutral', 0)} 条 ({sentiment_counts.get('neutral', 0) / total_reviews * 100:.1f}%)
😞 负面评价：{sentiment_counts.get('negative', 0)} 条 ({sentiment_counts.get('negative', 0) / total_reviews * 100:.1f}%)

【核心优势】
"""
        if self.product_insights.get('pros'):
            for i, (pro, count) in enumerate(self.product_insights['pros'][:5], 1):
                report += f"  {i}. {pro} (提及{count}次)\n"
        else:
            report += "  暂无明显优势反馈\n"

        report += "\n【主要问题】\n"
        if self.product_insights.get('cons'):
            for i, (con, count) in enumerate(self.product_insights['cons'][:5], 1):
                report += f"  {i}. {con} (提及{count}次)\n"
        else:
            report += "  暂无明显问题反馈\n"

        report += f"\n【购买建议】\n"
        if avg_score >= 4.0:
            report += "✅ 强烈推荐：该商品获得了大多数用户的高度认可。\n"
        elif avg_score >= 3.5:
            report += "✅ 推荐购买：该商品整体评价良好。\n"
        elif avg_score >= 3.0:
            report += "⚠️ 谨慎考虑：该商品评价一般，存在一些问题。\n"
        else:
            report += "❌ 不推荐：该商品存在较多问题，建议选择其他产品。\n"

        # 添加代表性评论
        report += "\n【代表性评论示例】\n"

        # 正面评论
        positive_reviews = df[df['sentiment'] == 'positive'].head(2)
        if not positive_reviews.empty:
            report += "\n正面评价:\n"
            for _, row in positive_reviews.iterrows():
                report += f"  「{row['summary'][:80]}...」\n"

        # 负面评论
        negative_reviews = df[df['sentiment'] == 'negative'].head(2)
        if not negative_reviews.empty:
            report += "\n负面评价:\n"
            for _, row in negative_reviews.iterrows():
                report += f"  「{row['summary'][:80]}...」\n"

        report += "\n" + "=" * 80 + "\n"
        return report

    def generate_report(self):
        """生成分析报告和图表"""
        if not self.results:
            print("没有分析结果")
            return

        if not os.path.exists('analysis_results'):
            os.makedirs('analysis_results')

        # 生成CSV
        df = pd.DataFrame(self.results)
        df.to_csv('analysis_results/详细分析结果.csv', index=False, encoding='utf-8-sig')

        # 生成文本报告
        report = self.generate_comprehensive_analysis()
        with open('analysis_results/商品综合分析报告.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(report)

        # 生成可视化
        self.generate_visualizations(df)

        print("\n✅ 所有结果已保存到 'analysis_results' 文件夹")

    def generate_visualizations(self, df):
        """生成可视化图表"""
        try:
            sentiment_counts = df['sentiment'].value_counts()

            # 情感分布饼图
            plt.figure(figsize=(10, 6))
            colors = {'positive': '#2ecc71', 'negative': '#e74c3c', 'neutral': '#95a5a6'}

            if not sentiment_counts.empty:
                plt.pie(sentiment_counts.values,
                        labels=[f'{k}\n({v}条)' for k, v in sentiment_counts.items()],
                        colors=[colors.get(k, '#95a5a6') for k in sentiment_counts.index],
                        autopct='%1.1f%%',
                        startangle=90)
                plt.title('评论情感分布', fontsize=16, pad=20)

            plt.savefig('analysis_results/情感分布图.png', dpi=100, bbox_inches='tight')
            plt.close()

            # 情感强度分布
            plt.figure(figsize=(10, 6))
            plt.hist(df['score'], bins=10, edgecolor='black', alpha=0.7, color='skyblue')
            plt.xlabel('情感强度', fontsize=12)
            plt.ylabel('评论数量', fontsize=12)
            plt.title('情感强度分布', fontsize=16, pad=20)
            plt.xticks([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
            plt.grid(True, alpha=0.3)
            plt.axvline(df['score'].mean(), color='red', linestyle='dashed', linewidth=2,
                        label=f'平均分: {df["score"].mean():.2f}')
            plt.legend()
            plt.savefig('analysis_results/情感强度分布.png', dpi=100, bbox_inches='tight')
            plt.close()

            print("✓ 图表生成成功")
        except Exception as e:
            print(f"图表生成时出现问题: {e}")


def main():
    """主函数"""

    # ========== 配置区域 ==========
    CSV_FILE = "amazon_reviews.csv"
    API_KEY = "sk-a7dbc3801c44491c9081462edd4104fa"
    USE_API = True  # False = 本地分析, True = API分析
    # ==============================

    print("=" * 60)
    print("     亚马逊评论智能分析系统 v6.0 (修复版)")
    print("=" * 60)

    # 步骤1: 处理CSV文件
    if os.path.exists(CSV_FILE):
        print(f"\n[步骤1] 处理CSV文件: {CSV_FILE}")

        converter = CSVToReviewsConverter(CSV_FILE, output_folder="reviews")
        if not converter.convert():
            print("CSV处理失败")
            return

        print("\n" + "-" * 50)
    else:
        print(f"\n未找到CSV文件: {CSV_FILE}")
        return

    # 步骤2: 分析评论
    print(f"\n[步骤2] 开始分析评论")
    print(f"模式: {'DeepSeek API分析' if USE_API else '快速本地分析'}")

    analyzer = AmazonReviewAnalyzer(API_KEY, reviews_folder="reviews", use_api=USE_API)

    start_time = time.time()
    success = analyzer.analyze_all_reviews()  # 使用修复的分析方法
    elapsed_time = time.time() - start_time

    if success and analyzer.results:
        print(f"\n⚡ 分析耗时: {elapsed_time:.2f} 秒")

        # 步骤3: 生成报告
        print(f"\n[步骤3] 生成分析报告")
        analyzer.generate_report()

        print("\n" + "=" * 60)
        print("          ✅ 分析完成！")
        print("=" * 60)
    else:
        print("\n分析失败")


if __name__ == "__main__":
    main()