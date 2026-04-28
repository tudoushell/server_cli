# server_cli

中文 | [English](#english)

## 中文

`server_cli` 是一个用于部署和管理 Java JAR 服务的 Python 命令行工具。项目基于 Typer 构建命令行交互，使用 Rich 输出状态表格和运行提示。

这个仓库目前包含两套 CLI：

- `main.py`：读取当前目录的 `config.json`，用于管理单个固定服务。
- `manager.py`：以 `~/java_services` 为工作目录，用于管理多个服务，功能更完整。

如果只是按现有 `config.json` 管理一个服务，使用 `main.py`。如果希望部署和管理多个服务，优先使用 `manager.py`。

## 功能特性

- 解压 Java 服务包。
- 启动指定 JAR 服务。
- 记录和读取 PID。
- 查看服务运行状态。
- 支持可选健康检查 URL。
- `manager.py` 支持停止、重启和日志查看。
- 使用 Rich 展示更易读的终端输出。

## 环境要求

- Python 3.12 或兼容版本
- Java 运行环境
- macOS 或 Linux 终端环境

## 安装

创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

检查命令是否可用：

```bash
.venv/bin/python main.py --help
.venv/bin/python manager.py --help
```

## 使用 `main.py`

`main.py` 是配置驱动的单服务入口。它会读取项目根目录下的 `config.json`。

配置示例：

```json
{
  "package_file_path": "/Users/elliotk/tmp/assistant.zip",
  "jar_name": "assistant-server-1.0.jar",
  "server_port": 8080,
  "jar_extra_args": ["-Xmx1g", "-Xms1024M"],
  "health_check_url": ""
}
```

配置字段：

- `package_file_path`：服务压缩包路径。
- `jar_name`：解压后需要启动的 JAR 文件名。
- `server_port`：服务端口，目前主要作为配置记录。
- `jar_extra_args`：传给 JVM 的启动参数。
- `health_check_url`：健康检查地址，返回 HTTP 200 时认为服务在线；留空则只按 PID 判断。

常用命令：

```bash
.venv/bin/python main.py deploy
.venv/bin/python main.py start
.venv/bin/python main.py status
```

当前限制：`main.py` 中的 `stop`、`restart` 和 `log` 命令还没有完整实现。

## 使用 `manager.py`

`manager.py` 是多服务管理入口，默认使用以下目录：

```text
~/java_services          # 服务部署目录
~/java_services/.pids    # PID 文件目录
~/java_services/.logs    # 日志目录
```

部署并启动服务：

```bash
.venv/bin/python manager.py deploy /path/to/app.zip --name my-service --jvm "-Xmx512m" --args "--server.port=8080"
```

管理服务：

```bash
.venv/bin/python manager.py start my-service
.venv/bin/python manager.py stop my-service
.venv/bin/python manager.py restart my-service
.venv/bin/python manager.py status
```

查看日志：

```bash
.venv/bin/python manager.py logs my-service --lines 100
.venv/bin/python manager.py logs my-service --follow
```

如果没有传入服务名，`manager.py` 会在多个已部署服务之间提供交互式选择；如果只有一个服务，会自动选择该服务。

## 项目结构

```text
.
├── config.json          # main.py 使用的服务配置
├── config_loader.py     # 配置读取、解压、启动和状态检查逻辑
├── main.py              # 单服务 CLI 入口
├── manager.py           # 多服务 CLI 入口
├── requirements.txt     # Python 依赖
├── test.py              # 临时实验脚本
└── README.md            # 项目说明
```

## 开发

语法检查：

```bash
.venv/bin/python -m py_compile main.py config_loader.py manager.py test.py
```

查看当前服务状态：

```bash
.venv/bin/python main.py status
.venv/bin/python manager.py status
```

## 依赖说明

当前 `requirements.txt` 来自虚拟环境导出，包含运行依赖以及打包相关工具。项目实际核心运行依赖主要是：

- `typer`
- `rich`
- `requests`

如果只需要运行源码，可以把 `requirements.txt` 精简到上述核心依赖。

## 已知限制

- `main.py` 的停止、重启和日志命令尚未完成。
- 尚未提供正式单元测试。
- 尚未提供 `pyproject.toml` 或安装入口。
- `config.json` 中使用了本机绝对路径，换环境运行前需要修改。
- 进程识别主要依赖 PID 文件和进程查询，生产环境使用前建议进一步加固。

---

## English

`server_cli` is a Python command-line tool for deploying and managing Java JAR services. It uses Typer for the CLI and Rich for readable terminal output.

The repository currently contains two CLI entry points:

- `main.py`: reads `config.json` from the project directory and manages one configured service.
- `manager.py`: manages multiple services under `~/java_services` and provides a more complete command set.

Use `main.py` when you want to manage the single service described by `config.json`. Use `manager.py` when you want to deploy and manage multiple services.

## Features

- Unpack Java service archives.
- Start a specified JAR service.
- Write and read PID files.
- Show service status.
- Support an optional health-check URL.
- `manager.py` supports stop, restart, and log viewing.
- Rich terminal output for better readability.

## Requirements

- Python 3.12 or a compatible version
- Java runtime
- macOS or Linux terminal environment

## Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Check that the CLIs are available:

```bash
.venv/bin/python main.py --help
.venv/bin/python manager.py --help
```

## Using `main.py`

`main.py` is the config-driven single-service entry point. It reads `config.json` from the project root.

Example configuration:

```json
{
  "package_file_path": "/Users/elliotk/tmp/assistant.zip",
  "jar_name": "assistant-server-1.0.jar",
  "server_port": 8080,
  "jar_extra_args": ["-Xmx1g", "-Xms1024M"],
  "health_check_url": ""
}
```

Fields:

- `package_file_path`: path to the service archive.
- `jar_name`: JAR file name to start after unpacking.
- `server_port`: service port, currently kept as configuration metadata.
- `jar_extra_args`: JVM arguments.
- `health_check_url`: health-check endpoint. HTTP 200 means online; leave it empty to rely on PID checks only.

Common commands:

```bash
.venv/bin/python main.py deploy
.venv/bin/python main.py start
.venv/bin/python main.py status
```

Current limitation: `stop`, `restart`, and `log` in `main.py` are not fully implemented yet.

## Using `manager.py`

`manager.py` is the multi-service entry point. It uses these directories by default:

```text
~/java_services          # Service deployment directory
~/java_services/.pids    # PID files
~/java_services/.logs    # Log files
```

Deploy and start a service:

```bash
.venv/bin/python manager.py deploy /path/to/app.zip --name my-service --jvm "-Xmx512m" --args "--server.port=8080"
```

Manage a service:

```bash
.venv/bin/python manager.py start my-service
.venv/bin/python manager.py stop my-service
.venv/bin/python manager.py restart my-service
.venv/bin/python manager.py status
```

View logs:

```bash
.venv/bin/python manager.py logs my-service --lines 100
.venv/bin/python manager.py logs my-service --follow
```

If no service name is provided, `manager.py` prompts for a selection when multiple services exist. If only one service exists, it is selected automatically.

## Project Structure

```text
.
├── config.json          # Service configuration used by main.py
├── config_loader.py     # Config loading, unpacking, startup, and status logic
├── main.py              # Single-service CLI entry point
├── manager.py           # Multi-service CLI entry point
├── requirements.txt     # Python dependencies
├── test.py              # Temporary experiment script
└── README.md            # Project documentation
```

## Development

Syntax check:

```bash
.venv/bin/python -m py_compile main.py config_loader.py manager.py test.py
```

Show current service status:

```bash
.venv/bin/python main.py status
.venv/bin/python manager.py status
```

## Dependencies

The current `requirements.txt` was exported from a virtual environment, so it includes runtime dependencies and packaging tools. The core runtime dependencies are:

- `typer`
- `rich`
- `requests`

If you only need to run the source code, `requirements.txt` can be reduced to those core dependencies.

## Known Limitations

- `stop`, `restart`, and `log` in `main.py` are not completed.
- No formal unit tests are included yet.
- No `pyproject.toml` or installable console entry point is included yet.
- `config.json` contains local absolute paths and must be updated for another environment.
- Process detection mainly relies on PID files and process lookup; hardening is recommended before production use.
