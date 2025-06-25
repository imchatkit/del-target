@echo off
echo 正在清理编译临时文件...

if exist "build" (
    echo 删除 build 文件夹...
    rmdir /s /q "build"
)

if exist "FolderCleaner.spec" (
    echo 删除 spec 文件...
    del "FolderCleaner.spec"
)

if exist "__pycache__" (
    echo 删除 __pycache__ 文件夹...
    rmdir /s /q "__pycache__"
)

echo 清理完成！
echo 保留的文件：
echo - dist\FolderCleaner.exe (可执行文件)
echo - folder_cleaner.py (源代码)
echo - README.md (详细说明)
echo - EXE使用说明.md (EXE版本说明)

pause 