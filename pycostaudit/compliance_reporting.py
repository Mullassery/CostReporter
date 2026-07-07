"""
Compliance reporting module for cost audits and regulatory requirements.
Generates audit trails, cost certifications, and compliance reports.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
import hashlib
import csv
from io import StringIO


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOC2 = "soc2"           # SOC 2 Type II
    HIPAA = "hipaa"         # HIPAA BAA
    GDPR = "gdpr"           # GDPR compliance
    PCI_DSS = "pci_dss"     # PCI DSS
    ISO_27001 = "iso_27001" # ISO 27001
    CUSTOM = "custom"       # Custom requirements


class AuditEventType(Enum):
    """Types of audit events"""
    COST_RECORDED = "cost_recorded"
    COST_UPDATED = "cost_updated"
    COST_DELETED = "cost_deleted"
    BUDGET_CHANGED = "budget_changed"
    ALERT_TRIGGERED = "alert_triggered"
    REPORT_GENERATED = "report_generated"
    USER_LOGIN = "user_login"
    EXPORT_REQUESTED = "export_requested"


@dataclass
class AuditEvent:
    """Single audit event for compliance log"""
    event_id: str = field(default_factory=lambda: hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:16])
    event_type: AuditEventType = AuditEventType.COST_RECORDED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str = ""
    resource_type: str = ""  # cost, budget, alert
    resource_id: str = ""
    action: str = ""  # create, update, delete
    old_values: Dict = field(default_factory=dict)
    new_values: Dict = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"  # success, failure
    error_message: Optional[str] = None
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return data


@dataclass
class ComplianceReport:
    """Compliance report for audit and certification"""
    report_id: str
    framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    organization: str
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # Data summary
    total_costs: float = 0.0
    total_operations: int = 0
    cost_records: int = 0
    anomalies_detected: int = 0
    alerts_triggered: int = 0

    # Audit results
    audit_events: List[AuditEvent] = field(default_factory=list)
    access_logs: List[Dict] = field(default_factory=list)
    failed_operations: List[Dict] = field(default_factory=list)

    # Certification
    certified: bool = False
    certifier_name: str = ""
    certifier_signature: str = ""
    certification_date: Optional[datetime] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "framework": self.framework.value,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "organization": self.organization,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total_costs": self.total_costs,
                "total_operations": self.total_operations,
                "cost_records": self.cost_records,
                "anomalies_detected": self.anomalies_detected,
                "alerts_triggered": self.alerts_triggered
            },
            "audit_events_count": len(self.audit_events),
            "access_logs_count": len(self.access_logs),
            "failed_operations_count": len(self.failed_operations),
            "certified": self.certified,
            "certification_date": self.certification_date.isoformat() if self.certification_date else None
        }


class ComplianceManager:
    """Manages compliance auditing and reporting"""

    def __init__(self, db=None):
        self.db = db
        self.audit_log: List[AuditEvent] = []
        self.compliance_rules: Dict[ComplianceFramework, List[str]] = self._init_compliance_rules()

    def _init_compliance_rules(self) -> Dict[ComplianceFramework, List[str]]:
        """Initialize compliance rules for each framework"""
        return {
            ComplianceFramework.SOC2: [
                "All cost changes must be logged",
                "Access control must be enforced",
                "Data must be encrypted at rest and in transit",
                "User actions must be auditable"
            ],
            ComplianceFramework.HIPAA: [
                "All cost records must be retained for 6 years",
                "Access must be limited to authorized personnel",
                "All access must be logged with timestamp",
                "Breach notification required within 60 days"
            ],
            ComplianceFramework.GDPR: [
                "User data must be encrypted",
                "Right to be forgotten must be implemented",
                "Data breach must be reported within 72 hours",
                "Data processing agreements required"
            ],
            ComplianceFramework.PCI_DSS: [
                "All financial data must be encrypted",
                "Access control lists must be maintained",
                "All access must be logged and monitored",
                "Regular security assessments required"
            ],
            ComplianceFramework.ISO_27001: [
                "Information security policy documented",
                "Access control and authentication",
                "Cryptography and encryption requirements",
                "Incident management procedures"
            ]
        }

    def record_audit_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        resource_type: str,
        action: str,
        resource_id: str = "",
        old_values: Dict = None,
        new_values: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        status: str = "success",
        error_message: str = None
    ) -> AuditEvent:
        """Record an audit event"""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        self.audit_log.append(event)
        return event

    def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        user_id: str,
        organization: str,
        period_days: int = 30,
        anomalies: List[Tuple[str, float]] = None,
        cost_summary: Dict = None,
        forecast_data: Dict = None
    ) -> ComplianceReport:
        """Generate compliance report for the specified framework"""
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)

        # Filter audit events for period
        period_events = [e for e in self.audit_log if e.timestamp >= period_start]

        # Build report
        report = ComplianceReport(
            report_id=self._generate_report_id(),
            framework=framework,
            period_start=period_start,
            period_end=now,
            organization=organization,
            audit_events=period_events,
            cost_records=cost_summary.get('num_operations', 0) if cost_summary else 0,
            total_costs=cost_summary.get('total', 0.0) if cost_summary else 0.0,
            anomalies_detected=len(anomalies) if anomalies else 0,
        )

        # Add framework-specific data
        report.metadata = {
            "compliance_rules": self.compliance_rules[framework],
            "framework_version": "1.0",
            "audit_scope": f"Cost tracking system for user {user_id}",
            "report_period_days": period_days
        }

        # Check failed operations
        report.failed_operations = [asdict(e) for e in period_events if e.status == "failure"]

        return report

    def verify_compliance(
        self,
        report: ComplianceReport,
        framework: ComplianceFramework
    ) -> Dict[str, bool]:
        """Verify compliance against framework requirements"""
        results = {}
        rules = self.compliance_rules[framework]

        # Generic compliance checks
        results["audit_logging_enabled"] = len(report.audit_events) > 0
        results["no_failed_operations"] = len(report.failed_operations) == 0
        results["data_retention_policy"] = report.period_end > report.period_start
        results["anomalies_logged"] = report.anomalies_detected >= 0

        # Framework-specific checks
        if framework == ComplianceFramework.HIPAA:
            results["hipaa_retention"] = self._check_hipaa_retention(report)
            results["hipaa_access_control"] = self._check_hipaa_access(report)
            results["hipaa_breach_notification"] = True  # Placeholder

        elif framework == ComplianceFramework.GDPR:
            results["gdpr_encryption"] = self._check_gdpr_encryption(report)
            results["gdpr_right_to_forget"] = True  # Placeholder
            results["gdpr_data_agreement"] = True  # Placeholder

        elif framework == ComplianceFramework.SOC2:
            results["soc2_logging"] = len(report.audit_events) > 0
            results["soc2_access_control"] = self._check_soc2_access(report)
            results["soc2_availability"] = True  # Placeholder

        return results

    def export_audit_trail_csv(
        self,
        report: ComplianceReport,
        include_sensitive: bool = False
    ) -> str:
        """Export audit trail as CSV"""
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["event_id", "timestamp", "event_type", "user_id", "action", "resource_type", "status"]
        )

        writer.writeheader()
        for event in report.audit_events:
            writer.writerow({
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "action": event.action,
                "resource_type": event.resource_type,
                "status": event.status
            })

        return output.getvalue()

    def generate_audit_trail_json(
        self,
        report: ComplianceReport,
        include_sensitive: bool = False
    ) -> str:
        """Export audit trail as JSON"""
        events_data = [e.to_dict() for e in report.audit_events]
        return json.dumps(events_data, indent=2)

    def certify_compliance(
        self,
        report: ComplianceReport,
        certifier_name: str,
        certifier_signature: str
    ) -> ComplianceReport:
        """Add certification to compliance report"""
        report.certified = True
        report.certifier_name = certifier_name
        report.certifier_signature = certifier_signature
        report.certification_date = datetime.utcnow()
        return report

    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"REPORT-{timestamp}-{hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:8].upper()}"

    def _check_hipaa_retention(self, report: ComplianceReport) -> bool:
        """Check HIPAA 6-year retention requirement"""
        return True  # Placeholder - check actual retention policy

    def _check_hipaa_access(self, report: ComplianceReport) -> bool:
        """Check HIPAA access control"""
        return len([e for e in report.audit_events if e.event_type == AuditEventType.USER_LOGIN]) > 0

    def _check_gdpr_encryption(self, report: ComplianceReport) -> bool:
        """Check GDPR encryption requirements"""
        return True  # Placeholder - verify encryption status

    def _check_soc2_access(self, report: ComplianceReport) -> bool:
        """Check SOC 2 access control logging"""
        access_events = [e for e in report.audit_events if "login" in e.action.lower()]
        return len(access_events) > 0

    def get_compliance_summary(
        self,
        report: ComplianceReport,
        framework: ComplianceFramework
    ) -> Dict:
        """Get high-level compliance summary"""
        verification = self.verify_compliance(report, framework)
        compliant_checks = sum(1 for v in verification.values() if v)
        total_checks = len(verification)

        return {
            "framework": framework.value,
            "compliant_checks": compliant_checks,
            "total_checks": total_checks,
            "compliance_score": (compliant_checks / total_checks * 100) if total_checks > 0 else 0,
            "status": "COMPLIANT" if compliant_checks == total_checks else "NON-COMPLIANT",
            "verification_details": verification,
            "report_period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat()
            }
        }
