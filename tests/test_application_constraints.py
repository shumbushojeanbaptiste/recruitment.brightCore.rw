
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from tests.helpers import (
    create_application,
    create_published_job,
    create_user,
)


def test_same_email_cannot_apply_twice_to_same_job(db_session):
    admin = create_user(db_session)
    job = create_published_job(db_session, admin.id)

    create_application(db_session, job.id, "same@example.com")

    with pytest.raises(IntegrityError):
        create_application(db_session, job.id, "same@example.com")

    db_session.rollback()
