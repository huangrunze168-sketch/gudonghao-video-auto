@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\LLVM\bin\clang-cl.exe" /nologo /std:c++17 /EHsc /MD /O2 /D_CRT_SECURE_NO_WARNINGS /utf-8 C:\Users\Administrator\Documents\剪映\engine\native_export_windows.cpp /Fe:C:\Users\Administrator\Documents\剪映\work\guzhu-mingyun-v3\render\有一些瞬间_我在命运之外\native-export-helper.exe
