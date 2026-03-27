#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用腾讯财经API获取板块涨跌幅排行
"""

import requests
from datetime import datetime

def get_sector_data_tencent():
    """获取今日板块涨跌幅排行（腾讯财经）"""
    url = "http://qt.gtimg.cn/q=qs_bk0001"
    headers = {
        'Referer': 'https://gu.qq.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    data = []

    try:
        # 获取多个板块
        for i in range(1, 50):
            board_id = f"qs_bk{i:04d}"
            board_url = f"http://qt.gtimg.cn/q={board_id}"

            try:
                resp = requests.get(board_url, headers=headers, timeout=3)
                if resp.status_code == 200 and resp.text.strip():
                    # 格式: v_qs_bk0001="板块名~涨跌幅~..."
                    content = resp.text.strip()
                    if '~' in content:
                        parts = content.split('~')
                        if len(parts) > 2:
                            name = parts[0].split('"')[-1] if '"' in parts[0] else parts[0]
                            try:
                                change = float(parts[1])
                                if name:
                                    data.append({
                                        "name": name,
                                        "change": change
                                    })
                            except:
                                continue
            except:
                continue

        if data:
            sorted_data = sorted(data, key=lambda x: x['change'], reverse=True)
            return {
                "top_rise": sorted_data[:5],
                "top_fall": sorted_data[-5:]
            }

    except Exception as e:
        print(f"Error: {e}")

    return None

if __name__ == "__main__":
    result = get_sector_data_tencent()
    if result:
        print("领涨板块:")
        for item in result["top_rise"]:
            print(f"  {item['name']}: {item['change']:.2f}%")

        print("\n领跌板块:")
        for item in result["top_fall"]:
            print(f"  {item['name']}: {item['change']:.2f}%")
    else:
        print("暂无数据")