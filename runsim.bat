set MYIP=169.254.149.37
set PATH=C:\programs\tools\nircmd;%PATH%

:restart

echo restarting

nircmdc.exe sendkey 1 press
nircmdc.exe sendkey 2 press
nircmdc.exe sendkey 3 press
nircmdc.exe sendkey enter press
ssh -X knoppix@knoppix killall -9 server
rem pause


nircmdc.exe sendkey 1 press
nircmdc.exe sendkey 2 press
nircmdc.exe sendkey 3 press
nircmdc.exe sendkey enter press
rem ssh -X knoppix@knoppix export DISPLAY=%MYIP%:0.0;/media/hda1/2008/sim/lo-res/server -v /media/hda1/2008/sim/sample-maps/%1
rem ssh -X knoppix@knoppix export DISPLAY=%MYIP%:0.0;/media/hda1/2008/sim/linux2.6.24/server -v -p 17676 /media/hda1/2008/sim/sample-maps/%1
ssh -X knoppix@knoppix export DISPLAY=%MYIP%:0.0;/media/hda1/2008/sim/livecd/server -v -p 17676 /media/hda1/2008/sim/sample-maps/%1

exit

rem goto restart