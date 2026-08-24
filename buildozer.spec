[app]

title = V16 Antivirus Pro
package.name = v16antivirus
package.domain = org.kingtaj

source.dir = .
source.include_exts = py,json,png,jpg,jpeg,kv,atlas

version = 16.2

orientation = portrait
fullscreen = 0

# ============================================================
# REQUIREMENTS
# ============================================================

requirements = python3,kivy==2.3.1,charset-normalizer==3.3.2

# ============================================================
# ANDROID
# ============================================================

android.api = 35
android.minapi = 24

android.ndk = 28c
android.ndk_api = 24

android.archs = arm64-v8a

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


[buildozer]

log_level = 2
warn_on_root = 1
