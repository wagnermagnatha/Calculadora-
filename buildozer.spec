[app]
title = FII Calculator
package.name = fiicalc
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,txt
version = 0.1
requirements = python3,kivy,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_NETWORK_STATE
# (optional) specify the target sdk / ndk in the android section below if needed
# android.api = 30
# android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1