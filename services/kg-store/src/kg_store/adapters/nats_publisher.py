"""NATS JetStream publisher — CloudEvents 1.0 envelope (IF-INFRA-001)."""
import json
import uuid
from datetime import datetime, timezone

import nats
import nats.js

from ..domain import bir_id as bir_id_mod
from ..ports.events import ChangeEventPublisher

_SOURCE = "urn:archpulse:cs-kg-store"
_EVENT_TYPE = "jp.archpulse.kg.bir-updated.v1"


class NatsJetStreamPublisher(ChangeEventPublisher):
    def __init__(self, nc: nats.aio.client.Client, stream: str = "bldg") -> None:
        self._nc = nc
        self._js: nats.js.JetStreamContext = nc.jetstream()
        self._stream = stream

    async def publish_bir_updated(
        self,
        tid: str,
        bir_id: str,
        added_triples: list[tuple[str, str, str]],
        removed_triples: list[tuple[str, str, str]],
    ) -> None:
        tid_slug = bir_id_mod.to_nats_slug(tid)
        bir_slug = bir_id_mod.to_nats_slug(bir_id)
        subject = f"{self._stream}.{tid_slug}.event.bir-updated.{bir_slug}"

        envelope = {
            "specversion": "1.0",
            "id": str(uuid.uuid4()),
            "source": _SOURCE,
            "type": _EVENT_TYPE,
            "time": datetime.now(timezone.utc).isoformat(),
            "datacontenttype": "application/json",
            "tid": tid,
            "data_class": "Analytics",
            "subject": bir_id,
            "data": {
                "bir_id": bir_id,
                "added_triples": [list(t) for t in added_triples],
                "removed_triples": [list(t) for t in removed_triples],
            },
        }
        await self._js.publish(subject, json.dumps(envelope).encode())

    async def aclose(self) -> None:
        await self._nc.drain()
