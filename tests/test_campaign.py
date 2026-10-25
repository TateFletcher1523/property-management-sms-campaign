from src.campaign import InspectionReminder, MaintenanceRequest, TenantDocument, build_messages


def test_campaign_excludes_records_without_a_phone() -> None:
    messages, skipped = build_messages(
        [MaintenanceRequest("MR-1", "Ari", "+15550001", "fix the lock")],
        [TenantDocument("Ari", "+15550001", "lease copy", "2026-12-01")],
        [InspectionReminder("2A", None, "2026-12-02")],
    )

    assert len(messages) == 2
    assert messages[0]["to"] == "+15550001"
    assert skipped == ["inspection:2A"]
