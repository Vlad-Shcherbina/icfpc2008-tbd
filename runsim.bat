set MYIP=169.254.149.37

:restart

rem ssh -X knoppix@knoppix killall -9 server

ssh -X knoppix@knoppix export DISPLAY=%MYIP%:0.0;/media/hda1/2008/sim/lo-res/server -v /media/hda1/2008/sim/sample-maps/simple-small.wrld
pause

goto restart