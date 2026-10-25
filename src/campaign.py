from dataclasses import dataclass
from typing import Any

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    tenant_name: str
    phone: str | None
    summary: str


@dataclass(frozen=True)
class TenantDocument:
    tenant_name: str
    phone: str | None
    document_name: str
    due_date: str


@dataclass(frozen=True)
class InspectionReminder:
    unit: str
    phone: str | None
    inspection_date: str


def build_messages(
    requests: list[MaintenanceRequest],
    documents: list[TenantDocument],
    inspections: list[InspectionReminder],
) -> tuple[list[dict[str, str]], list[str]]:
    messages: list[dict[str, str]] = []
    skipped: list[str] = []
    for item in requests:
        if item.phone:
            messages.append({"to": item.phone, "message": f"Hi {item.tenant_name}, maintenance request {item.request_id}: {item.summary}."})
        else:
            skipped.append(f"request:{item.request_id}")
    for item in documents:
        if item.phone:
            messages.append({"to": item.phone, "message": f"Hi {item.tenant_name}, please send your {item.document_name} by {item.due_date}."})
        else:
            skipped.append(f"document:{item.document_name}")
    for item in inspections:
        if item.phone:
            messages.append({"to": item.phone, "message": f"Inspection reminder for unit {item.unit}: {item.inspection_date}."})
        else:
            skipped.append(f"inspection:{item.unit}")
    return messages, skipped


def send_campaign(client: InfraiClient, messages: list[dict[str, str]]) -> list[dict[str, Any]]:
    client.queue_publish_batch({"queue": "property-reminders", "messages": messages})
    sent = client.sms_batch_send(messages)
    results = []
    for item in sent if isinstance(sent, list) else sent.get("messages", []):
        message_id = item["message_id"]
        results.append({"message_id": message_id, "status": client.sms_events(message_id)})
    return results
