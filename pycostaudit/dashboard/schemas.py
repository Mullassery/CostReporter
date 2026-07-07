"""
Pydantic schemas for request validation.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from enum import Enum


class ForecastAlgorithmEnum(str, Enum):
    """Valid forecasting algorithms"""
    ARIMA = "ARIMA"
    EXPONENTIAL_SMOOTHING = "EXPONENTIAL_SMOOTHING"
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    ENSEMBLE = "ENSEMBLE"


class ComplianceFrameworkEnum(str, Enum):
    """Valid compliance frameworks"""
    SOC2 = "SOC2"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI_DSS"
    ISO_27001 = "ISO_27001"
    CUSTOM = "CUSTOM"


class AuditEventTypeEnum(str, Enum):
    """Valid audit event types"""
    COST_RECORDED = "COST_RECORDED"
    COST_UPDATED = "COST_UPDATED"
    COST_DELETED = "COST_DELETED"
    BUDGET_CHANGED = "BUDGET_CHANGED"
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    REPORT_GENERATED = "REPORT_GENERATED"
    DATA_EXPORTED = "DATA_EXPORTED"


class PeriodEnum(str, Enum):
    """Valid time periods"""
    DAY_7 = "7d"
    DAY_30 = "30d"
    DAY_90 = "90d"
    DAY_365 = "365d"


class OutputFormatEnum(str, Enum):
    """Valid output formats"""
    JSON = "json"
    CSV = "csv"


# ============================================================================
# Auth Schemas
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    password: str = Field(..., min_length=8, max_length=255, description="Password (min 8 chars)")

    @validator("password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="Password")


# ============================================================================
# Cost & Budget Schemas
# ============================================================================

class CostQuery(BaseModel):
    """Cost list query parameters"""
    period: PeriodEnum = Field("7d", description="Time period (7d, 30d, 90d, 365d)")
    provider: Optional[str] = Field(None, max_length=100, description="Filter by provider")
    model: Optional[str] = Field(None, max_length=100, description="Filter by model")
    limit: int = Field(100, ge=1, le=1000, description="Max results (1-1000)")


class BudgetUpdateRequest(BaseModel):
    """Budget update request"""
    amount: float = Field(..., gt=0, description="Monthly budget in USD")
    alert_threshold_percent: float = Field(75, ge=0, le=100, description="Alert threshold (0-100%)")


# ============================================================================
# Forecast Schemas
# ============================================================================

class ForecastQuery(BaseModel):
    """Cost forecast query parameters"""
    forecast_days: int = Field(30, ge=1, le=180, description="Days to forecast (1-180)")
    algorithm: ForecastAlgorithmEnum = Field("ENSEMBLE", description="Forecasting algorithm")
    confidence: float = Field(0.95, ge=0.50, le=0.99, description="Confidence level (0.50-0.99)")
    period: PeriodEnum = Field("30d", description="Historical period (7d, 30d, 90d)")


class BudgetForecastQuery(BaseModel):
    """Budget forecast query parameters"""
    forecast_days: int = Field(30, ge=1, le=180, description="Days to forecast (1-180)")


class TrendQuery(BaseModel):
    """Trend analysis query parameters"""
    period: PeriodEnum = Field("30d", description="Analysis period (7d, 30d, 90d, 365d)")


# ============================================================================
# Compliance Schemas
# ============================================================================

class AuditEventRequest(BaseModel):
    """Audit event request"""
    event_type: AuditEventTypeEnum = Field("COST_RECORDED", description="Event type")
    resource_type: str = Field(..., min_length=1, max_length=100, description="Resource type")
    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    resource_id: Optional[str] = Field(None, max_length=255, description="Resource ID")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    ip_address: Optional[str] = Field(None, max_length=50, description="Client IP address")
    status: str = Field("success", regex="^(success|failure)$", description="Event status")
    error_message: Optional[str] = Field(None, max_length=500, description="Error message if failed")


class ComplianceReportQuery(BaseModel):
    """Compliance report query parameters"""
    framework: ComplianceFrameworkEnum = Field("SOC2", description="Compliance framework")
    period_days: int = Field(30, ge=1, le=365, description="Report period in days (1-365)")


class ComplianceVerifyQuery(BaseModel):
    """Compliance verification query parameters"""
    framework: ComplianceFrameworkEnum = Field("SOC2", description="Compliance framework")


class AuditTrailQuery(BaseModel):
    """Audit trail export query parameters"""
    format: OutputFormatEnum = Field("json", description="Export format (json, csv)")


# ============================================================================
# Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field("ok", description="Service status")
    version: str = Field(..., description="API version")


class UserResponse(BaseModel):
    """User info response"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    name: str = Field(..., description="Full name")


class LoginResponse(BaseModel):
    """Login response"""
    token: str = Field(..., description="JWT token")
    user: UserResponse = Field(..., description="User info")


class CostItem(BaseModel):
    """Single cost entry"""
    id: str
    timestamp: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


class CostListResponse(BaseModel):
    """Cost list response"""
    data: List[CostItem]
    count: int
    period: str
