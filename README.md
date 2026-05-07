# server_cli

中文 | [English](#english)

## 中文

`server_cli` 是一个用于部署和管理 Java JAR 服务的 Python 命令行工具。当前主入口是 `main.py`，面向单服务管理场景，支持部署、启动、停止、重启、状态查看和日志查看。

CLI 基于 Typer 实现，终端输出使用 Rich。

## 功能概览

- 解压 Java 服务包。
- 启动指定 JAR。
- 使用 PID 文件记录服务进程。
- 支持按 PID 文件和 JAR 路径查找进程。
- 支持停止、强制停止、重启。
- 支持可选健康检查 URL。
- 支持查看日志文件最近 N 行和实时跟踪。
- 支持 `config.json` 配置文件，也支持部分命令直接传命令行参数。

## 环境要求

- Python 3.12 或兼容版本
- Java 运行环境
- macOS 或 Linux

## 安装

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

检查 CLI：

```bash
.venv/bin/python main.py --help
```

## 快速开始

使用配置文件：

```bash
.venv/bin/python main.py deploy
.venv/bin/python main.py start
.venv/bin/python main.py status
.venv/bin/python main.py stop
.venv/bin/python main.py restart
```

不使用配置文件，直接指定服务目录和 JAR：

```bash
.venv/bin/python main.py start --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py status --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py stop --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py restart --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

## 配置文件

`main.py` 会优先读取当前运行目录下的 `config.json`。

示例：

```json
{
  "package_file_path": "/Users/elliotk/tmp/assistant.zip",
  "jar_name": "assistant-server-1.0.jar",
  "jvm_args": ["-Xmx1g", "-Xms1024M"],
  "health_check_url": "http://127.0.0.1:8080/health"
}
```

字段说明：

- `package_file_path`：服务包路径。`deploy` 会解压它；其他命令会用它推导服务目录。
- `jar_name`：需要启动或管理的 JAR 文件名。
- `jvm_args`：JVM 参数列表。
- `health_check_url`：可选健康检查地址，HTTP 200 表示健康。

服务目录推导规则：

```text
/Users/elliotk/tmp/assistant.zip
=> /Users/elliotk/tmp/assistant
=> /Users/elliotk/tmp/assistant/assistant-server-1.0.jar
```

如果 `package_file_path` 本身是 `.jar` 文件，则使用该 JAR 所在目录作为服务目录。

## 命令

### deploy

从配置文件部署：

```bash
.venv/bin/python main.py deploy
```

不使用配置文件：

```bash
.venv/bin/python main.py deploy --package /Users/elliotk/tmp/assistant.zip --jar assistant-server-1.0.jar
```

`deploy` 会把压缩包解压到同名目录，并检查目标 JAR 是否存在。

### start

从配置文件启动：

```bash
.venv/bin/python main.py start
```

不使用配置文件：

```bash
.venv/bin/python main.py start --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

临时指定 JVM 参数：

```bash
.venv/bin/python main.py start --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar --jvm="-Xms500m -Xmx512m"
```

注意：JVM 参数以 `-` 开头，建议使用 `--jvm="..."` 写法，避免被 Typer/Click 当作 CLI 选项。

启动状态判断：

- 没有配置 `health_check_url` 时，进程存活即表示 JAR 进程已启动。
- 配置了 `health_check_url` 时，健康检查通过才显示 `ONLINE`。
- 如果进程存在但健康检查失败，会提示“进程存在但健康检查未通过”。

### stop

从配置文件停止：

```bash
.venv/bin/python main.py stop
```

不使用配置文件：

```bash
.venv/bin/python main.py stop --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

强制停止：

```bash
.venv/bin/python main.py stop --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar --force
```

停止时会先读取 PID 文件；如果没有 PID 文件，则按完整 JAR 路径查找进程。

### restart

从配置文件重启：

```bash
.venv/bin/python main.py restart
.venv/bin/python main.py restart --force
```

不使用配置文件：

```bash
.venv/bin/python main.py restart --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py restart --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar --force
```

`restart` 会先停止当前服务，再重新启动。如果服务未运行，会直接启动。

### status

从配置文件查看状态：

```bash
.venv/bin/python main.py status
```

不使用配置文件：

```bash
.venv/bin/python main.py status --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

状态判断规则：

- 无健康检查地址：按 PID 是否存活判断。
- 有健康检查地址：PID 存活且健康检查返回 HTTP 200 才显示 `ONLINE`。

### log

默认读取服务目录下的 `server.log`：

```bash
.venv/bin/python main.py log
```

查看最近 200 行：

```bash
.venv/bin/python main.py log --lines 200
```

实时跟踪：

```bash
.venv/bin/python main.py log --follow
```

指定日志文件：

```bash
.venv/bin/python main.py log --log-file logs/app.log
.venv/bin/python main.py log --log-file /var/log/app.log
```

不使用配置文件：

```bash
.venv/bin/python main.py log --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

说明：当前 `run_server` 默认把 Java 标准输出和错误输出丢弃到 `DEVNULL`，不会自动生成 `server.log`。`log` 命令查看的是已经存在的日志文件，例如 Java 应用自己写出的日志，或通过 `--log-file` 指定的文件。

## 测试

运行单元测试：

```bash
.venv/bin/python -m unittest discover -s tests
```

语法检查：

```bash
.venv/bin/python -m py_compile main.py config_loader.py manager.py test.py tests/test_main.py tests/test_config_loader.py
```

## 打包

推荐使用脚本打包：

```bash
scripts/build_executable.sh
```

自定义可执行文件名：

```bash
scripts/build_executable.sh --name jsvc
```

脚本内部使用 PyInstaller，等价于手动执行：

```bash
.venv/bin/python -m PyInstaller --onefile --name server-cli main.py
```

产物位置：

```text
dist/server-cli
```

运行：

```bash
./dist/server-cli --help
```

打包后仍需要准备 `config.json`，或在支持的命令中通过 `--install-dir` 和 `--jar` 指定服务。

## 项目结构

```text
.
├── config_loader.py          # 配置读取、路径推导、PID、启动、停止等辅助逻辑
├── main.py                   # 主 CLI 入口
├── manager.py                # 多服务管理实验入口
├── requirements.txt          # 依赖列表
├── tests/
│   ├── test_config_loader.py
│   └── test_main.py
└── README.md
```

## manager.py

仓库中保留了 `manager.py`，它是一个多服务管理入口，默认使用 `~/java_services` 作为工作目录。当前主线是 `main.py`，`manager.py` 可以作为后续多服务管理能力的参考实现。

## 已知限制

- `deploy` 仍按压缩包文件名推导安装目录，暂不支持显式 `install_dir`。
- `run_server` 不会自动把 Java stdout/stderr 写入 `server.log`。
- `requirements.txt` 同时包含运行依赖和打包工具，后续可以拆分运行依赖与开发依赖。
- 项目尚未提供 `pyproject.toml` 和正式 console entry point。

---

## English

`server_cli` is a Python command-line tool for deploying and managing Java JAR services. The primary entry point is `main.py`, designed for single-service workflows including deploy, start, stop, restart, status, and log inspection.

The CLI is built with Typer and uses Rich for terminal output.

## Features

- Unpack Java service archives.
- Start a selected JAR file.
- Record service processes with PID files.
- Locate processes by PID file and JAR path.
- Stop, force stop, and restart services.
- Optional health-check URL support.
- Show recent log lines or follow a log file.
- Supports both `config.json` and command-line arguments for selected commands.

## Requirements

- Python 3.12 or compatible
- Java runtime
- macOS or Linux

## Installation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Check the CLI:

```bash
.venv/bin/python main.py --help
```

## Quick Start

With `config.json`:

```bash
.venv/bin/python main.py deploy
.venv/bin/python main.py start
.venv/bin/python main.py status
.venv/bin/python main.py stop
.venv/bin/python main.py restart
```

Without `config.json`, pass the service directory and JAR name:

```bash
.venv/bin/python main.py start --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py status --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py stop --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py restart --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

## Configuration File

`main.py` first looks for `config.json` in the current working directory.

Example:

```json
{
  "package_file_path": "/Users/elliotk/tmp/assistant.zip",
  "jar_name": "assistant-server-1.0.jar",
  "jvm_args": ["-Xmx1g", "-Xms1024M"],
  "health_check_url": "http://127.0.0.1:8080/health"
}
```

Fields:

- `package_file_path`: service archive path. `deploy` unpacks it; other commands use it to infer the service directory.
- `jar_name`: JAR file name to manage.
- `jvm_args`: JVM argument list.
- `health_check_url`: optional health endpoint. HTTP 200 means healthy.

Service directory inference:

```text
/Users/elliotk/tmp/assistant.zip
=> /Users/elliotk/tmp/assistant
=> /Users/elliotk/tmp/assistant/assistant-server-1.0.jar
```

If `package_file_path` is already a `.jar` file, its parent directory is used as the service directory.

## Commands

### deploy

With config:

```bash
.venv/bin/python main.py deploy
```

Without config:

```bash
.venv/bin/python main.py deploy --package /Users/elliotk/tmp/assistant.zip --jar assistant-server-1.0.jar
```

`deploy` unpacks the archive into a same-named directory and checks whether the target JAR exists.

### start

With config:

```bash
.venv/bin/python main.py start
```

Without config:

```bash
.venv/bin/python main.py start --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

Override JVM arguments:

```bash
.venv/bin/python main.py start --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar --jvm="-Xms500m -Xmx512m"
```

Because JVM arguments start with `-`, prefer the `--jvm="..."` form so Typer/Click does not parse them as CLI options.

Start status rules:

- Without `health_check_url`, a live process means the JAR process has started.
- With `health_check_url`, the service is shown as `ONLINE` only after the health check succeeds.
- If the process exists but the health check fails, the CLI reports that the process exists but health is not confirmed.

### stop

With config:

```bash
.venv/bin/python main.py stop
```

Without config:

```bash
.venv/bin/python main.py stop --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

Force stop:

```bash
.venv/bin/python main.py stop --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar --force
```

`stop` first checks the PID file. If no PID file is available, it searches by the full JAR path.

### restart

With config:

```bash
.venv/bin/python main.py restart
.venv/bin/python main.py restart --force
```

Without config:

```bash
.venv/bin/python main.py restart --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
.venv/bin/python main.py restart --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar --force
```

`restart` stops the current service first and then starts it again. If the service is not running, it starts directly.

### status

With config:

```bash
.venv/bin/python main.py status
```

Without config:

```bash
.venv/bin/python main.py status --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

Status rules:

- Without a health URL, status is based on whether the PID is alive.
- With a health URL, the service is `ONLINE` only when the PID is alive and the health check returns HTTP 200.

### log

Read the default `server.log` under the service directory:

```bash
.venv/bin/python main.py log
```

Show the last 200 lines:

```bash
.venv/bin/python main.py log --lines 200
```

Follow logs:

```bash
.venv/bin/python main.py log --follow
```

Specify a log file:

```bash
.venv/bin/python main.py log --log-file logs/app.log
.venv/bin/python main.py log --log-file /var/log/app.log
```

Without config:

```bash
.venv/bin/python main.py log --install-dir /Users/elliotk/tmp/assistant --jar assistant-server-1.0.jar
```

Note: `run_server` currently discards Java stdout/stderr to `DEVNULL`, so it does not automatically create `server.log`. The `log` command reads an existing log file, such as one written by the Java application or specified with `--log-file`.

## Tests

Run unit tests:

```bash
.venv/bin/python -m unittest discover -s tests
```

Syntax check:

```bash
.venv/bin/python -m py_compile main.py config_loader.py manager.py test.py tests/test_main.py tests/test_config_loader.py
```

## Packaging

Recommended build command:

```bash
scripts/build_executable.sh
```

Customize the executable name:

```bash
scripts/build_executable.sh --name jsvc
```

The script uses PyInstaller internally. The equivalent manual command is:

```bash
.venv/bin/python -m PyInstaller --onefile --name server-cli main.py
```

Output:

```text
dist/server-cli
```

Run:

```bash
./dist/server-cli --help
```

After packaging, you still need to provide `config.json` or pass `--install-dir` and `--jar` for commands that support them.

## Project Structure

```text
.
├── config_loader.py          # Config loading, path inference, PID, start/stop helpers
├── main.py                   # Primary CLI entry point
├── manager.py                # Experimental multi-service entry point
├── requirements.txt          # Dependencies
├── tests/
│   ├── test_config_loader.py
│   └── test_main.py
└── README.md
```

## manager.py

`manager.py` is kept as a multi-service management entry point. It uses `~/java_services` by default. The current main path is `main.py`; `manager.py` can be used as a reference for future multi-service features.

## Known Limitations

- `deploy` still infers the installation directory from the archive name and does not yet support an explicit `install_dir`.
- `run_server` does not automatically write Java stdout/stderr to `server.log`.
- `requirements.txt` includes both runtime dependencies and packaging tools; these can be split later.
- The project does not yet provide `pyproject.toml` or an installable console entry point.
