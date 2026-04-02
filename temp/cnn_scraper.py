#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取 CNN 恐贪指数
"""

import requests
import re
from datetime import datetime

def get_cnn_fear_greed():
    """获取 CNN Fear & Greed Index"""
    url = "https://money.cnn.com/data/fear-and-greed/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            # 查找 Fear & Greed 数值
            # 通常在页面中有类似 <li>Fear & Greed Now: <span>XX</span></li>
            text = response.text

            # 尝试多种模式匹配
            patterns = [
                r'Fear\s*&\s*Greed\s*Now:\s*<[^>]+>(\d+)</span>',
                r'"fgNow":\s*(\d+)',
                r'<span[^>]*class="fg-now"[^>]*>(\d+)</span>',
                r'data-value="(\d+)"[^>]*class="[^"]*gauge-value',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = int(match.group(1))
                    # 判断情绪
                    if value <= 20:
                        sentiment = "极度恐慌"
                    elif value <= 40:
                        sentiment = "恐慌"
                    elif value <= 60:
                        sentiment = "中性"
                    elif value <= 80:
                        sentiment = "贪婪"
                    else:
                        sentiment = "极度贪婪"

                    return {
                        "value": value,
                        "sentiment": sentiment,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
    except Exception as e:
        print(f"Error fetching CNN Fear & Greed: {e}")

    return None

if __name__ == "__main__":
    result = get_cnn_fear_greed()
    if result:
        print(f"CNN恐贪指数: {result['value']}")
        print(f"情绪状态: {result['sentiment']}")
        print(f"更新时间: {result['timestamp']}")
    else:
        print("暂无数据")