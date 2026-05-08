from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from app.config import get_settings
from app.models import SubAgentPayload
from app.subagent import SubAgentWorker


async def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m workers.agent_worker <payload.json> <result.json>", file=sys.stderr)
        return 1

    payload_path = Path(sys.argv[1])
    result_path = Path(sys.argv[2])

    payload = SubAgentPayload.model_validate(
        json.loads(payload_path.read_text(encoding="utf-8"))
    )
    worker = SubAgentWorker(get_settings())
    result = await worker.execute(payload)
    result_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

