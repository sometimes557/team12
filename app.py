# -*- coding: utf-8 -*-
"""
Amazon评论分析系统 - Flask应用
满足以下要求：
- Flask + Bootstrap5 + Chart.js
- 产品搜索、评论爬取、情感分析（复用 modules/analysis.py）、可视化展示
- 历史记录与报告详情页
- 深色/浅色主题切换、页面加载动画
- 结果导出 PDF/CSV（PDF基于reportlab，若环境无此库将自动回退下载HTML）
"""
import os
import io
import json
import shutil
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import pandas as pd

# 本地模块
from modules.ymx_get_id import search_amazon_products, save_to_csv
from modules.ymx_pac import scrape_amazon_reviews
from modules.analysis import AmazonReviewAnalyzer

# Flask 基础设置
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCT_DIR = os.path.join(DATA_DIR, "products")
REPORT_DIR = os.path.join(DATA_DIR, "reports")

# 确保目录存在
os.makedirs(PRODUCT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

def _safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()

def build_chart_payload(df: pd.DataFrame) -> dict:
    """将分析结果转为Chart.js可用的数据"""
    payload = {"has_rating": False}

    # 情感计数
    sentiment_counts = df["sentiment"].value_counts().reindex(["positive","negative","neutral"]).fillna(0).astype(int)
    payload["sentiment"] = {
        "labels": ["Positive","Negative","Neutral"],
        "data": [int(sentiment_counts.get("positive",0)), int(sentiment_counts.get("negative",0)), int(sentiment_counts.get("neutral",0))],
    }

    # 评分分布
    if "rating" in df.columns and df["rating"].notna().any():
        payload["has_rating"] = True
        rating_counts = df["rating"].value_counts().sort_index()
        payload["rating"] = {
            "labels": [str(int(i)) for i in rating_counts.index.tolist()],
            "data": [int(x) for x in rating_counts.values.tolist()],
        }

        # 评分-情感 交叉
        ctab = pd.crosstab(df["rating"], df["sentiment"]).reindex(index=[1,2,3,4,5], fill_value=0).fillna(0)
        payload["rating_sentiment"] = {
            "labels": [f"{i}★" for i in ctab.index.tolist()],
            "datasets": [
                {"label": "Positive", "data": ctab.get("positive", pd.Series([0]*len(ctab))).tolist()},
                {"label": "Negative", "data": ctab.get("negative", pd.Series([0]*len(ctab))).tolist()},
                {"label": "Neutral",  "data": ctab.get("neutral",  pd.Series([0]*len(ctab))).tolist()},
            ]
        }

    return payload

def _copy_analysis_outputs_to_report(report_path: str):
    """如果 modules/analysis.py 生成了 analysis_results 目录，则拷贝其成果到报告目录"""
    src_dir = os.path.join(BASE_DIR, "analysis_results")
    if os.path.isdir(src_dir):
        for name in ["detailed_results.csv","analysis_report.txt",
                     "distributions.png","sentiment_rating_analysis.png",
                     "word_clouds.png","advanced_analysis.png","word_frequency_analysis.csv"]:
            src = os.path.join(src_dir, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(report_path, name))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["GET","POST"])
def search():
    if request.method == "POST":
        keyword = request.form.get("keyword","").strip()
        pages = int(request.form.get("pages", "1") or 1)
    else:
        keyword = request.args.get("q","").strip()
        pages = int(request.args.get("pages","1") or 1)

    if not keyword:
        return render_template("search.html", keyword="", products=[], used_pages=pages)

    # 调用已有的搜索模块
    products = search_amazon_products(keyword, max_pages=pages)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{_safe_filename(keyword)}_{ts}.csv"
    fullpath = os.path.join(PRODUCT_DIR, fname)

    # 记录为历史产品列表
    save_to_csv(products, filename=fullpath)

    # 还生成一份通用的 amazon_product_ids.csv 供后续爬虫复用（只存当前结果）
    save_to_csv(products, filename=os.path.join(BASE_DIR, "amazon_product_ids.csv"))

    return render_template("search.html", keyword=keyword, products=products, used_pages=pages, saved_file=f"data/products/{fname}")

