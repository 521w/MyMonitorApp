"""全局主题 - 微信风格深色"""
import json
import os

# ============ 微信绿主色调 ============
ACCENT = (0.027, 0.757, 0.376, 1)
ACCENT_HEX = "07C160"

# ============ 背景色 ============
BG_DARK = (0.07, 0.07, 0.09, 1)
BG_CARD = (0.12, 0.12, 0.16, 0.88)
BG_INPUT = (0.15, 0.15, 0.19, 0.9)
BG_NAV = (0.05, 0.05, 0.07, 0.95)

# ============ 状态色 RGBA ============
GREEN = (0.1, 0.9, 0.31, 1)
YELLOW = (1, 0.8, 0, 1)
RED = (1, 0.3, 0.3, 1)
PURPLE = (0.7, 0.4, 1, 1)

# ============ 状态色 HEX (markup) ============
GREEN_HEX = "1AE650"
YELLOW_HEX = "FFCC00"
RED_HEX = "FF4D4D"
PURPLE_HEX = "B266FF"

# ============ 按钮色 ============
BTN_PRIMARY = (0.027, 0.757, 0.376, 1)
BTN_SUCCESS = (0.1, 0.9, 0.31, 1)
BTN_DANGER = (1, 0.3, 0.3, 1)
BTN_NEUTRAL = (0.25, 0.25, 0.3, 0.9)
BTN_WARN = (1, 0.7, 0, 1)

# ============ 文字色 ============
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_DIM = (0.55, 0.55, 0.6, 1)

# ============ 分割线 ============
DIVIDER = (0.2, 0.2, 0.24, 0.6)

# ============ 字体大小 ============
FONT_XL = "20sp"
FONT_LG = "16sp"
FONT_MD = "14sp"
FONT_SM = "12sp"
FONT_XS = "10sp"

# ============ 圆角 ============
RADIUS_LG = [16]
RADIUS_MD = [10]
RADIUS_SM = [6]

# ============ 背景预设 ============
BG_PRESETS = {
    "深邃黑": (0.07, 0.07, 0.09, 1),
    "微信墨绿": (0.05, 0.09, 0.07, 1),
    "深海蓝": (0.04, 0.06, 0.12, 1),
    "暗紫": (0.08, 0.05, 0.12, 1),
    "碳灰": (0.12, 0.12, 0.12, 1),
    "午夜": (0.02, 0.02, 0.05, 1),
    "森林": (0.04, 0.08, 0.04, 1),
    "暖棕": (0.1, 0.07, 0.05, 1),
}

# ============ 配置持久化 ============
CONFIG_PATH = "/sdcard/pm_config.json"


def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f)
    except Exception:
        pass