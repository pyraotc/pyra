#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tortoise import fields, models


class IrAgentCategory(models.Model):
    id = fields.IntField(pk=True)

    name = fields.CharField(max_length=255, null=False, description="分类名称")
    sequence = fields.IntField(null=False, default=0, description="排序字段")

    groups = fields.ManyToManyField(
        "models.Group",
        related_name="groups_category",
        null=True,
        on_delete=fields.SET_NULL,
        description="权限组"
    )
    create_date = fields.DatetimeField(auto_now_add=True, description="创建时间")
    write_date = fields.DatetimeField(auto_now=True, description="最后更新时间")

    class Meta:
        table = 'ir_agents_category'
        table_description = "智能体分类表"
