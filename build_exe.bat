@echo off
echo 正在编译文件夹清理工具...
echo.

REM 清理之前的构建文件
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "folder_cleaner.spec" del "folder_cleaner.spec"

echo 开始编译...
pyinstaller --onefile --windowed --name=FolderCleaner folder_cleaner.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 编译成功！
    echo 📁 可执行文件位置: dist\FolderCleaner.exe
    echo.
    echo 正在打开dist文件夹...
    explorer dist
) else (
    echo.
    echo ❌ 编译失败！
    echo 请检查错误信息。
)

echo.
pause 