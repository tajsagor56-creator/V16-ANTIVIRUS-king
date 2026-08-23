[app]

# ============================================================
# V16 ANTIVIRUS PRO
# ============================================================

title = V16 Antivirus Pro
package.name = v16antivirus
package.domain = org.kingtaj

source.dir = .
source.include_exts = py,json,png,jpg,jpeg,kv,atlas

version = 16.2

orientation = portrait
fullscreen = 0

# ============================================================
# PYTHON / KIVY REQUIREMENTS
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
# PYTHON-FOR-ANDROID
# ============================================================

p4a.branch = master

# ============================================================
# PERMISSIONS
# ============================================================

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,POST_NOTIFICATIONS

# ============================================================
# SDK LICENSE
# ============================================================

android.accept_sdk_license = True

# ============================================================
# STORAGE / BACKUP
# ============================================================

android.private_storage = True
android.allow_backup = False


[buildozer]

log_level = 2
warn_on_root = 1
