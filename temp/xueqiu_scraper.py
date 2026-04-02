#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取雪球情绪指标
"""

import requests
import json
from datetime import datetime

def get_xueqiu_sentiment():
    """获取雪球市场情绪"""
    # 雪球市场情绪API
    url = "https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH000001&extend=detail"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://xueqiu.com/'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("雪球API返回数据:", json.dumps(data, ensure_ascii=False, indent=2)[:500])
            return data
    except Exception as e:
        print(f"Error: {e}")

    return None

if __name__ == "__main__":
    result = get_xueqiu_sentiment()
    if result:
        print("\n雪球情绪数据获取成功")
    else:
        print("暂无数据")