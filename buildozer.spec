[app]

title = V16 Antivirus Pro
package.name = v16antivirus
package.domain = org.kingtaj

source.dir = .
source.include_exts = py

version = 16.4

orientation = portrait
fullscreen = 0

# ============================================================
# REQUIREMENTS
# ============================================================

requirements = python3,kivy

# ============================================================
# ANDROID
# ============================================================

android.api = 35
android.minapi = 24

android.ndk = 28c
android.ndk_api = 24

android.archs = arm64-v8a,armeabi-v7a

# ============================================================
# PERMISSIONS
# ============================================================

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,POST_NOTIFICATIONS

# ============================================================
# STORAGE
# ============================================================

android.private_storage = True
android.allow_backup = False

# ============================================================
# SDK
# ============================================================

android.accept_sdk_license = True

# ============================================================
# PYTHON-FOR-ANDROID
# ============================================================

p4a.fork = kivy
p4a.branch = master


[buildozer]

log_level = 2
warn_on_root = 1
