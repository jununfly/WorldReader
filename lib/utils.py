"""
工具函数模块
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def compute_sha256_hash(content: str) -> str:
    """
    计算内容的 SHA256 hash

    Args:
        content: 要计算 hash 的内容

    Returns:
        SHA256 hash 字符串
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def load_json(file_path: str) -> Optional[dict]:
    """
    加载 JSON 文件

    Args:
        file_path: JSON 文件路径

    Returns:
        JSON 数据，失败返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_json(data: dict, file_path: str) -> bool:
    """
    保存数据到 JSON 文件

    Args:
        data: 要保存的数据
        file_path: 文件路径

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def ensure_directory(path: str) -> None:
    """
    确保目录存在

    Args:
        path: 目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def generate_id() -> str:
    """
    生成唯一 ID

    Returns:
        唯一 ID 字符串
    """
    import uuid
    return str(uuid.uuid4())


def format_date(date: datetime) -> str:
    """
    格式化日期

    Args:
        date: datetime 对象

    Returns:
        格式化的日期字符串 (YYYY-MM-DD)
    """
    return date.strftime('%Y-%m-%d')


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        datetime 对象
    """
    return datetime.strptime(date_str, '%Y-%m-%d')