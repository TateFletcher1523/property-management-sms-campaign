from .campaign import InspectionReminder, MaintenanceRequest, TenantDocument, build_messages, send_campaign
from .infrai_client import InfraiClient


def main() -> None:
    messages, skipped = build_messages(
        [MaintenanceRequest("MR-104", "Mina", "+15550101", "replace the kitchen tap")],
        [TenantDocument("Mina", "+15550101", "renter insurance certificate", "2026-11-01")],
        [InspectionReminder("3B", None, "2026-11-04")],
    )
    results = send_campaign(InfraiClient(), messages)
    print({"sent": results, "skipped": skipped})


if __name__ == "__main__":
    main()
