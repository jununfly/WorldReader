#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取东方财富板块涨跌幅数据
"""

import requests
import json
from datetime import datetime

def get_sector_data():
    """获取今日板块涨跌幅排行"""
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "cb": "jQuery",
        "pn": "1",
        "pz": "50",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:90+t:2",  # 行业板块
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152",
        "_": int(datetime.now().timestamp() * 1000)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            # 移除 jQuery 回调
            text = response.text
            if text.startswith('jQuery'):
                text = text[text.index('(') + 1:text.rindex(')')]
            data = json.loads(text)

            if data.get('data') and data['data'].get('diff'):
                sectors = data['data']['diff']
                result = {
                    "top_rise": [],
                    "top_fall": []
                }

                for sector in sectors[:5]:  # 前5名
                    result["top_rise"].append({
                        "name": sector.get("f14", ""),
                        "code": sector.get("f12", ""),
                        "change": sector.get("f3", 0),
                        "price": sector.get("f2", 0)
                    })

                for sector in sectors[-5:]:  # 后5名
                    result["top_fall"].append({
                        "name": sector.get("f14", ""),
                        "code": sector.get("f12", ""),
                        "change": sector.get("f3", 0),
                        "price": sector.get("f2", 0)
                    })

                return result
    except Exception as e:
        print(f"Error fetching sector data: {e}")

    return None

if __name__ == "__main__":
    result = get_sector_data()
    if result:
        print("领涨板块:")
        for sector in result["top_rise"]:
            print(f"  {sector['name']} ({sector['code']}): {sector['change']:.2f}%")

        print("\n领跌板块:")
        for sector in result["top_fall"]:
            print(f"  {sector['name']} ({sector['code']}): {sector['change']:.2f}%")
    else:
        print("暂无数据")