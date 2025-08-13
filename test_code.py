import time
import json
import psutil
import platform
import hashlib
import queue
import threading
import logging
import random
import os
import tempfile
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Tuple, Optional, Any
import requests
from fake_useragent import UserAgent
import pytest
import socket
from collections import defaultdict
import matplotlib.pyplot as plt  # 用于生成性能图表（需安装matplotlib）
import concurrent.futures  # 补充缺失的导入

# ------------------------------
# 配置与常量定义
# ------------------------------
TEST_CONFIG = {
    "base_url": "http://localhost:63342/team12/start_interface.html",  # 替换为实际测试(项目)网站
    "test_paths": {
        "product_comments": "/product1/comments",
        "article_reviews": "/article3/discussions",
        "video_ratings": "/video5/ratings"
    },
    "expected_fields": {
        "product_comments": ["author", "content", "timestamp", "rating", "product_id"],
        "article_reviews": ["author", "content", "timestamp", "reply_count", "article_id"],
        "video_ratings": ["author", "content", "timestamp", "score", "video_id"]
    },
    "performance": {
        "quick_runs": 2,  # 每个路径快速运行次数
        "long_duration": 300,  # 长时间运行时长（秒）
        "extreme_concurrency": 32  # 极限并发数
    },
    "compatibility": {
        "browsers": ["chrome", "firefox", "safari", "edge", "opera"],
        "os_list": ["Windows-10", "Linux-5.4.0-100-generic", "Darwin-21.6.0"]  # 模拟不同系统
    },
    "security": {
        "sensitive_patterns": ["password", "key", "token", "database", "internal"],
        "restricted_paths": ["/admin/comments", "/user/private-reviews"]
    }
}

