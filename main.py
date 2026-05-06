# encoding: utf-8
import shlex
import subprocess
from typing import Optional

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
def deploy(
        package: str = typer.Option(None, "--package", "-p", help="指定服务程序压缩包路径"),
        jar: str = typer.Option(None, "--jar", "-j", help="服务名称（默认取包名）"),
        jvm_opts: Optional[str] = typer.Option(None, "--jvm", help="指定JVM参数,如 '-Xmx512m'")
):
    """
    解压指定的服务程序
    """
    # 获取配置文件信息
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        if not package or not os.path.isfile(package):
            console.print(f"服务程序压缩包不存在{package}")
            return
        shell_args = []
        if jvm_opts:
            shell_args = shlex.split(jvm_opts)
        config_info = config_loader.ConfigInfo(package, jar, shell_args, is_exists_config=True)
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
    pid = config_loader.get_pid_by_pid_file(jar_parent_path)
    if pid == -1:
        pid = config_loader.get_pid_by_pid_jar_path(jar_file_path)
    if pid > -1:
        config_loader.write_pid(pid, jar_parent_path)
        if config_info.health_url:
            if config_loader.server_is_online_by_health_url(config_info):
                console.print(f"{config_info.jar_name}服务已启动，pid: {pid}", style='bold yellow')
            else:
                console.print(f"{config_info.jar_name}进程存在但健康检查未通过，pid: {pid}", style='bold yellow')
        else:
            console.print(f"{config_info.jar_name}进程已存在，pid: {pid}", style='bold yellow')
        return
    if config_info.health_url and config_loader.server_is_online_by_health_url(config_info):
        console.print(f"{config_info.jar_name}健康检查已通过，但未找到进程PID，跳过启动", style='bold yellow')
        return
    if not os.path.isfile(jar_file_path):
        console.print(f"启动失败 {jar_file_path} 不存在", style='bold red')
        return
    config_loader.run_server(config_info, jar_parent_path)


@app.command()
def restart(
        force: bool = typer.Option(False, "--force", "-f", help="强制停止后重启服务")
):
    """
    重启服务
    """
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    jar_file_path, jar_parent_path = config_loader.get_full_jar_path(config_info)
    pid = config_loader.get_pid_by_pid_file(jar_parent_path)
    if pid == -1:
        pid = config_loader.get_pid_by_pid_jar_path(jar_file_path)
    if pid > -1:
        config_loader.kill_server(pid, config_info.jar_name, jar_parent_path, force)
    else:
        console.print(f"{config_info.jar_name} 未启动，直接启动服务", style='bold yellow')
    if not os.path.isfile(jar_file_path):
        console.print(f"启动失败 {jar_file_path} 不存在", style='bold red')
        return
    config_loader.run_server(config_info, jar_parent_path)


@app.command()
def stop(
        force: bool = typer.Option(False, "--force", "-f", help="强制停止服务")
):
    """
    停止服务
    """
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    # 查看PID文件
    jar_file_path, jar_parent_path = config_loader.get_full_jar_path(config_info)
    pid = config_loader.get_pid_by_pid_file(jar_parent_path)
    if pid == -1:
        pid = config_loader.get_pid_by_pid_jar_path(jar_file_path)
    if pid > -1:
        config_loader.kill_server(pid, config_info.jar_name, jar_parent_path, force)
        config_loader.print_server_status(config_info.jar_name, pid, "OFFLINE")
    else:
        console.print(f"{config_info.jar_name} 未启动", style='bold yellow')


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
    if config_info.health_url:
        is_online = config_loader.server_is_online(config_info.health_url)
        server_status = "ONLINE" if is_online and server_is_running else "OFFLINE"
    else:
        server_status = "ONLINE" if server_is_running else "OFFLINE"
    config_loader.print_server_status(config_info.jar_name, pid, server_status)


@app.command()
def log(
        log_file: str = typer.Option(None, "--log-file", "-f", help="指定日志文件路径"),
        line: int = typer.Option(100, "--n", "-n", help="指定日志行数")
):
    """
    查看日志
    """
    if not log_file:
        console.print("未指定日志文件路径", style='bold yellow')
        return
    config_info = config_loader.get_config_info()
    if not config_info.is_exists_config:
        return
    jar_file_path, jar_parent_path = config_loader.get_full_jar_path(config_info)
    log_file_path = os.path.join(jar_parent_path, log_file)
    if os.path.exists(log_file):
        log_file_path = log_file
    elif not os.path.exists(log_file_path):
        console.print(f"日志文件 {log_file_path} 不存在", style='bold yellow')
        return
    subprocess.run(["tail", "-f", "-n", str(line), log_file_path])


if __name__ == '__main__':
    app()
