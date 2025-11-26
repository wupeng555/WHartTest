"""
ASGI config for wharttest_django project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# 设置 umask 确保新建文件有正确的权限（664 文件，775 目录）
os.umask(0o002)

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wharttest_django.settings')

application = get_asgi_application()