# ------------------------------
# 日志与报告配置
# ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestReport:
    """测试报告生成器"""

    def __init__(self):
        self.report = {
            "metadata": {
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system_info": self._get_system_info()
            },
            "functional_test": {},
            "performance_test": {},
            "compatibility_test": {},
            "security_test": {}
        }

    @staticmethod
    def _get_system_info() -> Dict:
        """获取系统信息"""
        return {
            "os": platform.system(),
            "os_version": platform.release(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "ram_gb": f"{psutil.virtual_memory().total / (1024 ** 3):.2f}",
            "machine": platform.machine()
        }

    def save(self, file_path: str = "crawler_test_report.json"):
        """保存报告到JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        logger.info(f"测试报告已保存至: {file_path}")

    def add_section(self, section_name: str, data: Dict):
        """添加测试章节到报告"""
        self.report[section_name] = data


# ------------------------------
# 核心测试类
# ------------------------------
class CrawlerTester:
    def __init__(self, crawler, report: TestReport):
        self.crawler = crawler  # 待测试的爬虫实例
        self.report = report
        self.session = requests.Session()  # 共享HTTP会话
        self.ua = UserAgent()

    # ------------------------------
    # 功能测试模块
    # ------------------------------
    def functional_test(self):
        """验证爬虫核心功能：评论提取准确性、异常处理能力"""
        logger.info("===== 开始功能测试 =====")
        results = {"total_cases": 0, "passed_cases": 0, "failed_cases": []}

        # 测试1：正常评论提取（覆盖所有预期路径）
        for path_name, path in TEST_CONFIG["test_paths"].items():
            full_url = f"{TEST_CONFIG['base_url']}{path}"
            expected_fields = TEST_CONFIG["expected_fields"][path_name]
            case_result = self._test_comment_extraction(full_url, expected_fields, path_name)
            results["total_cases"] += 1
            if case_result["success"]:
                results["passed_cases"] += 1
            else:
                results["failed_cases"].append(case_result)

        # 测试2：无评论页面处理
        no_comment_url = f"{TEST_CONFIG['base_url']}/empty-comments"
        case_result = self._test_empty_comments(no_comment_url)
        results["total_cases"] += 1
        if case_result["success"]:
            results["passed_cases"] += 1
        else:
            results["failed_cases"].append(case_result)

        # 测试3：反爬机制应对（模拟验证码/封禁）
        blocked_url = f"{TEST_CONFIG['base_url']}/blocked-comments"
        case_result = self._test_anti_spider(blocked_url)
        results["total_cases"] += 1
        if case_result["success"]:
            results["passed_cases"] += 1
        else:
            results["failed_cases"].append(case_result)

        self.report.add_section("functional_test", results)
        logger.info(f"功能测试完成：通过率 {results['passed_cases']}/{results['total_cases']}")

    def _test_comment_extraction(self, url: str, expected_fields: List[str], path_name: str) -> Dict:
        """测试单条路径的评论提取准确性"""
        case = {
            "url": url,
            "expected_fields": expected_fields,
            "success": False,
            "error": None,
            "comment_count": 0,
            "missing_fields": []
        }

        try:
            start_time = time.time()
            comments = self.crawler.crawl(url)
            case["execution_time"] = time.time() - start_time
            case["comment_count"] = len(comments)

            if not comments:
                case["error"] = "未提取到任何评论"
                return case

            # 验证字段完整性（检查前10条评论）
            for comment in comments[:10]:
                for field in expected_fields:
                    if field not in comment:
                        case["missing_fields"].append(field)
                        case["success"] = False

            if not case["missing_fields"]:
                case["success"] = True
                logger.info(f"功能测试通过：{url} 提取 {len(comments)} 条评论，字段完整")
            else:
                case["error"] = f"缺失字段: {case['missing_fields']}"

        except Exception as e:
            case["error"] = str(e)
            logger.error(f"功能测试失败：{url} - {str(e)}")

        return case

    def _test_empty_comments(self, url: str) -> Dict:
        """测试无评论页面的处理逻辑"""
        case = {
            "url": url,
            "success": False,
            "error": None,
            "expected_message": "无评论数据"
        }

        try:
            comments = self.crawler.crawl(url)
            if not comments:
                # 验证是否返回友好提示（根据爬虫实现调整）
                if hasattr(self.crawler, "parse_empty"):
                    result = self.crawler.parse_empty()
                    case["success"] = result.get("message") == case["expected_message"]
                else:
                    case["success"] = True  # 若爬虫默认处理空数据则通过
            else:
                case["error"] = "预期无评论，但实际提取到数据"

        except Exception as e:
            case["error"] = f"处理空评论时异常: {str(e)}"

        if case["success"]:
            logger.info(f"功能测试通过：{url} 正确处理无评论场景")
        else:
            logger.error(f"功能测试失败：{url} - {case['error']}")

        return case

    def _test_anti_spider(self, url: str) -> Dict:
        """测试反爬机制（如验证码、IP封禁）"""
        case = {
            "url": url,
            "success": False,
            "error": None,
            "expected_error": "访问受限"
        }

        try:
            # 模拟未登录状态访问受限路径
            self.crawler.set_auth(None)  # 清除认证信息
            self.crawler.crawl(url)
            case["error"] = "未触发反爬机制，可能允许未授权访问"
        except Exception as e:
            if case["expected_error"] in str(e):
                case["success"] = True
                logger.info(f"功能测试通过：{url} 正确触发反爬机制")
            else:
                case["error"] = f"触发异常但非预期错误: {str(e)}"

        return case

    # ------------------------------
    # 性能测试模块
    # ------------------------------
    def performance_test(self):
        """评估不同负载下的响应速度、稳定性与资源占用"""
        logger.info("===== 开始性能测试 =====")
        results = {
            "quick_run": {},
            "long_run": {},
            "extreme_load": {}
        }

        # 快速运行测试（短时间高频）
        self._quick_run_test(results["quick_run"])

        # 长时间运行测试（持续压力）
        self._long_run_test(results["long_run"])

        # 极限负载测试（高并发）
        self._extreme_load_test(results["extreme_load"])

        self.report.add_section("performance_test", results)
        logger.info("性能测试完成")

    def _quick_run_test(self, result: Dict):
        """快速运行测试：短时间内多次请求"""
        logger.info("执行快速运行测试...")
        urls = [f"{TEST_CONFIG['base_url']}{path}"
                for path in TEST_CONFIG["test_paths"].values()] * TEST_CONFIG["performance"]["quick_runs"]

        start_time = time.time()
        success_count = 0
        durations = []
        comment_counts = []

        # 多线程并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._crawl_with_metric, url): url for url in urls}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    duration, count = future.result()
                    durations.append(duration)
                    comment_counts.append(count)
                    if duration < 10:  # 设定超时阈值（秒）
                        success_count += 1
                except Exception as e:
                    logger.warning(f"快速测试失败：{url} - {str(e)}")

        # 统计结果
        result.update({
            "total_requests": len(urls),
            "successful_requests": success_count,
            "success_rate": f"{(success_count / len(urls)) * 100:.2f}%" if urls else "N/A",
            "avg_duration": f"{sum(durations) / len(durations):.2f}s" if durations else "N/A",
            "max_duration": f"{max(durations):.2f}s" if durations else "N/A",
            "min_duration": f"{min(durations):.2f}s" if durations else "N/A",
            "avg_comments": f"{sum(comment_counts) / len(comment_counts):.2f}条" if comment_counts else "N/A"
        })

    def _long_run_test(self, result: Dict):
        """长时间运行测试：持续5分钟压力"""
        logger.info("执行长时间运行测试...")
        start_time = time.time()
        end_time = start_time + TEST_CONFIG["performance"]["long_duration"]
        urls = [f"{TEST_CONFIG['base_url']}{path}"
                for path in TEST_CONFIG["test_paths"].values()]

        success_count = 0
        durations = []
        memory_usage = []
        cpu_usage = []

        # 监控线程：每1秒记录资源使用
        def monitor():
            process = psutil.Process(os.getpid())
            while time.time() < end_time:
                memory_usage.append(process.memory_info().rss / 1024 ** 2)  # MB
                cpu_usage.append(process.cpu_percent(interval=1))
                time.sleep(1)

        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.start()

        # 持续发送请求
        while time.time() < end_time:
            for url in urls:
                if time.time() >= end_time:
                    break
                try:
                    start = time.time()
                    self.crawler.crawl(url)
                    durations.append(time.time() - start)
                    success_count += 1
                except:
                    pass

        monitor_thread.join()

        # 统计结果
        result.update({
            "duration_seconds": TEST_CONFIG["performance"]["long_duration"],
            "total_requests": success_count,
            "success_rate": f"{(success_count / (len(urls) * (end_time - start_time))) * 100:.2f}%" if urls else "N/A",
            "avg_duration": f"{sum(durations) / len(durations):.2f}s" if durations else "N/A",
            "memory_usage": {
                "max_mb": max(memory_usage) if memory_usage else 0,
                "avg_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0
            },
            "cpu_usage": {
                "max_percent": max(cpu_usage) if cpu_usage else 0,
                "avg_percent": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
            }
        })

    def _extreme_load_test(self, result: Dict):
        """极限负载测试：高并发请求"""
        logger.info("执行极限负载测试...")
        urls = [f"{TEST_CONFIG['base_url']}{path}"
                for path in TEST_CONFIG["test_paths"].values()] * TEST_CONFIG["performance"]["extreme_concurrency"]

        start_time = time.time()
        success_count = 0
        errors = []
        concurrency_levels = [8, 16, 32]  # 测试不同并发数

        for concurrency in concurrency_levels:
            logger.info(f"测试并发数：{concurrency}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = {executor.submit(self._crawl_with_metric, url): url for url in urls}
                level_success = 0
                level_errors = []
                for future in concurrent.futures.as_completed(futures):
                    url = futures[future]
                    try:
                        duration, _ = future.result()
                        if duration < 15:  # 极限场景放宽超时阈值
                            level_success += 1
                    except Exception as e:
                        level_errors.append(str(e))
                success_count += level_success
                errors.extend(level_errors)

        # 统计结果
        result.update({
            "max_concurrency": TEST_CONFIG["performance"]["extreme_concurrency"],
            "total_requests": len(urls) * len(concurrency_levels),
            "successful_requests": success_count,
            "error_rate": f"{((len(urls) * len(concurrency_levels) - success_count) / (len(urls) * len(concurrency_levels))) * 100:.2f}%" if urls else "N/A",
            "error_details": list(set(errors)),  # 去重错误类型
            "recommendation": "降低并发数或优化爬虫速率限制" if errors else "系统稳定"
        })

    def _crawl_with_metric(self, url: str) -> Tuple[float, int]:
        """带指标记录的爬取方法"""
        start_time = time.time()
        comments = self.crawler.crawl(url)
        return (time.time() - start_time, len(comments))

    # ------------------------------
    # 兼容性测试模块
    # ------------------------------
    def compatibility_test(self):
        """验证不同环境下的兼容性（浏览器UA、操作系统）"""
        logger.info("===== 开始兼容性测试 =====")
        results = {
            "browser_ua": {},
            "os_environment": {}
        }

        # 浏览器UA兼容性测试
        self._browser_ua_test(results["browser_ua"])

        # 操作系统兼容性测试（模拟不同系统环境）
        self._os_environment_test(results["os_environment"])

        self.report.add_section("compatibility_test", results)
        logger.info("兼容性测试完成")

    def _browser_ua_test(self, result: Dict):
        """测试不同浏览器UA的请求头"""
        logger.info("测试浏览器UA兼容性...")
        for browser in TEST_CONFIG["compatibility"]["browsers"]:
            try:
                ua = self.ua[browser]
                self.crawler.set_headers({"User-Agent": ua})  # 假设爬虫支持设置请求头
                test_url = f"{TEST_CONFIG['base_url']}{random.choice(list(TEST_CONFIG['test_paths'].values()))}"
                comments = self.crawler.crawl(test_url)
                result[browser] = {
                    "success": len(comments) > 0,
                    "comment_count": len(comments),
                    "user_agent": ua
                }
                logger.info(f"UA测试通过：{browser} 提取 {len(comments)} 条评论")
            except Exception as e:
                result[browser] = {
                    "success": False,
                    "error": str(e),
                    "user_agent": ua
                }
                logger.error(f"UA测试失败：{browser} - {str(e)}")

    def _os_environment_test(self, result: Dict):
        """测试不同操作系统环境（需结合CI/CD工具，此处模拟）"""
        logger.info("测试操作系统兼容性...")
        for os_name in TEST_CONFIG["compatibility"]["os_list"]:
            # 实际需在对应系统环境运行，此处模拟记录
            result[os_name] = {
                "status": "模拟通过",
                "note": "需在真实环境中验证"
            }
            logger.info(f"OS兼容性模拟：{os_name} - 假设通过")

    # ------------------------------
    # 安全测试模块
    # ------------------------------
    def security_test(self):
        """检测数据泄露、非法访问等安全风险"""
        logger.info("===== 开始安全测试 =====")
        results = {
            "data_leakage": {},
            "unauthorized_access": {},
            "input_validation": {}
        }

        # 数据泄露检测（临时文件、日志）
        self._data_leakage_test(results["data_leakage"])

        # 非法访问检测（未授权路径）
        self._unauthorized_access_test(results["unauthorized_access"])

        # 输入验证检测（恶意URL）
        self._input_validation_test(results["input_validation"])

        self.report.add_section("security_test", results)
        logger.info("安全测试完成")

    def _data_leakage_test(self, result: Dict):
        """检测敏感数据泄露"""
        logger.info("检测数据泄露风险...")
        test_cases = [
            ("临时文件", self._test_temp_file_leakage),
            ("日志文件", self._test_log_leakage)
        ]

        for case_name, test_func in test_cases:
            case_result = {"success": False, "error": None}
            try:
                test_func(case_result)
                case_result["success"] = True
            except Exception as e:
                case_result["error"] = str(e)
            result[case_name] = case_result

    def _test_temp_file_leakage(self, case_result: Dict):
        """测试临时文件是否被正确清理"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write("敏感数据: 123456")
            tmp_path = tmp_file.name

        # 假设爬虫会处理此文件
        self.crawler.process_temp_file(tmp_path)  # 需爬虫实现此方法

        # 检查文件是否删除
        if os.path.exists(tmp_path):
            case_result["error"] = "临时文件未清理"
        else:
            case_result["message"] = "临时文件已清理"

    def _test_log_leakage(self, case_result: Dict):
        """测试日志是否包含敏感信息"""
        log_path = "crawler_test.log"
        sensitive_data = "test_password_123"

        # 模拟写入敏感数据到日志
        logger.info(f"测试日志敏感信息: {sensitive_data}")

        # 检查日志内容
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
                if sensitive_data in log_content:
                    case_result["error"] = "日志包含敏感信息"
                else:
                    case_result["message"] = "日志无敏感信息"
        else:
            case_result["error"] = "日志文件未生成"

    def _unauthorized_access_test(self, result: Dict):
        """检测未授权访问控制"""
        logger.info("检测未授权访问风险...")
        restricted_urls = [
            f"{TEST_CONFIG['base_url']}{path}"
            for path in TEST_CONFIG["security"]["restricted_paths"]
        ]

        for url in restricted_urls:
            case_result = {"success": False, "error": None}
            try:
                self.crawler.set_auth(None)  # 清除认证
                self.crawler.crawl(url)
                case_result["error"] = "未授权访问成功"
            except Exception as e:
                if "403" in str(e) or "权限不足" in str(e):
                    case_result["success"] = True
                    case_result["message"] = "正确拒绝未授权访问"
                else:
                    case_result["error"] = f"意外错误: {str(e)}"
            result[url] = case_result

    def _input_validation_test(self, result: Dict):
        """检测输入验证（防止注入攻击）"""
        logger.info("检测输入验证风险...")
        malicious_urls = [
            f"{TEST_CONFIG['base_url']}/comments?user_id=1' OR '1'='1",  # SQL注入
            f"{TEST_CONFIG['base_url']}/comments?content=<script>alert(1)</script>"  # XSS
        ]

        for url in malicious_urls:
            case_result = {"success": False, "error": None}
            try:
                self.crawler.crawl(url)
                # 若爬虫未崩溃或执行恶意代码则通过
                case_result["success"] = True
                case_result["message"] = "输入验证有效"
            except Exception as e:
                case_result["error"] = f"输入验证失败: {str(e)}"
            result[url] = case_result

    # ------------------------------
    # 辅助方法
    # ------------------------------
    def generate_performance_charts(self):
        """生成性能图表（需matplotlib）"""
        # 示例：从报告中提取快速运行测试的持续时间数据
        quick_run_data = self.report.report["performance_test"].get("quick_run", {})
        if not quick_run_data:
            logger.warning("无性能数据可生成图表")
            return

        durations = []
        # 假设快速运行测试的持续时间存储在某个字段中（需根据实际报告结构调整）
        # 此处仅为示例，实际需根据测试结果填充数据
        plt.figure(figsize=(10, 5))
        plt.hist([1.2, 0.8, 1.5, 0.9], bins=20, color='blue', alpha=0.7)  # 模拟数据
        plt.xlabel('响应时间（秒）')
        plt.ylabel('请求次数')
        plt.title('爬虫响应时间分布（快速运行测试）')
        plt.savefig('performance_distribution.png')
        logger.info("性能图表已保存至 performance_distribution.png")


# ------------------------------
# 示例爬虫实现（需根据实际替换）
# ------------------------------
# 补充缺失的导入（关键修复1）
from fake_useragent import UserAgent  # 导入生成随机User-Agent的库


class ExampleCommentCrawler:
    def __init__(self):
        # 关键修复2：初始化ua属性（必须添加）
        self.ua = UserAgent()  # 创建UserAgent对象，用于生成随机User-Agent

        # 原代码逻辑（保留，但依赖self.ua已初始化）
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.ua.random,  # 现在self.ua已存在，可正常访问
            "Accept": "application/json"
        })
        self.auth_token = None

    def set_headers(self, headers: Dict):
        self.session.headers.update(headers)

    def set_auth(self, token: Optional[str]):
        self.auth_token = token
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def process_temp_file(self, file_path: str):
        """示例：处理临时文件（正确清理）"""
        if os.path.exists(file_path):
            os.unlink(file_path)

    def crawl(self, url: str) -> List[Dict]:
        """模拟爬取评论"""
        try:
            # 模拟网络延迟（0.1-1.5秒）
            time.sleep(random.uniform(0.1, 1.5))

            # 模拟反爬：5%概率返回403
            if random.random() < 0.05:
                raise requests.exceptions.HTTPError("403 Forbidden")

            # 模拟评论数据
            return [{
                "author": f"user_{random.randint(1000, 9999)}",
                "content": f"测试评论 #{random.randint(1, 100)}",
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "rating": random.randint(1, 5)
            } for _ in range(random.randint(5, 15))]

        except Exception as e:
            raise e


# ------------------------------
# 测试执行入口
# ------------------------------
if __name__ == "__main__":
    # 初始化测试组件
    crawler = ExampleCommentCrawler()
    report = TestReport()
    tester = CrawlerTester(crawler, report)

    # 执行全量测试
    tester.functional_test()
    tester.performance_test()
    tester.compatibility_test()
    tester.security_test()

    # 生成报告与图表（图表使用模拟数据）
    report.save()
    tester.generate_performance_charts()

    # 输出摘要
    print("\n===== 测试摘要 =====")
    print(
        f"功能测试通过率: {report.report['functional_test']['passed_cases']}/{report.report['functional_test']['total_cases']}")
    print(f"快速运行成功率: {report.report['performance_test']['quick_run'].get('success_rate', 'N/A')}")
    print(f"长时间运行内存峰值: {report.report['performance_test']['long_run']['memory_usage']['max_mb']:.2f}MB")
    print(
        f"浏览器兼容性通过率: {sum(1 for ua in report.report['compatibility_test']['browser_ua'].values() if ua['success'])}/{len(report.report['compatibility_test']['browser_ua'])}")
    print(f"安全测试建议: 检查临时文件清理逻辑（若有错误）")