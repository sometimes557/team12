"""
亚马逊评论情感分析系统 - 修复版
修复中性评论识别和可视化重叠问题
"""

import os
import json
import pandas as pd
import numpy as np
from openai import OpenAI
import time
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import jieba
import re
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ==================== 配置区域 ====================
# 设置字体，避免显示问题
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# API配置
USE_API = False  # True: 使用 DeepSeek API, False: 使用本地分析
DEEPSEEK_API_KEY = "sk-a7dbc3801c44491c9081462edd4104fa"


class EnhancedSentimentAnalyzer:
    """增强版情感分析器 - 简化版"""

    def __init__(self):
        """初始化情感词典"""
        # 正面词汇
        self.positive_words = set([
            'excellent', 'perfect', 'amazing', 'fantastic', 'wonderful', 'awesome',
            'outstanding', 'superb', 'exceptional', 'brilliant', 'magnificent',
            'great', 'good', 'nice', 'well', 'better', 'best', 'quality',
            'worth', 'value', 'works', 'working', 'functional', 'effective',
            'fast', 'easy', 'simple', 'convenient', 'comfortable', 'useful',
            'love', 'loved', 'like', 'liked', 'enjoy', 'satisfied', 'pleased',
            'happy', 'recommend', 'recommended', 'beautiful', 'pretty'
        ])

        # 负面词汇
        self.negative_words = set([
            'terrible', 'horrible', 'awful', 'worst', 'disgusting', 'hate',
            'bad', 'poor', 'inferior', 'weak', 'wrong', 'useless', 'worthless',
            'broken', 'damaged', 'defective', 'faulty', 'cheap', 'junk',
            'failed', 'failure', 'fail', 'malfunction', 'unreliable', 'slow',
            'disappointed', 'disappointing', 'dissatisfied', 'unhappy', 'frustrated',
            'waste', 'wasted', 'fake', 'scam', 'return', 'returned', 'refund'
        ])

        # 中性词汇
        self.neutral_words = set([
            'okay', 'ok', 'fine', 'average', 'normal', 'standard', 'acceptable',
            'adequate', 'fair', 'moderate', 'reasonable', 'decent', 'satisfactory',
            'alright', 'so-so', 'ordinary', 'typical', 'regular', 'expected'
        ])

        # 否定词
        self.negation_words = set([
            'not', 'no', 'never', 'neither', 'nor', 'cannot', "can't",
            "won't", "doesn't", "didn't", "isn't", "aren't", "wasn't"
        ])

    def analyze(self, text, rating=None):
        """
        分析单条评论的情感 - 简化版

        Args:
            text: 评论文本
            rating: 星级评分 (1-5)
        """
        if pd.isna(text) or str(text).strip() == '':
            return 'neutral', 0.5

        text = str(text).lower()
        words = text.split()

        # 初始化分数
        positive_score = 0
        negative_score = 0
        neutral_score = 0

        # 基于评分的初始偏向
        if rating is not None and not pd.isna(rating):
            rating = float(rating)
            if rating <= 2:
                negative_score += 3
            elif rating == 3:
                neutral_score += 5  # 3星强烈暗示中性
            elif rating >= 4:
                positive_score += 2

        # 统计情感词
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word)
            if word_clean in self.positive_words:
                positive_score += 1
            elif word_clean in self.negative_words:
                negative_score += 1
            elif word_clean in self.neutral_words:
                neutral_score += 1

        # 检查中性短语
        neutral_phrases = ['not bad', 'not great', 'just okay', 'nothing special',
                           'as expected', 'its okay', 'its fine', 'could be better']

        text_lower = text.lower()
        for phrase in neutral_phrases:
            if phrase in text_lower:
                neutral_score += 2

        # 特殊短语检测
        if 'highly recommend' in text_lower or 'definitely recommend' in text_lower:
            positive_score += 3
        if 'do not recommend' in text_lower or "don't recommend" in text_lower:
            negative_score += 3
        if 'waste of money' in text_lower or 'terrible quality' in text_lower:
            negative_score += 2

        # 决定情感
        total_score = positive_score + negative_score + neutral_score

        # 如果没有明显情感词
        if total_score == 0:
            if rating == 3:
                return 'neutral', 0.7
            elif rating <= 2:
                return 'negative', 0.6
            elif rating >= 4:
                return 'positive', 0.6
            else:
                return 'neutral', 0.5

        # 计算各情感比例
        pos_ratio = positive_score / total_score
        neg_ratio = negative_score / total_score
        neu_ratio = neutral_score / total_score

        # 判断逻辑 - 更加平衡
        # 1. 如果中性分数最高或者3星评论
        if rating == 3 and neutral_score >= max(positive_score, negative_score) * 0.5:
            return 'neutral', 0.7 + neu_ratio * 0.2

        # 2. 如果中性词占主导
        if neu_ratio > 0.4 or neutral_score > max(positive_score, negative_score):
            return 'neutral', 0.6 + neu_ratio * 0.3

        # 3. 如果正负面接近（混合情感）
        if positive_score > 0 and negative_score > 0:
            diff = abs(positive_score - negative_score)
            if diff <= 2:
                return 'neutral', 0.65

        # 4. 基于评分的判断
        if rating is not None:
            if rating <= 2:
                if negative_score >= positive_score:
                    return 'negative', 0.7 + neg_ratio * 0.2
                elif positive_score > negative_score * 2:
                    return 'neutral', 0.6  # 评分低但文本正面，可能是中性
                else:
                    return 'neutral', 0.55
            elif rating >= 4:
                if positive_score >= negative_score:
                    return 'positive', 0.7 + pos_ratio * 0.2
                elif negative_score > positive_score * 2:
                    return 'neutral', 0.6  # 评分高但文本负面，可能是中性
                else:
                    return 'neutral', 0.55

        # 5. 基于文本的最终判断
        if positive_score > negative_score + 2:
            return 'positive', 0.6 + pos_ratio * 0.3
        elif negative_score > positive_score + 2:
            return 'negative', 0.6 + neg_ratio * 0.3
        else:
            return 'neutral', 0.6


