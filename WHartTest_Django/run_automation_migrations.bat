@echo off
echo 正在创建自动化脚本应用的数据库迁移...

REM 激活虚拟环境（如果有的话）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM 创建迁移文件
python manage.py makemigrations automation_scripts

REM 应用迁移
python manage.py migrate

echo 数据库迁移完成！
pause