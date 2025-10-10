import asyncio, random, json, httpx, time, math, hashlib
from urllib.parse import quote_plus

SERVER = "http://localhost:8000"

_httpx_client: httpx.AsyncClient | None = None
_cfg_cache: dict[str, tuple[dict, float]] = {}
CFG_TTL_SEC = 30.0

# ====== 调度与限流参数（可在 config.json 覆盖）======
PERIOD_SEC = 60.0         # 对齐周期：默认每整分
PHASE_MAX_MS = 10_000     # 每只传感器固定相位 0~10s 以内错峰
MAX_INFLIGHT = 20         # 全局同时在途请求上限
_sema: asyncio.Semaphore | None = None
# ===================================================

# -------------------- HTTP 客户端 --------------------
async def get_client() -> httpx.AsyncClient:
    global _httpx_client
    if _httpx_client is None:
        limits = httpx.Limits(max_connections=400, max_keepalive_connections=200)
        _httpx_client = httpx.AsyncClient(timeout=20, limits=limits, http2=True)
    return _httpx_client

def _get_sema() -> asyncio.Semaphore:
    global _sema
    if _sema is None:
        _sema = asyncio.Semaphore(MAX_INFLIGHT)
    return _sema

# -------------------- Household 解析 --------------------
async def query_house_id_by_householder(householder: str) -> str | None:
    client = await get_client()
    paths = [
        f"{SERVER}/households?householder={quote_plus(householder)}",
        f"{SERVER}/api/households/resolve?householder={quote_plus(householder)}",
        f"{SERVER}/api/households?householder={quote_plus(householder)}",
    ]
    for url in paths:
        try:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "house_id" in data:
                    return str(data["house_id"])
                if isinstance(data, list) and data:
                    first = data[0]
                    if isinstance(first, dict) and "house_id" in first:
                        return str(first["house_id"])
        except Exception:
            continue
    return None

async def resolve_house_id(box: dict) -> str:
    v = box.get("house_id")
    if v:
        return str(v)
    name = box.get("householder")
    if name:
        hid = await query_house_id_by_householder(str(name))
        if hid:
            return hid
    raise RuntimeError("house_id or householder is required in box definition")

# -------------------- 传感器创建 --------------------
async def create_sensor(box: dict, sensor: dict, house_id: str) -> dict:
    client = await get_client()
    url = f"{SERVER}/sensors/?house_id={quote_plus(house_id)}"
    serial = sensor.get("serial") or sensor.get("serial_number") or box.get("serial_number")

    # 冗余写一些元信息，便于排查
    meta = (sensor.get("meta") or {}) | {"house_id": house_id, "box": box.get("name")}
    payload = {
        "name": f"{box['name']}_{sensor['name']}",
        "type": sensor["type"],
        "location": box.get("location"),
        "metadata": meta,
    }
    if serial:
        payload["serial_number"] = serial

    print("POST", url, "payload.serial_number=", payload.get("serial_number"))
    r = await client.post(url, json=payload)
    r.raise_for_status()
    return r.json()

# -------------------- 配置读取（带缓存） --------------------
async def fetch_config_raw(sensor_id: str, retries: int = 4, delay: float = 0.25) -> dict:
    client = await get_client()
    for i in range(retries):
        try:
            r = await client.get(f"{SERVER}/sensors/{sensor_id}")
            if r.status_code == 200:
                data = r.json()
                cfg = data.get("meta") or data.get("metadata") or {}
                return cfg or {}
            return {}
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError, httpx.ReadTimeout):
            await asyncio.sleep(delay * (2 ** i))
    return {}

async def fetch_config_with_cache(sensor_id: str) -> dict:
    now = time.monotonic()
    hit = _cfg_cache.get(sensor_id)
    if hit and hit[1] > now:
        return hit[0]
    cfg = await fetch_config_raw(sensor_id)
    if not isinstance(cfg, dict):
        cfg = {}
    _cfg_cache[sensor_id] = (cfg, now + CFG_TTL_SEC)
    return cfg

# -------------------- 对齐调度（整分 + 稳定相位） --------------------
def _next_tick(anchor: float, period: float) -> float:
    now = time.time()
    k = math.floor((now - anchor) / period) + 1
    return anchor + k * period

async def _sleep_until(ts_epoch: float):
    delay = ts_epoch - time.time()
    if delay > 0:
        await asyncio.sleep(delay)

def _stable_phase_seconds(sensor_id: str, max_ms: int) -> float:
    h = hashlib.md5(sensor_id.encode("utf-8")).hexdigest()
    ms = int(h, 16) % max_ms
    return ms / 1000.0

# -------------------- 写入读数（带重试 + 并发限流） --------------------
def _should_retry_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599

