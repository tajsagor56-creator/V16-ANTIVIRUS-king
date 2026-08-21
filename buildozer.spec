ini
[app]

title = V16 Antivirus Pro
package.name = v16antivirus
package.domain = org.kingtaj

source.dir = .

source.include_exts = py,json,png,jpg,jpeg,kv,atlas

version = 16.2

orientation = portrait
fullscreen = 0

requirements = python3,kivy,plyer

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,POST_NOTIFICATIONS

android.api = 33
android.minapi = 24
android.ndk = 25b

android.archs = arm64-v8a

android.private_storage = True
android.allow_backup = False
android.uses_cleartext_connection = False

# Buildozer যে SDK ব্যবহার করবে
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk

# Buildozer যে NDK ব্যবহার করবে
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r28c

android.accept_sdk_license = True


[buildozer]

log_level = 2
