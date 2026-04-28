# encoding: utf-8

import typer
import os
import config_loader
from rich.console import Console

console = Console()
app = typer.Typer(
    help="Java 服务管理工具 —— 解压、启动、监控、停止",
    add_completion=False,
    rich_markup_mode="rich",
)


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
    if config_loader.server_is_online_by_pid_file(config_info, jar_parent_path):
        return
    if not os.path.isfile(jar_file_path):
        console.print(f"启动失败 {jar_file_path} 不存在", style='bold red')
        return
    config_loader.run_server(config_info, jar_parent_path)


@app.command()
def restart():
    """
    重启服务
    """
    pass


@app.command()
def stop():
    """
    停止服务
    """

    pass


@app.command()
def status():
    """
    显示服务状态
    """
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    jar_file_path, jar_parent_path = config_loader.get_full_jar_path(config_info)
    pid = config_loader.read_pid_file(jar_parent_path, config_info.jar_name)
    server_is_running = config_loader.is_running(pid)
    if  config_info.health_url:
        is_online = config_loader.server_is_online(config_info.health_url)
        server_status = "ONLINE" if is_online and server_is_running else "OFFLINE"
    else:
        server_status = "ONLINE" if server_is_running else "OFFLINE"
    config_loader.print_server_status(config_info.jar_name, pid, server_status)


@app.command()
def log():
    """
    查看日志
    """


if __name__ == '__main__':
    app()
