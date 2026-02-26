#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tortoise import fields, models
from mimesis import Person


class User(models.Model):
    id = fields.IntField(pk=True)

    email = fields.CharField(max_length=150, unique=True, null=False, index=True, description="登录邮箱")
    phone = fields.BigIntField(null=True, unique=True, index=True, description="手机号")
    password = fields.CharField(max_length=150, null=False, description="登录密码")

    name = fields.CharField(max_length=128, default=Person().name(), null=True, description="姓名")

    active = fields.BooleanField(default=True, description="激活状态")
    superuser = fields.BooleanField(default=False, description="超级用户")
    is_update_password = fields.BooleanField(default=False, description="是否需要修改密码")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")

    create_date = fields.DatetimeField(auto_now_add=True, description="创建时间")
    write_date = fields.DatetimeField(auto_now=True, description="最后更新时间")

    class Meta:
        table = 'users'
        table_description = "用户表"
