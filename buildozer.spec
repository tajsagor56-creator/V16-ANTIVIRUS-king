[app]

# ==========================================
# অ্যাপের নাম
# ==========================================
title = V16 Antivirus Pro

# ==========================================
# Android package নাম
# ==========================================
package.name = v16antivirus
package.domain = org.kingtaj

# ==========================================
# Source directory
# ==========================================
source.dir = .

# ==========================================
# APK-তে যেসব ফাইল যাবে
# ==========================================
source.include_exts = py,json,png,jpg,jpeg,kv,atlas

# ==========================================
# অ্যাপের version
# ==========================================
version = 16.2

# ==========================================
# স্ক্রিন সেটিং
# ==========================================
orientation = portrait
fullscreen = 0

# ==========================================
# Python এবং Kivy dependency
# ==========================================
requirements = python3,kivy,plyer

# ==========================================
# Android Permission
# ==========================================
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,POST_NOTIFICATIONS

# ==========================================
# Android API
# ==========================================
android.api = 35
android.minapi = 23

# ==========================================
# CPU Architecture
# ==========================================
android.archs = arm64-v8a,armeabi-v7a

# ==========================================
# Android storage
# ==========================================
android.private_storage = True
android.allow_backup = False

# ==========================================
# Network security
# ==========================================
android.uses_cleartext_connection = False


[buildozer]

# ==========================================
# Buildozer log level
# ==========================================
log_level = 2
