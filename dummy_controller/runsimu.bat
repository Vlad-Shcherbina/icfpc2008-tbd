rem set KNOPPIX 169.254.149.38
set KNOPPIX=knoppix

start ..\runsim.bat
@sleep 1

dummy_controller.py %KNOPPIX% 17676
rem >log_knoppix 2>log_knoppix_err
