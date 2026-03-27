#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日市场情绪日报数据收集
"""

import akshare as ak
import yfinance as yf
from datetime import datetime

def get_market_sentiment_data():
    """收集市场情绪数据"""
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "北向资金": None,
        "VIX恐慌指数": None,
        "两融余额": None,
        "CNN恐贪指数": "暂无数据",
        "AAII散户情绪": "暂无数据",
        "Put/Call Ratio": "暂无数据",
        "雪球/股吧情绪": "暂无数据"
    }

    # 1. 北向资金
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        north_money = df[df['板块'].isin(['沪股通', '深股通'])]
        total_net_buy = north_money['成交净买额'].sum()
        data["北向资金"] = {
            "沪股通": north_money[north_money['板块']=='沪股通']['成交净买额'].values[0] if len(north_money[north_money['板块']=='沪股通']) > 0 else 0,
            "深股通": north_money[north_money['板块']=='深股通']['成交净买额'].values[0] if len(north_money[north_money['板块']=='深股通']) > 0 else 0,
            "合计": float(total_net_buy)
        }
    except Exception as e:
        print(f"北向资金获取失败: {e}")

    # 2. VIX恐慌指数
    try:
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="5d")
        if not vix_hist.empty:
            latest = vix_hist.iloc[-1]
            vix_value = float(latest['Close'])

            if vix_value > 25:
                sentiment = "恐惧"
            elif vix_value < 15:
                sentiment = "贪婪"
            else:
                sentiment = "中性"

            data["VIX恐慌指数"] = {
                "数值": vix_value,
                "情绪": sentiment
            }
    except Exception as e:
        print(f"VIX获取失败: {e}")

    # 3. 两融余额
    try:
        df_sh = ak.stock_margin_sse()
        latest = df_sh.iloc[0]
        data["两融余额"] = {
            "日期": latest['信用交易日期'],
            "余额": float(latest['融资融券余额'] / 1e8),
            "单位": "亿元"
        }
    except Exception as e:
        print(f"两融获取失败: {e}")

    return data

if __name__ == "__main__":
    data = get_market_sentiment_data()

    print("=" * 60)
    print("市场情绪日报数据")
    print("=" * 60)
    print(f"更新时间: {data['timestamp']}")
    print()

    # 北向资金
    print("📊 北向资金")
    if data["北向资金"]:
        print(f"  沪股通: {data['北向资金']['沪股通']}亿元")
        print(f"  深股通: {data['北向资金']['深股通']}亿元")
        print(f"  合计: {data['北向资金']['合计']}亿元")
        if data['北向资金']['合计'] > 0:
            print(f"  状态: 净流入 {abs(data['北向资金']['合计'])}亿元")
        else:
            print(f"  状态: 净流出 {abs(data['北向资金']['合计'])}亿元")
    else:
        print("  暂无数据")
    print()

    # VIX
    print("📊 VIX恐慌指数")
    if data["VIX恐慌指数"]:
        print(f"  数值: {data['VIX恐慌指数']['数值']:.2f}")
        print(f"  情绪: {data['VIX恐慌指数']['情绪']}")
    else:
        print("  暂无数据")
    print()

    # 两融余额
    print("📊 两融余额")
    if data["两融余额"]:
        print(f"  日期: {data['两融余额']['日期']}")
        print(f"  余额: {data['两融余额']['余额']:.2f}{data['两融余额']['单位']}")
    else:
        print("  暂无数据")
    print()

    # 其他指标
    print("📊 其他情绪指标")
    print(f"  CNN恐贪指数: {data['CNN恐贪指数']}")
    print(f"  AAII散户情绪: {data['AAII散户情绪']}")
    print(f"  Put/Call Ratio: {data['Put/Call Ratio']}")
    print(f"  雪球/股吧情绪: {data['雪球/股吧情绪']}")