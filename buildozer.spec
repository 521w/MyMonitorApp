[app]

title = Python Monitor
package.name = pythonmonitor
package.domain = org.xiaoliang
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
version = 3.4

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,READ_PHONE_STATE,READ_LOGS,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,BATTERY_STATS,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,CAMERA

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.build_tools_version = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a

android.sdk_path = /usr/local/lib/android/sdk

[buildozer]

log_level = 2
warn_on_root = 0