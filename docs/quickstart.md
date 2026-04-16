# 快速上手

这页只给最短路径。  
先跑通，再看高级参数。

## 1. 安装

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

安装：

```bash
pip install bullet-trade
```

## 2. 回测

```bash
bullet-trade backtest strategies/demo_strategy.py --start 2024-01-01 --end 2024-06-01
```

## 3. 本地 QMT

`.env` 最少：

```env
DEFAULT_DATA_PROVIDER=qmt
DEFAULT_BROKER=qmt
QMT_DATA_PATH=C:\国金QMT交易端\userdata_mini
QMT_ACCOUNT_ID=123456
```

运行：

```bash
bullet-trade live strategies/demo_strategy.py --broker qmt
```

## 4. 远程 server

Windows 上的 `.env` 最少：

```env
QMT_DATA_PATH=C:\国金QMT交易端\userdata_mini
QMT_ACCOUNT_ID=123456
QMT_SERVER_TOKEN=secret
```

启动：

```bash
bullet-trade --env-file .env server --listen 0.0.0.0 --port 58620 --enable-data --enable-broker
```

## 5. 远程 qmt-remote 客户端

客户端 `.env` 最少：

```env
DEFAULT_DATA_PROVIDER=qmt-remote
DEFAULT_BROKER=qmt-remote
QMT_SERVER_HOST=10.0.0.8
QMT_SERVER_PORT=58620
QMT_SERVER_TOKEN=secret
```

运行：

```bash
bullet-trade live strategies/demo_strategy.py --broker qmt-remote
```

## 6. 这几个参数先不用写

如果你只是想先跑通，下面这些先不要写：

- `LOG_DIR`
- `RUNTIME_DIR`
- `QMT_ACCOUNT_TYPE`
- `QMT_SERVER_ACCOUNT_KEY`
- `QMT_SESSION_ID`
- 风控相关参数

## 7. 常见问题

### `QMT_ACCOUNT_TYPE=stock` 要不要写

不用。  
默认就是 `stock`。  
只有期货账户才需要写 `QMT_ACCOUNT_TYPE=future`。

### `--accounts default=123456:stock` 要不要写

单账户场景也不用。  
如果 `.env` 里已经有 `QMT_ACCOUNT_ID=123456`，server 直接就能启动。

### `--data-path` 为什么报错

因为当前版本没有这个参数。  
请把数据目录写到 `.env`：

```env
QMT_DATA_PATH=C:\国金QMT交易端\userdata_mini
```

更多说明：

- [配置总览](config.md)
- [实盘引擎](live.md)
- [QMT server](qmt-server.md)
