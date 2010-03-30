@echo off

rem py2exe build script

echo pre-build cleaning...
rd /S /Q bin 2>nul
rd /S /Q src\dist 2>nul

echo creating the executable...
cd src
C:\Python26\python.exe -OO setup.py py2exe

echo post-build actions...
del /Q dist\w9xpopen.exe
move dist ..\bin
cd ..