class AmazonReviewAnalyzer:
    """亚马逊评论分析主类"""

    def __init__(self, use_api=False, api_key=None):
        """初始化分析器"""
        self.use_api = use_api
        self.api_key = api_key
        self.client = None
        self.local_analyzer = EnhancedSentimentAnalyzer()

        if self.use_api and self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com"
                )
                print("✅ DeepSeek API 连接成功")
            except Exception as e:
                print(f"❌ DeepSeek API 连接失败: {e}")
                print("⚠️ 自动切换到本地分析模式")
                self.use_api = False

    def analyze_sentiment_api(self, text, rating=None):
        """使用API分析情感"""
        if not self.client:
            return self.analyze_sentiment_local(text, rating)

        try:
            text_truncated = text[:500] if len(text) > 500 else text
            prompt = f"Analyze this Amazon review sentiment"
            if rating is not None:
                prompt += f" (Rating: {rating}/5 stars)"
            prompt += f": {text_truncated}"

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze sentiment. Return ONLY: positive, negative, or neutral. Consider rating: 3 stars often means neutral."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
                timeout=10
            )

            result = response.choices[0].message.content.strip().lower()
            if 'positive' in result:
                return 'positive', 0.9
            elif 'negative' in result:
                return 'negative', 0.9
            else:
                return 'neutral', 0.7

        except Exception as e:
            return self.analyze_sentiment_local(text, rating)

    def analyze_sentiment_local(self, text, rating=None):
        """使用本地分析器分析情感"""
        return self.local_analyzer.analyze(text, rating)

    def analyze_sentiment(self, text, rating=None):
        """统一的情感分析接口"""
        if self.use_api and self.client:
            return self.analyze_sentiment_api(text, rating)
        else:
            return self.analyze_sentiment_local(text, rating)

    def process_file(self, file_path):
        """处理单个文件"""
        reviews = []

        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
            review_cols = ['review', 'body', 'text', 'comment', 'content']
            title_cols = ['title', 'subject', 'heading']

            review_col = None
            title_col = None

            for col in review_cols:
                if col in df.columns:
                    review_col = col
                    break

            for col in title_cols:
                if col in df.columns:
                    title_col = col
                    break

            if review_col:
                for idx, row in df.iterrows():
                    content = str(row[review_col]) if pd.notna(row[review_col]) else ''
                    if title_col and pd.notna(row[title_col]):
                        content = str(row[title_col]) + ' ' + content

                    if content.strip():
                        reviews.append({
                            'filename': os.path.basename(file_path),
                            'content': content,
                            'rating': row.get('rating', None),
                            'username': row.get('username', 'Unknown'),
                            'product_id': row.get('product_id', 'Unknown'),
                            'product_title': row.get('product_title', 'Unknown Product')
                        })

        return reviews

    def analyze_reviews(self, input_source='reviews'):
        """分析评论"""
        reviews = []

        if os.path.isfile(input_source):
            print(f"📖 读取文件: {input_source}")
            reviews = self.process_file(input_source)
        else:
            print(f"❌ 找不到输入源: {input_source}")
            return None

        if not reviews:
            print("❌ 没有找到有效的评论数据")
            return None

        print(f"✅ 成功读取 {len(reviews)} 条评论")

        # 统计评分分布
        ratings = [r.get('rating') for r in reviews if r.get('rating') is not None]
        if ratings:
            print(f"\n📊 评分分布:")
            for star in range(1, 6):
                count = sum(1 for r in ratings if r == star)
                if count > 0:
                    print(f"   {star}星: {count} 条 ({count / len(ratings) * 100:.1f}%)")

        # 分析情感
        print(f"\n🔍 开始情感分析...")
        print(f"   模式: {'🚀 DeepSeek API' if (self.use_api and self.client) else '💻 本地分析'}")

        results = []
        total = len(reviews)
        sentiment_counter = {'positive': 0, 'negative': 0, 'neutral': 0}

        for idx, review in enumerate(reviews):
            sentiment, confidence = self.analyze_sentiment(
                review['content'],
                review.get('rating')
            )

            sentiment_counter[sentiment] += 1

            result = {
                'filename': review['filename'],
                'content': review['content'][:200] + '...' if len(review['content']) > 200 else review['content'],
                'full_content': review['content'],
                'sentiment': sentiment,
                'confidence': confidence,
                'rating': review.get('rating'),
                'username': review.get('username', 'Unknown'),
                'product_id': review.get('product_id', 'Unknown'),
                'product_title': review.get('product_title', 'Unknown Product')
            }
            results.append(result)

            if (idx + 1) % 10 == 0 or (idx + 1) == total:
                progress = (idx + 1) / total * 100
                print(f"   进度: {idx + 1}/{total} ({progress:.1f}%) - "
                      f"正面: {sentiment_counter['positive']}, "
                      f"负面: {sentiment_counter['negative']}, "
                      f"中性: {sentiment_counter['neutral']}")

            if self.use_api and self.client and idx < total - 1:
                time.sleep(0.1)

        print("✅ 分析完成！")

        print(f"\n📊 最终统计:")
        print(f"   正面评论: {sentiment_counter['positive']} ({sentiment_counter['positive'] / total * 100:.1f}%)")
        print(f"   负面评论: {sentiment_counter['negative']} ({sentiment_counter['negative'] / total * 100:.1f}%)")
        print(f"   中性评论: {sentiment_counter['neutral']} ({sentiment_counter['neutral'] / total * 100:.1f}%)")

        df = pd.DataFrame(results)
        return df

    def generate_report(self, df):
        """生成分析报告"""
        if df is None or len(df) == 0:
            print("❌ 没有数据可以生成报告")
            return

        print("\n📊 生成分析报告...")

        if not os.path.exists('analysis_results'):
            os.makedirs('analysis_results')

        total = len(df)
        sentiment_counts = df['sentiment'].value_counts()

        # 生成文本报告
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(" " * 25 + "Amazon Review Sentiment Analysis Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Reviews: {total}")
        report_lines.append("")

        # 1. 情感分布
        report_lines.append("[Sentiment Distribution]")
        report_lines.append("-" * 40)

        for sentiment in ['positive', 'negative', 'neutral']:
            if sentiment in sentiment_counts.index:
                count = sentiment_counts[sentiment]
                percentage = count / total * 100
                emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐'}[sentiment]
                bar = '█' * int(percentage / 2)
                report_lines.append(
                    f"{emoji} {sentiment.capitalize():8s}: {count:4d} reviews ({percentage:6.2f}%) {bar}")

        # 2. 星级统计（如果有评分数据）
        if 'rating' in df.columns and df['rating'].notna().any():
            report_lines.append("")
            report_lines.append("[Rating Statistics]")
            report_lines.append("-" * 40)
            report_lines.append(f"Average Rating: {df['rating'].mean():.2f} / 5.0")
            report_lines.append(f"Median Rating: {df['rating'].median():.1f}")
            report_lines.append(f"Standard Deviation: {df['rating'].std():.2f}")

            # 评分分布详细统计
            report_lines.append("")
            report_lines.append("Rating Distribution:")
            for star in range(5, 0, -1):  # 从5星到1星
                star_count = len(df[df['rating'] == star])
                if star_count > 0:
                    star_percentage = star_count / total * 100
                    stars_display = '★' * star + '☆' * (5 - star)
                    bar = '█' * int(star_percentage / 2)
                    report_lines.append(f"  {stars_display}: {star_count:4d} ({star_percentage:5.1f}%) {bar}")

            # 星级与情感的交叉分析
            report_lines.append("")
            report_lines.append("[Rating-Sentiment Cross Analysis]")
            report_lines.append("-" * 40)

            for star in range(5, 0, -1):
                star_df = df[df['rating'] == star]
                if len(star_df) > 0:
                    star_sentiments = star_df['sentiment'].value_counts()
                    report_lines.append(f"{star}★ Reviews ({len(star_df)} total):")
                    for sentiment in ['positive', 'negative', 'neutral']:
                        if sentiment in star_sentiments.index:
                            count = star_sentiments[sentiment]
                            pct = count / len(star_df) * 100
                            report_lines.append(f"    {sentiment:8s}: {count:3d} ({pct:5.1f}%)")

        # 3. 高频词分析
        report_lines.append("")
        report_lines.append("[High Frequency Words Analysis]")
        report_lines.append("-" * 40)

        # 停用词列表
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'have', 'from',
            'will', 'your', 'more', 'been', 'what', 'were', 'there', 'their',
            'would', 'could', 'very', 'been', 'have', 'also', 'just', 'only',
            'other', 'after', 'before', 'some', 'when', 'which', 'where',
            'these', 'those', 'then', 'than', 'both', 'each', 'they', 'them',
            'was', 'are', 'has', 'had', 'but', 'not', 'can', 'did', 'does'
        }

        # 分析整体高频词
        all_text = ' '.join(df['full_content'].astype(str))
        all_words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        all_filtered = [w for w in all_words if w not in stop_words]
        all_freq = Counter(all_filtered).most_common(15)

        report_lines.append("Overall Top 15 Words:")
        for i, (word, count) in enumerate(all_freq, 1):
            report_lines.append(f"  {i:2d}. {word:15s} ({count:4d} times)")

        # 分别分析各情感类别的高频词
        report_lines.append("")
        report_lines.append("Top Words by Sentiment:")

        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_reviews = df[df['sentiment'] == sentiment]['full_content'].astype(str)
            if len(sentiment_reviews) > 0:
                sentiment_text = ' '.join(sentiment_reviews)
                sentiment_words = re.findall(r'\b[a-zA-Z]{3,}\b', sentiment_text.lower())
                sentiment_filtered = [w for w in sentiment_words if w not in stop_words]
                sentiment_freq = Counter(sentiment_filtered).most_common(10)

                emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐'}[sentiment]
                report_lines.append(f"\n{emoji} {sentiment.capitalize()} Reviews:")
                for i, (word, count) in enumerate(sentiment_freq[:5], 1):
                    report_lines.append(f"    {i}. {word:15s} ({count:3d} times)")

        # 4. 关键短语分析
        report_lines.append("")
        report_lines.append("[Key Phrases Analysis]")
        report_lines.append("-" * 40)

        # 提取2-3词的短语
        def extract_phrases(text, n=2):
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            phrases = []
            for i in range(len(words) - n + 1):
                phrase_words = words[i:i + n]
                if not any(w in stop_words for w in phrase_words):
                    phrases.append(' '.join(phrase_words))
            return phrases

        # 分析正面评论的关键短语
        positive_text = ' '.join(df[df['sentiment'] == 'positive']['full_content'].astype(str))
        if positive_text:
            pos_phrases = extract_phrases(positive_text, 2)
            pos_phrase_freq = Counter(pos_phrases).most_common(5)
            report_lines.append("Positive Review Key Phrases:")
            for phrase, count in pos_phrase_freq:
                if count > 2:  # 只显示出现3次以上的短语
                    report_lines.append(f"  • \"{phrase}\" ({count} times)")

        # 分析负面评论的关键短语
        negative_text = ' '.join(df[df['sentiment'] == 'negative']['full_content'].astype(str))
        if negative_text:
            neg_phrases = extract_phrases(negative_text, 2)
            neg_phrase_freq = Counter(neg_phrases).most_common(5)
            report_lines.append("\nNegative Review Key Phrases:")
            for phrase, count in neg_phrase_freq:
                if count > 2:
                    report_lines.append(f"  • \"{phrase}\" ({count} times)")

        # 5. 置信度统计
        report_lines.append("")
        report_lines.append("[Analysis Confidence Statistics]")
        report_lines.append("-" * 40)
        report_lines.append(f"Average Confidence: {df['confidence'].mean():.2%}")
        report_lines.append(
            f"High Confidence (>80%): {len(df[df['confidence'] > 0.8]):4d} reviews ({len(df[df['confidence'] > 0.8]) / total * 100:.1f}%)")
        report_lines.append(
            f"Medium Confidence (50-80%): {len(df[(df['confidence'] >= 0.5) & (df['confidence'] <= 0.8)]):4d} reviews ({len(df[(df['confidence'] >= 0.5) & (df['confidence'] <= 0.8)]) / total * 100:.1f}%)")
        report_lines.append(
            f"Low Confidence (<50%): {len(df[df['confidence'] < 0.5]):4d} reviews ({len(df[df['confidence'] < 0.5]) / total * 100:.1f}%)")

        # 6. 典型评论示例
        report_lines.append("")
        report_lines.append("[Representative Review Examples]")
        report_lines.append("-" * 40)

        # 最正面的评论
        if len(df[df['sentiment'] == 'positive']) > 0:
            best_review = df[df['sentiment'] == 'positive'].nlargest(1, 'confidence').iloc[0]
            report_lines.append("Most Confident Positive Review:")
            if pd.notna(best_review['rating']):
                report_lines.append(
                    f"  Rating: {'★' * int(best_review['rating']) + '☆' * (5 - int(best_review['rating']))}")
            report_lines.append(f"  Confidence: {best_review['confidence']:.2%}")
            report_lines.append(f"  Content: \"{best_review['content'][:200]}...\"" if len(
                best_review['content']) > 200 else f"  Content: \"{best_review['content']}\"")

        # 最负面的评论
        if len(df[df['sentiment'] == 'negative']) > 0:
            worst_review = df[df['sentiment'] == 'negative'].nlargest(1, 'confidence').iloc[0]
            report_lines.append("")
            report_lines.append("Most Confident Negative Review:")
            if pd.notna(worst_review['rating']):
                report_lines.append(
                    f"  Rating: {'★' * int(worst_review['rating']) + '☆' * (5 - int(worst_review['rating']))}")
            report_lines.append(f"  Confidence: {worst_review['confidence']:.2%}")
            report_lines.append(f"  Content: \"{worst_review['content'][:200]}...\"" if len(
                worst_review['content']) > 200 else f"  Content: \"{worst_review['content']}\"")

        # 典型中性评论
        if len(df[df['sentiment'] == 'neutral']) > 0:
            neutral_review = df[df['sentiment'] == 'neutral'].nlargest(1, 'confidence').iloc[0]
            report_lines.append("")
            report_lines.append("Most Confident Neutral Review:")
            if pd.notna(neutral_review['rating']):
                report_lines.append(
                    f"  Rating: {'★' * int(neutral_review['rating']) + '☆' * (5 - int(neutral_review['rating']))}")
            report_lines.append(f"  Confidence: {neutral_review['confidence']:.2%}")
            report_lines.append(f"  Content: \"{neutral_review['content'][:200]}...\"" if len(
                neutral_review['content']) > 200 else f"  Content: \"{neutral_review['content']}\"")

        # 7. 分析洞察
        report_lines.append("")
        report_lines.append("[Analysis Insights]")
        report_lines.append("-" * 40)

        # 计算各种指标
        pos_ratio = sentiment_counts.get('positive', 0) / total * 100
        neg_ratio = sentiment_counts.get('negative', 0) / total * 100
        neu_ratio = sentiment_counts.get('neutral', 0) / total * 100

        if 'rating' in df.columns and df['rating'].notna().any():
            avg_rating = df['rating'].mean()

            # 评分与情感一致性分析
            low_rating_positive = len(df[(df['rating'] <= 2) & (df['sentiment'] == 'positive')])
            high_rating_negative = len(df[(df['rating'] >= 4) & (df['sentiment'] == 'negative')])
            consistency_issues = low_rating_positive + high_rating_negative

            if consistency_issues > 0:
                report_lines.append(f"⚠️ Found {consistency_issues} reviews with sentiment-rating mismatch")
                if low_rating_positive > 0:
                    report_lines.append(f"   - {low_rating_positive} low-rating reviews classified as positive")
                if high_rating_negative > 0:
                    report_lines.append(f"   - {high_rating_negative} high-rating reviews classified as negative")
            else:
                report_lines.append("✅ Sentiment analysis shows good consistency with ratings")

            # 产品评价总结
            report_lines.append("")
            if avg_rating >= 4.5 and pos_ratio > 70:
                report_lines.append(
                    "🌟 Excellent Product Performance: High ratings with predominantly positive sentiment")
            elif avg_rating >= 4.0 and pos_ratio > 60:
                report_lines.append("✅ Good Product Performance: Solid ratings with mostly positive feedback")
            elif avg_rating >= 3.5 and neu_ratio > 30:
                report_lines.append("⚡ Moderate Product Performance: Mixed feedback with significant neutral sentiment")
            elif avg_rating < 3.0 or neg_ratio > 40:
                report_lines.append("⚠️ Product Needs Improvement: Low ratings or high negative sentiment detected")
            else:
                report_lines.append("📊 Average Product Performance: Balanced feedback across sentiments")

        # 保存文本报告
        with open('analysis_results/analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print("✅ 文本报告已保存")

        # 保存详细数据
        df.to_csv('analysis_results/detailed_results.csv', index=False, encoding='utf-8-sig')
        print("✅ 详细数据已保存")

        # 生成高频词统计表（额外的CSV文件）
        word_stats = []
        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_reviews = df[df['sentiment'] == sentiment]['full_content'].astype(str)
            if len(sentiment_reviews) > 0:
                sentiment_text = ' '.join(sentiment_reviews)
                sentiment_words = re.findall(r'\b[a-zA-Z]{3,}\b', sentiment_text.lower())
                sentiment_filtered = [w for w in sentiment_words if w not in stop_words]
                sentiment_freq = Counter(sentiment_filtered).most_common(20)

                for word, count in sentiment_freq:
                    word_stats.append({
                        'sentiment': sentiment,
                        'word': word,
                        'frequency': count,
                        'percentage': count / len(sentiment_filtered) * 100 if sentiment_filtered else 0
                    })

        if word_stats:
            word_df = pd.DataFrame(word_stats)
            word_df.to_csv('analysis_results/word_frequency_analysis.csv', index=False, encoding='utf-8-sig')
            print("✅ 词频分析表已保存")

        self.create_visualizations(df, sentiment_counts)
        print("\n📁 所有结果已保存到 'analysis_results' 文件夹")

        # 打印报告摘要
        print("\n" + "=" * 60)
        print("Report Summary")
        print("=" * 60)
        for line in report_lines[:50]:  # 打印前50行作为摘要
            print(line)

    def create_visualizations(self, df, sentiment_counts):
        """创建可视化图表 - 增强版with高频词和星级统计"""
        print("📈 生成可视化图表...")

        sns.set_style("whitegrid")
        colors = {'positive': '#2ecc71', 'negative': '#e74c3c', 'neutral': '#95a5a6'}

        # 停用词列表
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'have', 'from',
            'will', 'your', 'more', 'been', 'what', 'were', 'there', 'their',
            'would', 'could', 'very', 'been', 'have', 'also', 'just', 'only',
            'other', 'after', 'before', 'some', 'when', 'which', 'where',
            'these', 'those', 'then', 'than', 'both', 'each', 'they', 'them',
            'was', 'are', 'has', 'had', 'but', 'not', 'can', 'did', 'does'
        }

        # 1. 情感分布饼图和评分分布
        fig1, axes = plt.subplots(1, 2, figsize=(14, 6))

        # 饼图
        ax1 = axes[0]
        plot_colors = [colors.get(s, '#333') for s in sentiment_counts.index]
        wedges, texts, autotexts = ax1.pie(
            sentiment_counts.values,
            labels=sentiment_counts.index,
            colors=plot_colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85
        )

        # 调整标签位置避免重叠
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')

        ax1.set_title('Sentiment Distribution', fontsize=12, fontweight='bold', pad=20)

        # 2. 评分分布
        if 'rating' in df.columns and df['rating'].notna().any():
            ax2 = axes[1]
            rating_counts = df['rating'].value_counts().sort_index()
            bars = ax2.bar(rating_counts.index, rating_counts.values,
                           color=['#e74c3c', '#f39c12', '#f1c40f', '#3498db', '#2ecc71'],
                           width=0.6)
            ax2.set_xlabel('Rating (Stars)', fontsize=10)
            ax2.set_ylabel('Count', fontsize=10)
            ax2.set_title('Rating Distribution', fontsize=12, fontweight='bold', pad=20)
            ax2.set_xticks([1, 2, 3, 4, 5])

            # 添加数值标签，调整位置
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2., height + rating_counts.max() * 0.01,
                         f'{int(height)}', ha='center', va='bottom', fontsize=9)

            ax2.set_ylim(0, rating_counts.max() * 1.1)  # 留出空间给标签

        plt.tight_layout()
        plt.savefig('analysis_results/distributions.png', dpi=150, bbox_inches='tight')
        plt.close(fig1)

        # 3. 情感与评分的关系图
        if 'rating' in df.columns and df['rating'].notna().any():
            fig2, axes = plt.subplots(1, 2, figsize=(14, 6))

            # 堆叠柱状图
            ax1 = axes[0]
            rating_sentiment = pd.crosstab(df['rating'], df['sentiment'])
            rating_sentiment.plot(kind='bar', stacked=True,
                                  color=[colors.get(col, '#333') for col in rating_sentiment.columns],
                                  ax=ax1, width=0.7)
            ax1.set_xlabel('Rating (Stars)', fontsize=10)
            ax1.set_ylabel('Count', fontsize=10)
            ax1.set_title('Sentiment by Rating', fontsize=12, fontweight='bold', pad=20)
            ax1.legend(title='Sentiment', loc='upper left', fontsize=9, framealpha=0.9)
            ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)

            # 平均评分图
            ax2 = axes[1]
            sentiment_rating = df.groupby('sentiment')['rating'].mean().sort_values()
            bars = ax2.bar(range(len(sentiment_rating)), sentiment_rating.values,
                           color=[colors.get(s, '#333') for s in sentiment_rating.index],
                           width=0.6)
            ax2.set_xlabel('Sentiment', fontsize=10)
            ax2.set_ylabel('Average Rating', fontsize=10)
            ax2.set_title('Average Rating by Sentiment', fontsize=12, fontweight='bold', pad=20)
            ax2.set_ylim(0, 5.5)
            ax2.set_xticks(range(len(sentiment_rating)))
            ax2.set_xticklabels(sentiment_rating.index)

            # 添加数值标签
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                         f'{height:.2f}', ha='center', va='bottom', fontsize=10)

            plt.tight_layout()
            plt.savefig('analysis_results/sentiment_rating_analysis.png', dpi=150, bbox_inches='tight')
            plt.close(fig2)

        # 4. 词云
        fig3, axes = plt.subplots(1, 2, figsize=(14, 6))

        # 正面词云
        ax1 = axes[0]
        positive_text = ' '.join(df[df['sentiment'] == 'positive']['full_content'].astype(str))
        if positive_text:
            try:
                wordcloud_pos = WordCloud(
                    width=600, height=400,
                    background_color='white',
                    colormap='Greens',
                    max_words=30,
                    relative_scaling=0.5,
                    min_font_size=10
                ).generate(positive_text)
                ax1.imshow(wordcloud_pos, interpolation='bilinear')
                ax1.axis('off')
                ax1.set_title('Positive Reviews Word Cloud', fontsize=12, fontweight='bold', y=1.02)
            except:
                ax1.text(0.5, 0.5, 'Word cloud generation failed', ha='center', va='center')
                ax1.axis('off')

        # 负面词云
        ax2 = axes[1]
        negative_text = ' '.join(df[df['sentiment'] == 'negative']['full_content'].astype(str))
        if negative_text:
            try:
                wordcloud_neg = WordCloud(
                    width=600, height=400,
                    background_color='white',
                    colormap='Reds',
                    max_words=30,
                    relative_scaling=0.5,
                    min_font_size=10
                ).generate(negative_text)
                ax2.imshow(wordcloud_neg, interpolation='bilinear')
                ax2.axis('off')
                ax2.set_title('Negative Reviews Word Cloud', fontsize=12, fontweight='bold', y=1.02)
            except:
                ax2.text(0.5, 0.5, 'Word cloud generation failed', ha='center', va='center')
                ax2.axis('off')

        plt.tight_layout()
        plt.savefig('analysis_results/word_clouds.png', dpi=150, bbox_inches='tight')
        plt.close(fig3)

        # 5. 新增：高频词对比图
        fig4, axes = plt.subplots(2, 2, figsize=(16, 10))

        all_text = ' '.join(df['full_content'].astype(str))
        all_words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        all_filtered = [w for w in all_words if w not in stop_words]

        # 子图1：整体高频词
        ax1 = axes[0, 0]
        overall_freq = Counter(all_filtered).most_common(10)
        if overall_freq:
            words, counts = zip(*overall_freq)
            y_pos = np.arange(len(words))
            ax1.barh(y_pos, counts, color='#3498db', alpha=0.8)
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(words, fontsize=9)
            ax1.set_xlabel('Frequency', fontsize=10)
            ax1.set_title('Top 10 Overall High Frequency Words', fontsize=11, fontweight='bold')
            ax1.invert_yaxis()

            # 添加数值标签
            for i, v in enumerate(counts):
                ax1.text(v + max(counts) * 0.01, i, str(v), va='center', fontsize=8)

        # 子图2：各情感类别高频词对比
        ax2 = axes[0, 1]
        sentiment_word_data = []
        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_reviews = df[df['sentiment'] == sentiment]['full_content'].astype(str)
            if len(sentiment_reviews) > 0:
                sentiment_text = ' '.join(sentiment_reviews)
                sentiment_words = re.findall(r'\b[a-zA-Z]{3,}\b', sentiment_text.lower())
                sentiment_filtered = [w for w in sentiment_words if w not in stop_words]
                sentiment_freq = Counter(sentiment_filtered).most_common(5)
                for word, count in sentiment_freq:
                    sentiment_word_data.append({
                        'word': word,
                        'sentiment': sentiment,
                        'count': count
                    })

        if sentiment_word_data:
            word_df = pd.DataFrame(sentiment_word_data)
            word_pivot = word_df.pivot_table(index='word', columns='sentiment', values='count', fill_value=0)
            word_pivot.plot(kind='barh', stacked=False, ax=ax2,
                            color=[colors.get(col, '#333') for col in word_pivot.columns])
            ax2.set_xlabel('Frequency', fontsize=10)
            ax2.set_title('Top Words Comparison by Sentiment', fontsize=11, fontweight='bold')
            ax2.legend(title='Sentiment', loc='best', fontsize=8)

        # 子图3：星级分布详细统计
        if 'rating' in df.columns and df['rating'].notna().any():
            ax3 = axes[1, 0]

            # 创建星级与情感的热力图数据
            rating_sentiment_matrix = pd.crosstab(df['rating'], df['sentiment'], normalize='index') * 100

            # 绘制热力图
            im = ax3.imshow(rating_sentiment_matrix.values, cmap='YlOrRd', aspect='auto')

            # 设置标签
            ax3.set_xticks(np.arange(len(rating_sentiment_matrix.columns)))
            ax3.set_yticks(np.arange(len(rating_sentiment_matrix.index)))
            ax3.set_xticklabels(rating_sentiment_matrix.columns)
            ax3.set_yticklabels([f'{int(r)}★' for r in rating_sentiment_matrix.index])
            ax3.set_xlabel('Sentiment', fontsize=10)
            ax3.set_ylabel('Rating', fontsize=10)
            ax3.set_title('Rating-Sentiment Heatmap (%)', fontsize=11, fontweight='bold')

            # 添加数值
            for i in range(len(rating_sentiment_matrix.index)):
                for j in range(len(rating_sentiment_matrix.columns)):
                    text = ax3.text(j, i, f'{rating_sentiment_matrix.values[i, j]:.1f}',
                                    ha="center", va="center", color="black", fontsize=9)

            # 添加颜色条
            plt.colorbar(im, ax=ax3, fraction=0.046, pad=0.04)

        # 子图4：关键短语频率
        ax4 = axes[1, 1]

        def extract_phrases(text, n=2):
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            phrases = []
            for i in range(len(words) - n + 1):
                phrase_words = words[i:i + n]
                if not any(w in stop_words for w in phrase_words):
                    phrases.append(' '.join(phrase_words))
            return phrases

        all_phrases = extract_phrases(all_text, 2)
        phrase_freq = Counter(all_phrases).most_common(10)

        if phrase_freq:
            phrases, counts = zip(*phrase_freq)
            # 只显示出现3次以上的短语
            filtered_phrases = [(p, c) for p, c in zip(phrases, counts) if c > 2]

            if filtered_phrases:
                phrases, counts = zip(*filtered_phrases)
                y_pos = np.arange(len(phrases))
                ax4.barh(y_pos, counts, color='#9b59b6', alpha=0.8)
                ax4.set_yticks(y_pos)
                ax4.set_yticklabels(phrases, fontsize=8)
                ax4.set_xlabel('Frequency', fontsize=10)
                ax4.set_title('Top Key Phrases (2-word combinations)', fontsize=11, fontweight='bold')
                ax4.invert_yaxis()

                # 添加数值标签
                for i, v in enumerate(counts):
                    ax4.text(v + max(counts) * 0.01, i, str(v), va='center', fontsize=8)

        plt.tight_layout()
        plt.savefig('analysis_results/advanced_analysis.png', dpi=150, bbox_inches='tight')
        plt.close(fig4)

        print("✅ 可视化图表已保存")


