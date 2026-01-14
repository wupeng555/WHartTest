import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from projects.models import Project


class AutomationScript(models.Model):
    """自动化脚本模型"""
    
    SCRIPT_TYPE_CHOICES = [
        ('web', 'Web自动化'),
        ('android', 'Android自动化'),
        ('ios', 'iOS自动化'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('generated', '已生成'),
        ('ready', '就绪'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '执行失败'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='automation_scripts')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_scripts')
    
    # 基本信息
    name = models.CharField(max_length=200, verbose_name='脚本名称')
    description = models.TextField(blank=True, verbose_name='脚本描述')
    script_type = models.CharField(max_length=20, choices=SCRIPT_TYPE_CHOICES, verbose_name='脚本类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    
    # 测试用例内容
    test_cases_content = models.TextField(verbose_name='测试用例内容')
    
    # 生成的YAML脚本
    yaml_content = models.TextField(blank=True, verbose_name='YAML脚本内容')
    
    # 配置信息
    target_url = models.URLField(blank=True, verbose_name='目标URL')
    viewport_width = models.IntegerField(default=1280, verbose_name='视口宽度')
    viewport_height = models.IntegerField(default=960, verbose_name='视口高度')
    
    # AI配置
    ai_model = models.CharField(max_length=50, default='qwen-turbo', verbose_name='AI模型')
    api_key = models.CharField(max_length=500, blank=True, verbose_name='API密钥')
    api_endpoint = models.URLField(blank=True, verbose_name='API端点')
    
    # 执行配置
    execution_timeout = models.IntegerField(default=300, verbose_name='执行超时时间(秒)')
    retry_count = models.IntegerField(default=1, verbose_name='重试次数')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name='生成时间')
    
    class Meta:
        db_table = 'automation_scripts'
        verbose_name = '自动化脚本'
        verbose_name_plural = '自动化脚本'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_script_type_display()})"


class ScriptExecution(models.Model):
    """脚本执行记录"""
    
    STATUS_CHOICES = [
        ('pending', '等待执行'),
        ('running', '执行中'),
        ('completed', '执行完成'),
        ('failed', '执行失败'),
        ('cancelled', '已取消'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    script = models.ForeignKey(AutomationScript, on_delete=models.CASCADE, related_name='executions')
    executor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='script_executions')
    
    # 执行信息
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='执行状态')
    execution_id = models.CharField(max_length=100, unique=True, verbose_name='执行ID')
    
    # 执行结果
    exit_code = models.IntegerField(null=True, blank=True, verbose_name='退出码')
    stdout = models.TextField(blank=True, verbose_name='标准输出')
    stderr = models.TextField(blank=True, verbose_name='错误输出')
    
    # 报告文件
    report_path = models.CharField(max_length=500, blank=True, verbose_name='报告路径')
    report_url = models.URLField(blank=True, verbose_name='报告URL')
    
    # 统计信息
    total_tests = models.IntegerField(default=0, verbose_name='总测试数')
    passed_tests = models.IntegerField(default=0, verbose_name='通过测试数')
    failed_tests = models.IntegerField(default=0, verbose_name='失败测试数')
    execution_time = models.FloatField(null=True, blank=True, verbose_name='执行时间(秒)')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    class Meta:
        db_table = 'script_executions'
        verbose_name = '脚本执行记录'
        verbose_name_plural = '脚本执行记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.script.name} - {self.execution_id}"


class ExecutionLog(models.Model):
    """执行日志"""
    
    LOG_LEVEL_CHOICES = [
        ('debug', 'DEBUG'),
        ('info', 'INFO'),
        ('warning', 'WARNING'),
        ('error', 'ERROR'),
        ('critical', 'CRITICAL'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(ScriptExecution, on_delete=models.CASCADE, related_name='logs')
    
    # 日志信息
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, verbose_name='日志级别')
    message = models.TextField(verbose_name='日志消息')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')
    
    # 额外信息
    step_name = models.CharField(max_length=200, blank=True, verbose_name='步骤名称')
    screenshot_path = models.CharField(max_length=500, blank=True, verbose_name='截图路径')
    
    class Meta:
        db_table = 'execution_logs'
        verbose_name = '执行日志'
        verbose_name_plural = '执行日志'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.execution.execution_id} - {self.level}: {self.message[:50]}"


class ScriptTemplate(models.Model):
    """脚本模板"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('web_login', 'Web登录模板'),
        ('web_form', 'Web表单模板'),
        ('web_navigation', 'Web导航模板'),
        ('android_app', 'Android应用模板'),
        ('ios_app', 'iOS应用模板'),
        ('custom', '自定义模板'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='script_templates')
    
    # 模板信息
    name = models.CharField(max_length=200, verbose_name='模板名称')
    description = models.TextField(blank=True, verbose_name='模板描述')
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, verbose_name='模板类型')
    
    # 模板内容
    yaml_template = models.TextField(verbose_name='YAML模板内容')
    test_case_template = models.TextField(blank=True, verbose_name='测试用例模板')
    
    # 配置
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    is_default = models.BooleanField(default=False, verbose_name='是否默认模板')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'script_templates'
        verbose_name = '脚本模板'
        verbose_name_plural = '脚本模板'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"