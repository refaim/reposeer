@echo off
rd /S /Q bin 2>nul
rd /S /Q src\dist 2>nul
rd /S /Q src\build 2>nul
del /S /Q src\*.pyc 2>nul >nul
del /Q *~ .gedit* *.swp 2>nul >nul
