@echo off
mkdir bin 2>nul
cd bin
cmake -G "Unix Makefiles" .. && make