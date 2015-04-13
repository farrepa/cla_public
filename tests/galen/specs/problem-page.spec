=====================================
header          #global-header
header-bar      #global-header-bar
footer          #footer
=====================================

@ *
--------------------

header-bar
  below: header 0px


@ desktop
--------------------

header
  inside: screen 0px left right
  height: 53px

footer
  inside: screen 0px bottom left right
  height: 271px


@ mobile
--------------------

header
  inside: screen 0px left right
  height: 84px
