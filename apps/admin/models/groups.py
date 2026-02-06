#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tortoise import fields, models


class Group(models.Model):
    id = fields.IntField(pk=True)

    name = fields.CharField(max_length=150, null=True)
    default = fields.BooleanField(default=False, null=False, description="是否默认分配权限")

    users = fields.ManyToManyField(
        'models.User',
        related_name="groups",
        null=True,
        on_delete=fields.SET_NULL,
    )

    comment = fields.TextField(description="描述")

    create_date = fields.DatetimeField(auto_now_add=True, description="创建时间")
    write_date = fields.DatetimeField(auto_now=True, description="最后更新时间")

    class Meta:
        table = 'groups'
        table_description = "用户组权限表"
