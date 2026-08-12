import hashlib
import json
from flask import request
from flask_login import current_user
from .extensions import db
from .models import AuditLog


def audit(action: str, resource_type: str | None = None, resource_id: str | None = None, details=None):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else None
    row = AuditLog(
        user_id=getattr(current_user, "id", None) if getattr(current_user, "is_authenticated", False) else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_hash=ip_hash,
        details_json=json.dumps(details, ensure_ascii=False) if details is not None else None,
    )
    db.session.add(row)
    db.session.commit()
