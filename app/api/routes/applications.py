
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import EmailStr, TypeAdapter
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.schemas.application import ApplicationPublic
from app.services.application_service import submit_application

router = APIRouter(tags=["applications"])
email_adapter = TypeAdapter(EmailStr)


@router.post(
    "/jobs/{job_id}/applications",
    response_model=ApplicationPublic,
    status_code=201,
)
async def apply_for_job(
    job_id: uuid.UUID,
    full_name: Annotated[str, Form(min_length=2, max_length=150)],
    email: Annotated[str, Form(max_length=320)],
    phone: Annotated[str, Form(min_length=7, max_length=30)],
    cv: Annotated[UploadFile, File()],
    cover_note: Annotated[str | None, Form(max_length=5000)] = None,
    db: Session = Depends(get_db),
    _: None = Depends(
        rate_limit(
            limit=10,
            window_seconds=60,
            key_prefix="application-submit",
        )
    ),
) -> ApplicationPublic:
    full_name = " ".join(full_name.split())
    phone = phone.strip()

    if len(full_name) < 2:
        raise HTTPException(status_code=422, detail="Invalid full name")

    if not phone:
        raise HTTPException(status_code=422, detail="Phone is required")

    try:
        normalized_email = str(email_adapter.validate_python(email)).lower()
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="A valid email address is required",
        ) from exc

    return await submit_application(
        db,
        job_id=job_id,
        full_name=full_name,
        email=normalized_email,
        phone=phone,
        cover_note=cover_note,
        cv=cv,
    )
