@echo off
mkdir bin 2>nul
cd bin
cmake.exe -G "Unix Makefiles" .. && make