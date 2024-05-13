@echo off
md build\windows\x64\bin
call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
cl /std:c11 /Z7 /Gy /MD /I. /Iinclude /DBUILD_SYSBVM_STATIC /W4 /wd4146 /wd4702 /wd4152 /wd4201 /Febuild\windows\x64\bin\sdvm sdvm\sdvm-unity.c

REM md build\windows\x86\bin
REM call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x86
REM cl /std:c11 /Z7 /O2 /Gy /MD /I. /Iinclude  /DBUILD_SYSBVM_STATIC /W4 /wd4146 /wd4702 /wd4152 /wd4201 /Febuild\windows\x86\bin\sdvm sdvm\sdvm-unity.c
