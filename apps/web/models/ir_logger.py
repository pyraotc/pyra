#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tortoise import fields, models


class IrLogger(models.Model):
    id = fields.IntField(pk=True)

    log_type = fields.CharField(
        max_length=10,
        description="日志类型",
        index=True
    )

    title = fields.CharField(
        max_length=200,
        description="日志标题",
        null=True
    )

    content = fields.TextField(
        description="日志详细内容",
        null=True
    )

    is_success = fields.BooleanField(
        default=True,
        description="操作是否成功"
    )

    error_message = fields.TextField(
        default=None,
        description="错误信息（如果操作失败）",
        null=True
    )

    ip_address = fields.CharField(
        default=None,
        max_length=45,  # IPv6最大长度
        description="操作IP地址",
        null=True
    )

    user_agent = fields.TextField(
        default=None,
        description="用户代理（浏览器信息）",
        null=True
    )

    # 其他信息
    metadata = fields.JSONField(
        description="其他元数据",
        null=True
    )

    create_date = fields.DatetimeField(auto_now_add=True, description="创建时间")
    write_date = fields.DatetimeField(auto_now=True, description="最后更新时间")

    class Meta:
        table = 'ir_logger'
        table_description = "前台日志表"