@app.route("/analyze", methods=["POST"])
def analyze():
    product_id = request.form.get("product_id")
    title = request.form.get("title","N/A")
    image_url = request.form.get("image_url","")
    max_pages = int(request.form.get("max_pages","2") or 2)

    if not product_id:
        flash("未获取到产品ID")
        return redirect(url_for("index"))

    # 1) 爬取评论 -> amazon_reviews.csv
    reviews_path = os.path.join(BASE_DIR, "amazon_reviews.csv")
    # 先写表头，防止重复
    if os.path.exists(reviews_path):
        os.remove(reviews_path)
    pd.DataFrame(columns=['product_id','product_title','username','rating','title','body','date']).to_csv(reviews_path, index=False)

    df_reviews = scrape_amazon_reviews(product_id, title, max_pages=max_pages)
    # 直接覆盖保存
    df_reviews.to_csv(reviews_path, index=False)

    if len(df_reviews) == 0:
        flash("未抓取到评论或被风控拦截，请稍后重试或更换产品。")
        return redirect(url_for("search", q=title))

    # 2) 调用情感分析模块
    analyzer = AmazonReviewAnalyzer(use_api=False, api_key=None)
    df = analyzer.analyze_reviews(reviews_path)

    if df is None or len(df)==0:
        flash("分析失败：无有效评论数据。")
        return redirect(url_for("search", q=title))

    # 3) 生成报告（会在 /analysis_results 下产出图表与CSV）
    analyzer.generate_report(df)

    # 4) 保存为历史记录
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + product_id
    report_path = os.path.join(REPORT_DIR, report_id)
    os.makedirs(report_path, exist_ok=True)

    # 拷贝分析产物到报告目录
    _copy_analysis_outputs_to_report(report_path)

    # 保存产品封面图URL和元信息
    meta = {
        "report_id": report_id,
        "product_id": product_id,
        "product_title": title,
        "image_url": image_url,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "review_count": int(len(df)),
    }
    with open(os.path.join(report_path,"meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 5) 生成Chart.js所需数据
    charts = build_chart_payload(df)
    with open(os.path.join(report_path,"charts.json"), "w", encoding="utf-8") as f:
        json.dump(charts, f, ensure_ascii=False)

    # 再保存一个样例评论表（最多前200条）便于页面展示
    sample_reviews = df[['username','rating','content','sentiment','confidence']].copy()
    sample_reviews.rename(columns={"content":"review"}, inplace=True)
    sample_reviews.head(200).to_csv(os.path.join(report_path,"samples.csv"), index=False)

    return redirect(url_for("report", report_id=report_id))

@app.route("/history")
def history():
    cards = []
    for rid in sorted(os.listdir(REPORT_DIR), reverse=True):
        rpath = os.path.join(REPORT_DIR, rid)
        if not os.path.isdir(rpath): 
            continue
        meta_path = os.path.join(rpath, "meta.json")
        if not os.path.exists(meta_path):
            continue
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        cards.append(meta)
    return render_template("history.html", items=cards)

@app.route("/report/<report_id>")
def report(report_id):
    report_path = os.path.join(REPORT_DIR, report_id)
    meta_path = os.path.join(report_path, "meta.json")
    charts_path = os.path.join(report_path, "charts.json")
    csv_path = os.path.join(report_path, "detailed_results.csv")
    samples_path = os.path.join(report_path, "samples.csv")

    if not os.path.exists(meta_path):
        flash("报告不存在")
        return redirect(url_for("history"))

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    charts = {}
    if os.path.exists(charts_path):
        with open(charts_path, "r", encoding="utf-8") as f:
            charts = json.load(f)

    # 附带图像路径（如果存在）
    img_files = []
    for name in ["distributions.png","sentiment_rating_analysis.png","word_clouds.png","advanced_analysis.png"]:
        if os.path.exists(os.path.join(report_path, name)):
            img_files.append(f"{report_id}/{name}")

    # 样例表（前200）
    samples = []
    if os.path.exists(samples_path):
        try:
            samples_df = pd.read_csv(samples_path)
            # 转为dict list
            samples = samples_df.to_dict(orient="records")
        except Exception:
            pass

    return render_template("report.html", meta=meta, charts=charts, img_files=img_files, report_id=report_id, samples=samples)

@app.route("/export/<report_id>/csv")
def export_csv(report_id):
    path = os.path.join(REPORT_DIR, report_id, "detailed_results.csv")
    if not os.path.exists(path):
        # 如无详细结果，则尝试 samples.csv
        path = os.path.join(REPORT_DIR, report_id, "samples.csv")
    if not os.path.exists(path):
        flash("未找到CSV文件")
        return redirect(url_for("report", report_id=report_id))
    return send_file(path, as_attachment=True, download_name=f"{report_id}.csv")

@app.route("/export/<report_id>/pdf")
def export_pdf(report_id):
    """优先使用reportlab生成PDF；若不可用，回退为下载HTML报告"""
    report_path = os.path.join(REPORT_DIR, report_id)
    meta_path = os.path.join(report_path, "meta.json")
    charts_path = os.path.join(report_path, "charts.json")
    if not os.path.exists(meta_path):
        flash("报告不存在")
        return redirect(url_for("history"))

    # 读取数据
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    charts = {}
    if os.path.exists(charts_path):
        with open(charts_path, "r", encoding="utf-8") as f:
            charts = json.load(f)

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # 标题
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, height-2*cm, "Amazon 评论分析报告")
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, height-2.6*cm, f"产品：{meta.get('product_title','N/A')} (ID: {meta.get('product_id','')})")
        c.drawString(2*cm, height-3.1*cm, f"时间：{meta.get('created_at','')}   评论数：{meta.get('review_count',0)}")

        y = height-3.8*cm
        # 插入分析图（如存在）
        for name in ["distributions.png","sentiment_rating_analysis.png","word_clouds.png","advanced_analysis.png"]:
            img_path = os.path.join(report_path, name)
            if os.path.exists(img_path):
                try:
                    img = ImageReader(img_path)
                    # 以版芯宽度缩放
                    iw, ih = img.getSize()
                    max_w = width - 4*cm
                    scale = min(max_w/iw, 14*cm/ih)
                    new_w, new_h = iw*scale, ih*scale
                    if y - new_h < 2*cm:
                        c.showPage()
                        y = height-2*cm
                    c.drawImage(img, 2*cm, y-new_h, new_w, new_h)
                    y -= (new_h + 0.6*cm)
                except Exception:
                    continue

        # 结束
        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"{report_id}.pdf", mimetype="application/pdf")

    except Exception as e:
        # 回退：导出静态HTML文件（用户可打印为PDF）
        html = render_template("report.html", meta=meta, charts=charts, img_files=[
            name for name in ["distributions.png","sentiment_rating_analysis.png","word_clouds.png","advanced_analysis.png"]
            if os.path.exists(os.path.join(report_path, name))
        ], report_id=report_id, samples=[])
        html_bytes = html.encode("utf-8")
        return send_file(io.BytesIO(html_bytes), as_attachment=True, download_name=f"{report_id}.html", mimetype="text/html; charset=utf-8")

@app.route("/assets/report/<report_id>/<name>")
def report_asset(report_id, name):
    """供模板访问报告目录中的图片等静态文件"""
    path = os.path.join(REPORT_DIR, report_id, name)
    if not os.path.exists(path):
        return ("Not Found", 404)
    return send_file(path)

# 健康检查
@app.route("/health")
def health():
    return jsonify(ok=True, time=time.time())

if __name__ == "__main__":
    # 在开发环境下运行
    app.run(host="0.0.0.0", port=5000, debug=True)
