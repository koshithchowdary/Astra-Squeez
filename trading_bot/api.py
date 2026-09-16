from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .domain import RiskLimits
from .engine import TradingEngine
from .gateways import CCXTMarketDataGateway, PaperExecutionGateway
from .risk import RiskManager
from .strategy import StructuralRetestStrategy

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)


class RunRequest(BaseModel):
    symbol: str = Field(min_length=1)
    timeframe: str = "30m"
    exchange: str = "binance"


execution = PaperExecutionGateway(float(os.getenv("PAPER_EQUITY", "100000")))
risk = RiskManager(RiskLimits(
    risk_fraction_per_trade=float(os.getenv("RISK_PER_TRADE", "0.005")),
    max_daily_loss_fraction=float(os.getenv("MAX_DAILY_LOSS", "0.02")),
    max_weekly_loss_fraction=float(os.getenv("MAX_WEEKLY_LOSS", "0.05")),
    min_rr=float(os.getenv("MIN_RR", "2.5")),
))
strategy = StructuralRetestStrategy()
running_tasks: set[asyncio.Task] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("service startup execution_mode=PAPER")
    yield
    for task in running_tasks:
        task.cancel()
    if running_tasks:
        await asyncio.gather(*running_tasks, return_exceptions=True)


app = FastAPI(title="AstraSqueeze Structural Retest Engine", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "execution_mode": "paper", "tasks": len(running_tasks)}


@app.post("/run")
async def run(request: RunRequest):
    if any(not task.done() for task in running_tasks):
        raise HTTPException(409, "engine already has an active stream")
    gateway = CCXTMarketDataGateway(request.exchange)
    engine = TradingEngine(gateway, execution, strategy, risk)
    task = asyncio.create_task(engine.run_symbol(request.symbol, request.timeframe))
    running_tasks.add(task)
    task.add_done_callback(running_tasks.discard)
    return {"status": "started", "symbol": request.symbol, "timeframe": request.timeframe, "mode": "paper"}


@app.post("/stop")
async def stop():
    for task in list(running_tasks):
        task.cancel()
    return {"status": "stopping"}
