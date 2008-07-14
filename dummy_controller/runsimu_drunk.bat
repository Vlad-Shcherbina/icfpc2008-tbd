rem set KNOPPIX 169.254.149.38
set KNOPPIX=knoppix

rem set CONTROLLER=stack_controller.py
rem set CONTROLLER=keyboard_controller.py
set CONTROLLER=drunk_controller.py
rem set CONTROLLER=rail_controller.py


rem simple-small.wrld
rem small-scatter.wrld
rem spiral.wrld
rem empty.wrld
rem empty1min.wrld
rem empty2s.wrld
rem empty30s.wrld
rem small-scatter-slowrot.wrld
rem map_rotAccel40_500_c10_b10_r4_e50.wrld

start ..\runsim.bat map_empty_1500_c20_b60_r8_e4.wrld
@sleep 2

python -OO %CONTROLLER% %KNOPPIX% 17676 
rem >log_knoppix 2>log_knoppix_err
pause