# purchase/domain/enums/requisition_status.py

from enum import StrEnum


class RequisitionStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"