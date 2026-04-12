[app]

title = Python Monitor
package.name = pythonmonitor
package.domain = org.xiaoliang
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 3.2

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.build_tools_version = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a

# 关键修复：使用系统 SDK，不让 buildozer 自己下载空壳 SDK
android.sdk_path = /usr/local/lib/android/sdk

[buildozer]

log_level = 2
warn_on_root = 0