#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tortoise import fields, models
from datetime import datetime


class SessionMetaDat(models.Model):
    id = fields.IntField(pk=True, description="ID")

    session_id = fields.CharField(max_length=255, unique=True, description="Session ID")
    model_name = fields.CharField(max_length=50, description="Model name")
    abstract = fields.CharField(max_length=150, description="摘要")
    metadata = fields.JSONField(null=True, description="元数据")

    agent = fields.ForeignKeyField(
        "models.IrAgents",
        related_name="session_metadats",
        null=True,
        on_delete=fields.SET_NULL,
        description="Agent"
    )

    last_activity = fields.DatetimeField(default=datetime.now, null=True, description="最后更新时间")

    create_user = fields.ForeignKeyField(
        "models.User",
        related_name="c_session_metadata",
        null=True,
        on_delete=fields.SET_NULL,
        description="创建用户")
    write_user = fields.ForeignKeyField(
        "models.User",
        related_name="w_session_metadata",
        null=True,
        on_delete=fields.SET_NULL,
        description="最后更新用户"
    )

    create_date = fields.DatetimeField(auto_now_add=True, description="创建时间")
    write_date = fields.DatetimeField(auto_now=True, description="最后更新时间")

    class Meta:
        table = 'session_metadata'
        table_description = "session 元数据表"
