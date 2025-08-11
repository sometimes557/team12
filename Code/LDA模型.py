# -*- coding: utf-8 -*-
"""
LDA 主题模型分析：基于情感分类后的评论数据，挖掘正面/负面评论的核心话题
适配 gensim 新版本（移除 formatted 参数兼容问题）
"""

import pandas as pd
import numpy as np
import re
import itertools
import matplotlib.pyplot as plt
from gensim import corpora, models

# ---------------------------
# 1. 加载数据（情感分析后的正负样本）
# ---------------------------
posdata = pd.read_csv("../Data/posdata.csv", encoding='utf-8')
negdata = pd.read_csv("../Data/negdata.csv", encoding='utf-8')

# 检查数据是否为空
if posdata.empty or negdata.empty:
    raise ValueError("警告：posdata.csv 或 negdata.csv 为空！请检查数据预处理流程")


# ---------------------------
# 2. 构建词典与语料库（Gensim 格式）
# ---------------------------
def build_corpus_and_dict(data):
    """
    输入情感分类后的评论数据，构建 Gensim 词典和语料库
    """
    # 转换为 [['词1'], ['词2'], ...] 格式（Gensim 要求的嵌套列表）
    texts = [[word] for word in data['word']]
    # 构建词典（去重 + 编号）
    dictionary = corpora.Dictionary(texts)
    # 构建语料库（词袋模型：(词ID, 词频)）
    corpus = [dictionary.doc2bow(text) for text in texts]
    return dictionary, corpus


# 正面评论处理
pos_dict, pos_corpus = build_corpus_and_dict(posdata)
# 负面评论处理
neg_dict, neg_corpus = build_corpus_and_dict(negdata)


# ---------------------------
# 3. 主题数寻优（核心：最小化主题间相似度）
# ---------------------------
def cos(vector1, vector2):
    """余弦相似度计算（用于衡量主题间区分度）"""
    dot_product = sum(a * b for a, b in zip(vector1, vector2))
    normA = np.sqrt(sum(a ** 2 for a in vector1))
    normB = np.sqrt(sum(b ** 2 for b in vector2))
    if normA == 0 or normB == 0:
        return None  # 避免除以 0
    return dot_product / (normA * normB)


def lda_topic_search(corpus, dictionary):
    """
    遍历主题数 2-10，计算主题间平均余弦相似度
    返回：各主题数对应的平均相似度（越小说明主题区分度越好）
    """
    mean_similarity = [1]  # 主题数=1 时无意义，手动填充

    for num_topics in range(2, 11):
        lda = models.LdaModel(
            corpus,
            num_topics=num_topics,
            id2word=dictionary,
            passes=10,
            random_state=42
        )

        # 提取每个主题的前 50 个关键词（适配新版本，不使用 formatted 参数）
        topics = lda.show_topics(num_words=50, formatted=False)
        # 解析关键词（只保留词，去除权重）
        top_words = []
        for topic in topics:
            words = [word for word, _ in topic[1]]  # topic[1] 是 (词, 权重) 列表
            top_words.append(words)

        # 构建词频向量（用于计算主题相似度）
        all_words = list(set(sum(top_words, [])))  # 所有主题的关键词去重
        topic_vectors = []
        for words in top_words:
            # 统计每个关键词在当前主题中的出现次数
            vector = [words.count(word) for word in all_words]
            topic_vectors.append(vector)

        # 计算所有主题对的余弦相似度
        similarities = []
        # 遍历所有主题对 (i,j) 且 i<j
        for i in range(num_topics):
            for j in range(i + 1, num_topics):
                sim = cos(topic_vectors[i], topic_vectors[j])
                if sim is not None:
                    similarities.append(sim)

        # 计算平均相似度（值越小，主题区分度越好）
        mean_sim = np.mean(similarities) if similarities else 0
        mean_similarity.append(mean_sim)

    return mean_similarity


# 正面评论主题数寻优
pos_k = lda_topic_search(pos_corpus, pos_dict)
# 负面评论主题数寻优
neg_k = lda_topic_search(neg_corpus, neg_dict)

# ---------------------------
# 4. 可视化主题数寻优结果
# ---------------------------
plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# 正面评论可视化
ax1.plot(range(1, 11), pos_k, marker='o', color='royalblue')
ax1.set_title('正面评论 - 主题数 vs 平均余弦相似度', fontsize=14)
ax1.set_xlabel('主题数', fontsize=12)
ax1.set_ylabel('平均余弦相似度', fontsize=12)
ax1.grid(alpha=0.3)

