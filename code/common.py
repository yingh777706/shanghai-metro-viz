# -*- coding: utf-8 -*-
"""项目公共工具：统一的数据文件定位与项目根目录。

所有分工脚本应 import 本模块，避免各自复制一份 find_data 导致路径约定漂移。

数据文件查找顺序（存在即返回）：
  1. 环境变量 METRO_DATA_DIR 指定的目录（若设置，优先级最高）
  2. <项目根>/data
  3. <项目根>/processed_data
  4. <项目根>/docs/processed_data
  5. <项目根>/docs/data
"""

import os
from pathlib import Path

# 项目根目录：本文件位于 code/ 下，其父目录即项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 数据文件可能存放的目录（按优先级查找，本地与仓库通用）
CANDIDATE_DIRS = (
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "processed_data",
    PROJECT_ROOT / "docs" / "processed_data",
    PROJECT_ROOT / "docs" / "data",
)


def find_data(name: str) -> Path:
    """在候选目录中查找数据文件，返回第一个存在的路径。

    找不到时抛出 FileNotFoundError，并列出所有已搜索的路径，
    便于使用者直接看到应把文件放到哪里。
    """
    dirs = CANDIDATE_DIRS
    override = os.environ.get("METRO_DATA_DIR")
    if override:
        dirs = (Path(override),) + dirs

    for d in dirs:
        p = d / name
        if p.exists():
            return p

    searched = "\n  - ".join(str(d / name) for d in dirs)
    raise FileNotFoundError(
        f"未找到数据文件 {name!r}，已搜索以下路径：\n  - {searched}\n"
        f"请将数据放入上述任一目录，或设置环境变量 METRO_DATA_DIR 指向数据目录。"
    )
