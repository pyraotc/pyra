#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core.servers.command import execute_from_command

app, host, port, debug, workers = execute_from_command()