async def send_reading_with_retry(sensor_id: str, value: float, attributes: dict | None = None, max_retries: int = 3) -> bool:
    client = await get_client()
    sem = _get_sema()

    # 组装 payload（保障可序列化）
    payload = {"sensor_id": str(sensor_id), "value": float(value), "attributes": {}}
    if attributes:
        for k, v in attributes.items():
            payload["attributes"][k] = v if isinstance(v, (str, int, float, bool)) or v is None else str(v)

    for attempt in range(max_retries + 1):
        try:
            async with sem:
                r = await client.post(f"{SERVER}/ingest", json=payload)
            if r.status_code < 300:
                return True
            if _should_retry_status(r.status_code) and attempt < max_retries:
                await asyncio.sleep((0.25 * (2 ** attempt)) + random.uniform(0, 0.25))
                continue
            else:
                print(f"[WARN] ingest HTTP {r.status_code}: {r.text[:200]}")
                return False
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError, httpx.ConnectError) as e:
            if attempt < max_retries:
                await asyncio.sleep((0.25 * (2 ** attempt)) + random.uniform(0, 0.25))
                continue
            print(f"[WARN] ingest network error: {e!r}")
            return False
        except Exception as e:
            print(f"[WARN] ingest unexpected error: {e!r}")
            return False

# -------------------- 传感器循环（每周期一次，失败不退出） --------------------
async def sensor_worker(box_def: dict, s: dict, server_obj: dict):
    sid = server_obj["id"]                          # 服务器返回的传感器 UUID
    phase = _stable_phase_seconds(sid, PHASE_MAX_MS)  # 0~PHASE_MAX_MS 毫秒稳定相位
    anchor = 0.0                                    # 与 Unix 纪元对齐 → 整分/整5分等

    # 首次对齐到 “整周期 + 固定相位”
    first_tick = _next_tick(anchor, PERIOD_SEC) + phase
    await _sleep_until(first_tick)

    while True:
        try:
            # 若禁用则跳过本周期
            if not s.get("enabled", True):
                next_tick = _next_tick(anchor, PERIOD_SEC) + phase
                await _sleep_until(next_tick)
                continue

            # 生成值：先读缓存配置，再从定义中兜底
            cfg = await fetch_config_with_cache(sid)
            base = s.get("meta") or {}
            lo = float(cfg.get("min", base.get("min", 0)))
            hi = float(cfg.get("max", base.get("max", 1)))
            if hi < lo:
                lo, hi = hi, lo
            value = random.uniform(lo, hi)
        except Exception as e:
            print(f"[WARN] gen value failed for {sid}: {e}")
            value = 0.0

        serial_attr = s.get("serial") or s.get("serial_number") or box_def.get("serial_number")
        ok = await send_reading_with_retry(
            sid,
            value,
            {
                "unit": s["type"],
                "box": box_def["name"],
                "serial_number": serial_attr,
            },
        )
        print(time.strftime("[%Y-%m-%d %H:%M:%S]"),
              f"{box_def['name']} {s['name']} -> {value:.2f} (phase {phase*1000:.0f}ms) ok={ok}")

        # 睡到下一“整周期 + 固定相位”
        next_tick = _next_tick(anchor, PERIOD_SEC) + phase
        await _sleep_until(next_tick)

# -------------------- Box 主流程 --------------------
async def simulate_box(box_def: dict):
    await get_client()  # 初始化 HTTP 客户端
    house_id = await resolve_house_id(box_def)

    # 1) 创建所有传感器
    sensors = []
    for s in (box_def.get("sensors") or []):
        resp = await create_sensor(box_def, s, house_id)
        sensors.append({"def": s, "server": resp})
        print(f"Created {resp['name']} id={resp['id']} enabled={s.get('enabled', True)}")

    # 2) 每个传感器一个独立任务：整分对齐 + 稳定相位 + 限流 + 重试
    tasks = [asyncio.create_task(sensor_worker(box_def, s["def"], s["server"])) for s in sensors]
    await asyncio.gather(*tasks)

# -------------------- 入口 --------------------
async def main():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    global SERVER, PERIOD_SEC, PHASE_MAX_MS, MAX_INFLIGHT, _sema
    SERVER = config.get("server_url", SERVER)
    PERIOD_SEC = float(config.get("period_seconds", PERIOD_SEC))          # 例如 60 或 300
    PHASE_MAX_MS = int(config.get("phase_max_ms", PHASE_MAX_MS))          # 例如 10000/15000/20000
    MAX_INFLIGHT = int(config.get("max_inflight", MAX_INFLIGHT))          # 例如 20/30/40

    # 以最新值重建限流信号量
    _sema = asyncio.Semaphore(MAX_INFLIGHT)

    tasks = [simulate_box(box) for box in config["boxes"]]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
