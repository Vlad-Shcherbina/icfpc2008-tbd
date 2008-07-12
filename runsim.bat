set MYIP=169.254.149.37
ssh -X knoppix@knoppix export DISPLAY=%MYIP%:0.0;/media/hda1/2008/sim/lo-res/server -v /media/hda1/2008/sim/sample-maps/simple-small.wrld
pause