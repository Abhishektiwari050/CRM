"""
Activity log and daily report models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============================================================================
# Activity Log Models
# ============================================================================

class ActivityLog(BaseModel):
    client_id: str
    outcome: str
    notes: Optional[str] = None
    category: Optional[str] = None
    attachments: Optional[List[dict]] = None
    quantity: Optional[int] = 1
    contact_method: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_due_date: Optional[str] = None

class ActivityLogResponse(BaseModel):
    id: str
    client_id: str
    employee_id: str
    category: str
    outcome: str
    notes: Optional[str] = None
    attachments: Optional[List[dict]] = None
    quantity: int = 1
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# Daily Report Models
# ============================================================================

class DailyReport(BaseModel):
    ta_calls: Optional[int] = None
    ta_calls_to: Optional[str] = None
    renewal_calls: Optional[int] = None
    renewal_calls_to: Optional[str] = None
    service_calls: Optional[int] = None
    service_calls_to: Optional[str] = None
    zero_star_calls: Optional[int] = None
    one_star_calls: Optional[int] = None
    additional_info: Optional[str] = None

class DailyReportResponse(BaseModel):
    id: str
    employee_id: str
    date: str
    ta_calls: Optional[int] = None
    renewal_calls: Optional[int] = None
    service_calls: Optional[int] = None
    zero_star_calls: Optional[int] = None
    one_star_calls: Optional[int] = None
    additional_info: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
