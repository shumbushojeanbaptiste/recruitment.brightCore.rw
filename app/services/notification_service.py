import logging

logger = logging.getLogger(__name__)


def log_application_status_notification(
    *,
    application_id,
    recipient_email: str,
    status: str,
    note: str | None,
) -> None:
    # Mock notification for this step.
    # A real email provider can replace this implementation later.
    logger.info(
        "Application status notification queued: "
        "application_id=%s recipient=%s status=%s note_present=%s",
        application_id,
        recipient_email,
        status,
        bool(note),
    )