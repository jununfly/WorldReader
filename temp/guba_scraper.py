#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取股吧情绪（东方财富）
"""

import requests
from datetime import datetime

def get_guba_sentiment():
    """获取东方财富股吧情绪"""
    url = "http://guba.eastmoney.com/list,000001,f_1.html"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.text
            # 简单统计
            import re
            
            # 提取帖子标题
            titles = re.findall(r'<span class="l3 a3">.*?title="(.*?)"', text)
            
            print(f"股吧帖子数量: {len(titles)}")
            print("\n最新5条帖子:")
            for i, title in enumerate(titles[:5], 1):
                print(f"  {i}. {title}")
            
            return len(titles)
    except Exception as e:
        print(f"Error: {e}")

    return None

if __name__ == "__main__":
    result = get_guba_sentiment()
    if result:
        print(f"\n股吧活跃度: {result}")
    else:
        print("暂无数据")