# 负面评论可视化
ax2.plot(range(1, 11), neg_k, marker='o', color='crimson')
ax2.set_title('负面评论 - 主题数 vs 平均余弦相似度', fontsize=14)
ax2.set_xlabel('主题数', fontsize=12)
ax2.set_ylabel('平均余弦相似度', fontsize=12)
ax2.grid(alpha=0.3)

plt.tight_layout()
# 保存可视化结果（可在 Data 文件夹查看）
plt.savefig('../Data/lda_topic_search.png', dpi=300, bbox_inches='tight')
plt.show()  # 弹出窗口显示


# ---------------------------
# 5. 训练最终 LDA 模型（基于最优主题数，根据曲线调整）
# ---------------------------
def train_lda(corpus, dictionary, num_topics=2):  # 已根据你的曲线改为 2
    """训练 LDA 模型并返回结果"""
    lda = models.LdaModel(
        corpus,
        num_topics=num_topics,
        id2word=dictionary,
        passes=20,  # 增加训练轮数提升稳定性
        random_state=42
    )
    return lda


# 训练模型（主题数根据可视化结果调整，这里用 2）
pos_lda = train_lda(pos_corpus, pos_dict, num_topics=2)
neg_lda = train_lda(neg_corpus, neg_dict, num_topics=2)


# ---------------------------
# 6. 输出主题关键词（适配 gensim 新版本，移除 formatted 参数）
# ---------------------------
def print_topics(lda_model, model_type='正面'):
    """格式化打印 LDA 主题关键词（适配 gensim 新版本）"""
    print(f"\n===== {model_type}评论 LDA 主题分析结果 =====")
    # 新版本 print_topics 无 formatted 参数，返回 (主题ID, "关键词1 权重1 + ...")
    topics = lda_model.print_topics(num_words=10)
    for topic_id, topic_str in topics:
        # 用正则提取关键词和权重（格式："词1"*0.123 + "词2"*0.456...）
        keywords = re.findall(r'"(.*?)"\s*\*([\d.]+)', topic_str)
        # 格式化输出：词(权重) + 词(权重)
        formatted_keywords = " + ".join([f"{word}({float(weight):.4f})" for word, weight in keywords])
        print(f"主题 {topic_id}: {formatted_keywords}")


# 打印结果到控制台
print_topics(pos_lda, model_type='正面')
print_topics(neg_lda, model_type='负面')


# ---------------------------
# 7. 保存主题结果到文件（方便后续分析）
# ---------------------------
def save_topics_to_csv(lda_model, model_type, save_path='../Data'):
    """将主题关键词保存为 CSV 文件"""
    topics = lda_model.print_topics(num_words=10)
    data = []
    for topic_id, topic_str in topics:
        # 提取关键词列表（只保留词，去除权重）
        keywords = re.findall(r'"(.*?)"', topic_str)
        data.append([topic_id, ", ".join(keywords)])

    df = pd.DataFrame(data, columns=['主题ID', '关键词列表'])
    df.to_csv(f"{save_path}/{model_type}_lda_topics.csv",
              index=False,
              encoding='utf-8')


# 保存结果
save_topics_to_csv(pos_lda, '正面')
save_topics_to_csv(neg_lda, '负面')

# ---------------------------
# 8. 可选：交互式可视化（需安装 pyLDAvis）
# ---------------------------
try:
    import pyLDAvis.gensim_models as gensimvis
    import pyLDAvis

    # 正面评论可视化
    vis_pos = gensimvis.prepare(pos_lda, pos_corpus, pos_dict)
    pyLDAvis.save_html(vis_pos, '../Data/lda_vis_pos.html')
    print("\n提示：正面评论交互式可视化已保存为 lda_vis_pos.html（浏览器打开查看）")

    # 负面评论可视化
    vis_neg = gensimvis.prepare(neg_lda, neg_corpus, neg_dict)
    pyLDAvis.save_html(vis_neg, '../Data/lda_vis_neg.html')
    print("提示：负面评论交互式可视化已保存为 lda_vis_neg.html（浏览器打开查看）")

except ImportError:
    print("\n提示：未安装 pyLDAvis，跳过交互式可视化（可运行 `pip install pyLDAvis` 补充）")
except Exception as e:
    print(f"\n交互式可视化生成失败：{str(e)}")

