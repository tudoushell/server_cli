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
    # 先判断是否存在PID文件，如果有，检测服务是否存在
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    jar_file_path, jar_parent_path = config_loader.get_full_jar_path(config_info)
    path = Path(jar_parent_path)
    files = [file for file in path.iterdir() if file.is_file() and file.name.lower().endswith('.pid')]
    if len(files) == 0:
        # 没有pid文件则通过服务器心跳检测和ps -ef 去判断服务是否存在，存在，写入pid文件(没有pid文件)
        if config_info.health_url and server_is_online(config_info.health_url):
            console.print(f"{config_info.jar_name}服务已启动", style='bold yellow')
            return
        else:
            pid = get_pid_by_server_name(config_info.jar_name)
            if pid > -1:
                write_pid(pid, jar_parent_path)
    else:
        for file in files:
            with open(file, 'r') as pid_file:
                pid = pid_file.read()
                if not pid:
                    continue
                if is_running(int(pid)):
                    console.print(f"服务已启动，pid: {pid}", style='bold yellow')
                    return

    if not os.path.isfile(jar_file_path):
        console.print(f"启动失败 {jar_file_path} 不存在", style='bold red')
        return
    # 不存在则启动



@app.command()
def stop():
    """
    停止服务
    """
    pass


@app.command()
def detail():
    """
    显示服务信息
    """
    pass


@app.command()
def log():
    """
    查看日志
    """


def start_server(jar_file_path:str, config_info: config_loader.ConfigInfo):

    pass


def write_pid(pid: int, jar_parent_path: str):
    # 写入pid文件
    with open(os.path.join(jar_parent_path, SERVER_PID_FILE), 'w') as pid_file:
        pid_file.write(str(pid))


def server_is_online(health_url: str) -> bool:
    try:
        res = requests.get(health_url, timeout=3)
        return res.status_code == 200
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.RequestException:
        return False


def get_pid_by_server_name(service_name: str) -> int:
    """
     获取服务PID
    :param service_name: 服务名
    :return: 进程ID
    """
    sub_process = subprocess.run(f"ps -ef|grep {service_name}",
                                 shell=True, stdout=subprocess.PIPE, text=True)
    for line in sub_process.stdout.splitlines():
        if f"{service_name}" in line and "grep" not in line:
            return int(line.split()[1])
    return -1


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


if __name__ == '__main__':
    app()
