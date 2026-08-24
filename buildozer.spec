[app]

title = V16 Antivirus Pro
package.name = v16antivirus
package.domain = org.kingtaj

source.dir = .
source.include_exts = py

version = 16.3

orientation = portrait
fullscreen = 0

requirements = python3,kivy

android.api = 35
android.minapi = 24

android.ndk = 28c
android.ndk_api = 24

android.archs = arm64-v8a

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.private_storage = True
android.allow_backup = False

android.accept_sdk_license = True


[buildozer]

log_level = 2
warn_on_root = 1
