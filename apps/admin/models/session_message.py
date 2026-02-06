#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tortoise import fields, models


class SessionMessage(models.Model):
    id = fields.IntField(pk=True, description="ID")

    session_id = fields.CharField(null=True, max_length=255, description="Session ID")
    tag = fields.CharField(null=False, max_length=255, unique=True, description="Tag")

    name = fields.CharField(null=True, max_length=255, description="Session name")
    type = fields.CharField(null=True, max_length=20, choice=["ai", "human"], description="Type")
    content = fields.TextField(null=True, description="message")

    think = fields.TextField(null=True, description="think")
    message = fields.TextField(null=True, description="message")

    additional_kwargs = fields.JSONField(null=True, description="additional kwargs")
    response_metadata = fields.JSONField(null=True, description="response metadata")

    metadata = fields.JSONField(null=True, description="元数据")

    files = fields.JSONField(null=True, description="文件信息")

    class Meta:
        table = 'session_messages'
        table_description = "session 消息内容"
