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

android.api = 35
android.minapi = 24

android.ndk = 27.3.13750724

android.archs = arm64-v8a

android.private_storage = True
android.allow_backup = False
android.uses_cleartext_connection = False

[buildozer]

log_level = 2
