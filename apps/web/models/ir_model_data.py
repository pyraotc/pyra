#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tortoise import fields, models


class IrModelData(models.Model):
    id = fields.IntField(pk=True)

    module = fields.CharField(max_length=255, description="模块名称")
    name = fields.CharField(max_length=255, description="XML ID 名称")
    complete_name = fields.CharField(
        max_length=255,
        unique=True,
        description="完整的 XML ID"
    )

    model = fields.CharField(max_length=255, description="关联的数据表")
    ref_id = fields.IntField(description="记录ID")

    create_date = fields.DatetimeField(auto_now_add=True, description="创建时间")
    write_date = fields.DatetimeField(auto_now=True, description="更新时间")
    noupdate = fields.BooleanField(default=False, description="更新时保留")

    data = fields.JSONField(null=True, description="附加数据")

    class Meta:
        table = "ir_model_data"
        unique_together = [("module", "name", "model")]
        table_description = "Ir Model Data"

    def __str__(self) -> str:
        """获取字符串表示"""
        return f"{self.complete_name} -> {self.model}:{self.ref_id}"
