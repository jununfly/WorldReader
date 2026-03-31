#!/usr/bin/env python3
"""测试 BaaFetcher"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

url = 'https://hub.baai.ac.cn/users/72033'
target_date = '2026-03-31'

print(f"测试 URL: {url}")
print(f"目标日期: {target_date}")
print()

# 获取 HTML
html = requests.get(url, timeout=30).text
soup = BeautifulSoup(html, 'html.parser')

# 查找 main
main = soup.find('main')
if not main:
    print("❌ 未找到 main 标签")
    sys.exit(1)

print(f"✅ 找到 main 标签")
print()

# 查找所有链接
links = main.find_all('a', href=True)
print(f"找到 {len(links)} 个链接")
print()

# 分析链接结构
print("=== 分析链接结构 ===")
for i, link in enumerate(links[:5]):
    href = link.get('href', '')
    if '/view/' in href:
        print(f"\n链接 {i+1}:")
        print(f"  href: {href}")
        print(f"  子节点:")
        for j, child in enumerate(link.children):
            if child.name:
                print(f"    {j}. <{child.name}>")
            else:
                text = child.strip()
                if text:
                    print(f"    {j}. 文本: {text[:100]}")

print("\n=== 测试文章提取 ===")

# 提取文章
articles = []
for link in links:
    href = link.get('href', '')
    
    if not href.startswith('/view/'):
        continue

    article_id = href.replace('/view/', '').strip()
    if not article_id:
        continue

    heading = link.find('h6')
    if not heading:
        continue
    
    title = heading.get_text(strip=True)
    if not title:
        continue

    # 提取发布时间
    published_at = ''
    for child in link.children:
        if child.name is None and child.strip():
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', child.strip())
            if time_match:
                published_at = time_match.group(1)
                break

    if not published_at:
        print(f"⚠️  跳过（无时间）: {title}")
        continue

    # 检查日期
    pub_date = published_at.split()[0]
    is_target = pub_date == target_date
    
    print(f"\n📄 文章: {title}")
    print(f"   发布时间: {published_at}")
    print(f"   日期: {pub_date}")
    print(f"   是否目标日期: {'✅' if is_target else '❌'}")
    
    if is_target:
        articles.append({
            'id': article_id,
            'title': title,
            'url': f"https://hub.baai.ac.cn{href}",
            'published_at': published_at
        })

print(f"\n=== 结果 ===")
print(f"找到 {len(articles)} 篇目标日期的文章:")
for article in articles:
    print(f"  - {article['title']}")