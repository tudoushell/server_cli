# encoding: utf-8

import typer
import os
import shutil
import config_loader
import traceback
import subprocess
import requests
from pathlib import Path
from rich.console import Console
from rich.table import Column, Table

console = Console()
app = typer.Typer(
    help="Java 服务管理工具 —— 解压、启动、监控、停止",
    add_completion=False,
    rich_markup_mode="rich",
)
CONFIG_JSON_FILE = 'config.json'
SERVER_PID_FILE = 'java_server.pid'


@app.command()
def deploy():
    """
    解压指定的服务程序
    """
    # 获取配置文件信息
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    # 解压压缩包
    is_unpack_success = config_loader.unpack_server_package_check(config_info)
    if not is_unpack_success:
        return


@app.command()
def start():
    """
    启动服务
    """
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    jar_file_path, jar_parent_path = config_loader.get_full_jar_path(config_info)
    pid = config_loader.get_pid_by_server_name(config_info.jar_name)
    if pid > -1:
        config_loader.write_pid(pid, jar_parent_path)
        console.print(f"{config_info.jar_name}服务已启动", style='bold yellow')
        return
    if not config_loader.server_is_online_by_pid_file(config_info, jar_parent_path, jar_file_path):
        return
    config_loader.run_server(config_info, jar_parent_path)


@app.command()
def stop():
    """
    停止服务
    """
    pass


@app.command()
def status():
    """
    显示服务信息
    """
    pass


@app.command()
def log():
    """
    查看日志
    """


if __name__ == '__main__':
    app()
