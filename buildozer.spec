[app]

title = Cloud Calculator
package.name = cloudcalculator
package.domain = org.mono
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

[buildozer]

log_level = 2
warn_on_root = 1

[android]

android.permissions = INTERNET
android.api = 35
android.minapi = 23
