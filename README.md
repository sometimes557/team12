# Amazon 评论分析系统

Amazon Review Analyzer 是一个基于 Flask 的端到端 Web 应用，旨在帮助用户**快速、稳定、可视化地**获取并分析 Amazon 商品评论。系统支持关键词搜索、多线程爬取、情感分析、交互式图表以及报告导出，适用于市场研究、竞品分析、用户洞察等多种场景。

---

## 目录
1. [核心功能](#核心功能)  
2. [技术架构](#技术架构)  
3. [快速开始](#快速开始)  
4. [使用指南](#使用指南)  
5. [项目结构](#项目结构)  
6. [二次开发](#二次开发)  
7. [合规声明](#合规声明)  
8. [许可证](#许可证)  
9. [联系方式](#联系方式)  

---

## 核心功能

| 模块 | 关键能力 | 技术亮点 |
|---|---|---|
| **智能产品搜索** | 关键词搜索、结果分页、产品卡片展示 | 自动提取 ASIN、标题、缩略图 |
| **多线程评论爬取** | 指定页数、断点续爬、异常重试 | 随机 UA、指数退避、限速保护 |
| **情感分析引擎** | 正面 / 负面 / 中性三分类 | 词典+评分的融合算法，置信度输出 |
| **交互式可视化** | 饼图、柱状图、词云、交叉热力图 | Chart.js + Matplotlib 双端渲染 |
| **报告管理** | CSV / PDF 一键导出、历史记录 | 自动生成文件名并归档 |

---

## 技术架构

### 后端
- **Web 框架**: Flask ≥ 2.0  
- **数据科学**: Pandas, NumPy, Seaborn  
- **爬虫**: Requests, BeautifulSoup4, tenacity（重试）  
- **并发**: threading + 队列，可扩展至 asyncio  
- **可视化**: Matplotlib, WordCloud, Jinja2 模板  

### 前端
- **UI 框架**: Bootstrap 5  
- **图表**: Chart.js  
- **交互**: 原生 JavaScript + Fetch API  
- **模板**: Jinja2（服务器端渲染）

---

## 快速开始

### 1. 环境要求
- Python 3.8+  
- 2 GB+ 可用内存（生成词云时）

### 2. 获取源码
```bash
git clone https://github.com/sometimes557/team12.git
cd team12
```

### 3. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 启动服务
```bash
python app.py
# 浏览器访问 http://127.0.0.1:5000
```

---

## 使用指南

### Step 1 搜索产品
1. 在首页输入关键词，例如：`wireless earphones`  
2. 选择页数（1–3 页）  
3. 点击「搜索产品」→ 结果以卡片形式呈现  

### Step 2 分析评论
1. 在产品卡片点击「分析评论」  
2. 选择评论页数（建议 ≤ 10 页）  
3. 系统自动爬取并生成情感报告  

### Step 3 查看与导出
- **可视化**：情感分布饼图、评分柱状图、词云  
- **导出**：CSV（原始数据）、PDF（完整报告）  
- **历史**：通过「历史记录」页随时回顾  

---

## 项目结构
```
amazon-review-analyzer/
├── app.py                 # 入口 & 路由
├── requirements.txt       # 依赖清单
├── README.md              # 本文档
├── data/
│   ├── products/          # 搜索缓存 (JSON)
│   └── reports/           # 分析报告 (CSV / PDF)
├── modules/
│   ├── ymx_get_id.py      # 产品搜索
│   ├── ymx_pac.py         # 评论爬取
│   └── analysis.py        # 情感分析
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── index.html
│   ├── search.html
│   ├── report.html
│   └── history.html
└── analysis_results/      # 词云等附加输出
```

---

## 二次开发

### 1. 情感分析优化
编辑 `modules/analysis.py`  
- 自定义词典：在 `sentiment_dict/` 目录添加行业词汇  
- 权重调节：修改 `SCORE_WEIGHT` 与 `LEXICON_WEIGHT`  

### 2. 爬虫策略
编辑 `modules/ymx_pac.py`  
- 调整 `MAX_WORKERS` 控制并发  
- 在 `headers_pool` 添加更多 UA 以降低封禁概率  

### 3. 前端定制
- 样式：覆盖 `static/css/custom.css`  
- 图表：在 `templates/report.html` 引入新的 Chart.js 配置  

---

## 合规声明
1. **仅用于教育与研究目的**，禁止大规模商业抓取。  
2. 请遵守 [Amazon Robots.txt](https://www.amazon.com/robots.txt) 及当地法律法规。  
3. 合理设置请求间隔（默认 ≥ 1 s），避免对 Amazon 服务造成压力。  

---

## 许可证
MIT License  
详见 [LICENSE](LICENSE) 文件。

---

## 联系方式
- **Issue Tracker**: https://github.com/sometimes557/team12  
- **Email**: example@example.com  
- **Discussions**: 欢迎提交 Pull Request 与 Issue 共同维护项目。

---
© 2025 Amazon Review Analyzer Contributors