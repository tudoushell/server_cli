import time
from pathlib import Path
import os
import subprocess
import socket
from subprocess import DEVNULL
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import config_loader
def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False

# console = Console()
#
# table = Table(show_header=True, title="Service Status", title_style="red")
# table.add_column("PID", justify="right")
# table.add_column("Name")
# table.add_column("Status")
#
# table.add_row("1", "sshd", "running")
# console.print(table)



# path = Path.home() / "project/python-project/server_cli"
#
# for name in path.iterdir():
#     if name.is_dir() and name.name.startswith("."):
#         print(name.name)
#
# print('-------')
# sub = subprocess.Popen(["java", "-jar", "assistant-server-1.0.jar"], cwd="/Users/elliotk/tmp/assistant", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
# time.sleep(5)
# stout,_ = sub.communicate()
# pid = sub.pid
# print(f'----------> pid {sub.pid}')
#
# if not is_running(int(pid)):
#     print(f'stout {stout}')


print(os.path.basename('/Users/elliotk/tmp'))

# sub_process = subprocess.run("ps -ef|grep assistant-server-1.0.jar", shell=True, stdout=subprocess.PIPE, text=True)
#
# for line in sub_process.stdout.splitlines():
#     if "assistant-server-1.0.jar" in line and "grep" not in line:
#         print(line.split()[1])


# with socket.socket(socket.AF_INET, socket.SocketKind.SOCK_STREAM) as sock:
#     sock.settimeout(2)
#     result = sock.connect_ex(('127.0.0.1', 8083))
#     print(result)
