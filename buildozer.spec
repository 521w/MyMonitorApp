[app]

title = Python Monitor
package.name = pythonmonitor
package.domain = org.xiaoliang
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

# API 33 必须用 MANAGE_EXTERNAL_STORAGE
android.permissions = MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# 锁定 build-tools（最后一个包含 aidl 的版本）
android.build_tools_version = 33.0.2

# CI 自动接受许可证
android.accept_sdk_license = True

android.archs = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 0