def main():
    """主程序"""
    print("=" * 60)
    print(" " * 15 + "Amazon Review Sentiment Analysis System")
    print("=" * 60)

    use_api = USE_API
    api_key = DEEPSEEK_API_KEY
    input_source = "amazon_reviews.csv"

    if not os.path.exists(input_source):
        print(f"\n❌ 文件 '{input_source}' 不存在")
        return

    analyzer = AmazonReviewAnalyzer(use_api=use_api, api_key=api_key)

    print(f"\n🚀 开始分析: {input_source}")
    df = analyzer.analyze_reviews(input_source)

    if df is not None and len(df) > 0:
        analyzer.generate_report(df)

        print("\n" + "=" * 60)
        print("🎉 分析完成!")
        print("=" * 60)

        sentiment_counts = df['sentiment'].value_counts()
        total = len(df)

        print("\n📊 分析摘要:")
        print("-" * 40)

        for sentiment in ['positive', 'negative', 'neutral']:
            if sentiment in sentiment_counts.index:
                count = sentiment_counts[sentiment]
                percentage = count / total * 100
                emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐'}[sentiment]
                print(f"  {emoji} {sentiment.capitalize():8s}: {count:4d} 条 ({percentage:6.2f}%)")

        if 'rating' in df.columns and df['rating'].notna().any():
            print(f"\n  ⭐ 平均评分: {df['rating'].mean():.2f}/5.0")

        print("\n📁 详细结果请查看 'analysis_results' 文件夹")
    else:
        print("\n❌ 分析失败")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback

        traceback.print_exc()

