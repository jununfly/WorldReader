#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用新浪财经API获取板块涨跌幅排行
"""

import requests
import json
from datetime import datetime

def get_sector_data_sina():
    """获取今日板块涨跌幅排行（新浪财经）"""
    # 新浪财经行业板块API
    url = "https://hq.sinajs.cn/list=s_bk0001"
    headers = {
        'Referer': 'https://finance.sina.com.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.text
            # 解析新浪返回的数据格式
            # 格式: var hq_str_s_bk0001="板块名,最新价,涨跌额,涨跌幅,成交量,...";
            data = {}

            # 获取所有板块ID (s_bk0001 到 s_bk0075)
            for i in range(1, 76):
                board_id = f"s_bk{i:04d}"
                board_url = f"https://hq.sinajs.cn/list={board_id}"

                try:
                    resp = requests.get(board_url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        content = resp.text
                        if f'var hq_str_{board_id}=' in content:
                            start = content.index('"') + 1
                            end = content.rindex('"')
                            values = content[start:end].split(',')

                            if len(values) > 3:
                                name = values[0]
                                price = values[1]
                                change = values[3]
                                if name and change:
                                    try:
                                        change_float = float(change)
                                        data[name] = {
                                            "name": name,
                                            "change": change_float,
                                            "price": price
                                        }
                                    except:
                                        continue
                except:
                    continue

            # 排序
            sorted_sectors = sorted(data.items(), key=lambda x: x[1]['change'], reverse=True)

            return {
                "top_rise": sorted_sectors[:5],
                "top_fall": sorted_sectors[-5:]
            }
    except Exception as e:
        print(f"Error fetching sector data from Sina: {e}")

    return None

if __name__ == "__main__":
    result = get_sector_data_sina()
    if result:
        print("领涨板块:")
        for name, data in result["top_rise"]:
            print(f"  {name}: {data['change']:.2f}%")

        print("\n领跌板块:")
        for name, data in result["top_fall"]:
            print(f"  {name}: {data['change']:.2f}%")
    else:
        print("暂无数据")