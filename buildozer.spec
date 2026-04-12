[app]

title = Python Monitor
package.name = pythonmonitor
package.domain = org.xiaoliang
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 3.3

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,READ_PHONE_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,WAKE_LOCK,SYSTEM_ALERT_WINDOW

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.build_tools_version = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a

# 使用系统 SDK
android.sdk_path = /usr/local/lib/android/sdk

[buildozer]

log_level = 2
warn_on_root = 0