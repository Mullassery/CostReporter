"""
Multi-organization and department tracking system.
Enables multi-tenant cost tracking with hierarchical organization structure.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class UserRole(Enum):
    """User roles in organization"""
    ADMIN = "admin"  # Can manage org, users, all departments
    MANAGER = "manager"  # Can manage departments, view all costs
    DEPARTMENT_LEAD = "department_lead"  # Can manage own department
    MEMBER = "member"  # Can view own department costs
    VIEWER = "viewer"  # Read-only access


class AccessLevel(Enum):
    """Data access levels"""
    ORG_WIDE = "org_wide"  # All departments
    DEPARTMENT = "department"  # Single department
    PERSONAL = "personal"  # Only own operations


@dataclass
class Organization:
    """Organization entity"""
    org_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    billing_contact: str = ""
    billing_email: str = ""
    max_users: int = 100
    max_departments: int = 20
    features: Dict[str, bool] = field(default_factory=lambda: {
        "cost_anomaly_detection": True,
        "forecasting": True,
        "recommendations": True,
        "multi_region": True,
        "sso": False
    })
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Department:
    """Department within organization"""
    dept_id: str
    org_id: str
    name: str
    description: str = ""
    parent_dept_id: Optional[str] = None  # For nested departments
    budget_monthly: float = 0.0
    budget_alert_threshold: float = 0.8  # Alert at 80%
    created_at: datetime = field(default_factory=datetime.utcnow)
    cost_center_id: str = ""  # For billing/accounting
    metadata: Dict[str, Any] = field(default_factory=dict)
    child_departments: List[str] = field(default_factory=list)


@dataclass
class DepartmentUser:
    """User assigned to department"""
    user_id: str
    org_id: str
    dept_id: str
    role: UserRole = UserRole.MEMBER
    access_level: AccessLevel = AccessLevel.DEPARTMENT
    is_active: bool = True
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostAllocation:
    """Cost allocation rule for splitting costs"""
    allocation_id: str
    org_id: str
    source_dept_id: str  # Department where cost occurred
    allocation_rules: List[Dict[str, Any]] = field(default_factory=list)
    # allocation_rules format: [{"dept_id": "...", "percentage": 50}, ...]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


class OrganizationManager:
    """Manage organizations and departments"""

    def __init__(self):
        self.organizations: Dict[str, Organization] = {}
        self.departments: Dict[str, Department] = {}
        self.users: Dict[str, DepartmentUser] = {}
        self.cost_allocations: Dict[str, CostAllocation] = {}

    def create_organization(
        self,
        org_id: str,
        name: str,
        description: str = "",
        billing_contact: str = ""
    ) -> Organization:
        """Create new organization"""
        if org_id in self.organizations:
            raise ValueError(f"Organization {org_id} already exists")

        org = Organization(
            org_id=org_id,
            name=name,
            description=description,
            billing_contact=billing_contact
        )

        self.organizations[org_id] = org
        return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.organizations.get(org_id)

    def create_department(
        self,
        org_id: str,
        dept_id: str,
        name: str,
        description: str = "",
        parent_dept_id: Optional[str] = None,
        budget_monthly: float = 0.0
    ) -> Department:
        """Create department within organization"""
        if org_id not in self.organizations:
            raise ValueError(f"Organization {org_id} not found")

        # Check parent department if nested
        if parent_dept_id:
            parent_key = f"{org_id}:{parent_dept_id}"
            if parent_key not in self.departments:
                raise ValueError(f"Parent department {parent_dept_id} not found")

        dept_key = f"{org_id}:{dept_id}"
        if dept_key in self.departments:
            raise ValueError(f"Department {dept_id} already exists in org {org_id}")

        dept = Department(
            dept_id=dept_id,
            org_id=org_id,
            name=name,
            description=description,
            parent_dept_id=parent_dept_id,
            budget_monthly=budget_monthly
        )

        self.departments[dept_key] = dept

        # Add to parent's children
        if parent_dept_id:
            parent_key = f"{org_id}:{parent_dept_id}"
            self.departments[parent_key].child_departments.append(dept_id)

        return dept

    def get_department(self, org_id: str, dept_id: str) -> Optional[Department]:
        """Get department by ID"""
        key = f"{org_id}:{dept_id}"
        return self.departments.get(key)

    def get_departments_by_org(self, org_id: str) -> List[Department]:
        """Get all departments in organization"""
        return [
            dept for dept in self.departments.values()
            if dept.org_id == org_id
        ]

    def get_department_hierarchy(self, org_id: str, dept_id: str) -> Dict[str, Any]:
        """Get full department hierarchy starting from dept"""
        dept = self.get_department(org_id, dept_id)
        if not dept:
            return {}

        hierarchy = {
            "dept_id": dept.dept_id,
            "name": dept.name,
            "children": []
        }

        # Add child departments recursively
        for child_id in dept.child_departments:
            hierarchy["children"].append(
                self.get_department_hierarchy(org_id, child_id)
            )

        return hierarchy

    def assign_user_to_department(
        self,
        user_id: str,
        org_id: str,
        dept_id: str,
        role: UserRole = UserRole.MEMBER
    ) -> DepartmentUser:
        """Assign user to department"""
        if org_id not in self.organizations:
            raise ValueError(f"Organization {org_id} not found")

        dept_key = f"{org_id}:{dept_id}"
        if dept_key not in self.departments:
            raise ValueError(f"Department {dept_id} not found in org {org_id}")

        # Determine access level based on role
        access_level = AccessLevel.DEPARTMENT
        if role == UserRole.ADMIN:
            access_level = AccessLevel.ORG_WIDE

        user_key = f"{org_id}:{user_id}"
        dept_user = DepartmentUser(
            user_id=user_id,
            org_id=org_id,
            dept_id=dept_id,
            role=role,
            access_level=access_level
        )

        self.users[user_key] = dept_user
        return dept_user

    def get_user_departments(self, org_id: str, user_id: str) -> List[Department]:
        """Get departments user has access to"""
        user_key = f"{org_id}:{user_id}"
        user = self.users.get(user_key)

        if not user:
            return []

        if user.access_level == AccessLevel.ORG_WIDE:
            return self.get_departments_by_org(org_id)
        else:
            dept = self.get_department(org_id, user.dept_id)
            return [dept] if dept else []

    def can_user_access_department(
        self,
        user_id: str,
        org_id: str,
        dept_id: str
    ) -> bool:
        """Check if user can access department"""
        user_key = f"{org_id}:{user_id}"
        user = self.users.get(user_key)

        if not user:
            return False

        if user.access_level == AccessLevel.ORG_WIDE:
            return True

        return user.dept_id == dept_id

    def create_cost_allocation(
        self,
        org_id: str,
        source_dept_id: str,
        allocation_rules: List[Dict[str, Any]]
    ) -> CostAllocation:
        """Create cost allocation rule"""
        allocation_id = f"alloc_{org_id}_{source_dept_id}_{datetime.utcnow().timestamp()}"

        allocation = CostAllocation(
            allocation_id=allocation_id,
            org_id=org_id,
            source_dept_id=source_dept_id,
            allocation_rules=allocation_rules
        )

        self.cost_allocations[allocation_id] = allocation
        return allocation

    def apply_cost_allocation(
        self,
        cost: float,
        org_id: str,
        source_dept_id: str
    ) -> Dict[str, float]:
        """Apply allocation rules to cost"""
        allocated = {}

        # Find active allocation for this department
        active_allocations = [
            alloc for alloc in self.cost_allocations.values()
            if alloc.org_id == org_id and
               alloc.source_dept_id == source_dept_id and
               alloc.is_active
        ]

        if not active_allocations:
            # No allocation, cost stays with source department
            allocated[source_dept_id] = cost
            return allocated

        allocation = active_allocations[0]  # Use first active allocation
        total_percentage = sum(rule.get("percentage", 0) for rule in allocation.allocation_rules)

        if total_percentage != 100:
            raise ValueError(f"Allocation percentages must sum to 100, got {total_percentage}")

        for rule in allocation.allocation_rules:
            target_dept_id = rule.get("dept_id")
            percentage = rule.get("percentage", 0)
            allocated[target_dept_id] = cost * (percentage / 100)

        return allocated


class CostAggregator:
    """Aggregate costs across organizational hierarchy"""

    def __init__(self, org_manager: OrganizationManager):
        self.org_manager = org_manager
        self.costs: Dict[str, float] = {}  # key: "org_id:dept_id", value: cost

    def record_cost(self, org_id: str, dept_id: str, cost: float):
        """Record cost for department"""
        key = f"{org_id}:{dept_id}"
        self.costs[key] = self.costs.get(key, 0) + cost

    def get_department_cost(self, org_id: str, dept_id: str) -> float:
        """Get total cost for department (excluding children)"""
        key = f"{org_id}:{dept_id}"
        return self.costs.get(key, 0)

    def get_department_total_cost(self, org_id: str, dept_id: str) -> float:
        """Get total cost including all child departments"""
        dept = self.org_manager.get_department(org_id, dept_id)
        if not dept:
            return 0

        total = self.get_department_cost(org_id, dept_id)

        # Add child department costs
        for child_id in dept.child_departments:
            total += self.get_department_total_cost(org_id, child_id)

        return total

    def get_org_total_cost(self, org_id: str) -> float:
        """Get total cost for entire organization"""
        return sum(
            cost for key, cost in self.costs.items()
            if key.startswith(f"{org_id}:")
        )

    def get_department_cost_breakdown(
        self,
        org_id: str,
        dept_id: str
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown for department"""
        dept = self.org_manager.get_department(org_id, dept_id)
        if not dept:
            return {}

        direct_cost = self.get_department_cost(org_id, dept_id)
        child_costs = sum(
            self.get_department_total_cost(org_id, child_id)
            for child_id in dept.child_departments
        )

        return {
            "dept_id": dept_id,
            "dept_name": dept.name,
            "direct_cost": direct_cost,
            "child_departments_cost": child_costs,
            "total_cost": direct_cost + child_costs,
            "budget_monthly": dept.budget_monthly,
            "budget_utilization_percent": (
                ((direct_cost + child_costs) / dept.budget_monthly * 100)
                if dept.budget_monthly > 0 else 0
            ),
            "is_over_budget": (direct_cost + child_costs) > dept.budget_monthly
        }

    def get_org_cost_breakdown(self, org_id: str) -> Dict[str, Any]:
        """Get cost breakdown for entire organization"""
        org = self.org_manager.get_organization(org_id)
        if not org:
            return {}

        departments = self.org_manager.get_departments_by_org(org_id)
        dept_costs = []
        total_cost = 0

        for dept in departments:
            if not dept.parent_dept_id:  # Only root departments
                breakdown = self.get_department_cost_breakdown(org_id, dept.dept_id)
                dept_costs.append(breakdown)
                total_cost += breakdown["total_cost"]

        return {
            "org_id": org_id,
            "org_name": org.name,
            "total_cost": total_cost,
            "departments": dept_costs,
            "department_count": len(departments)
        }

    def get_user_visible_costs(
        self,
        user_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get costs visible to user based on permissions"""
        departments = self.org_manager.get_user_departments(org_id, user_id)

        visible_costs = {}
        for dept in departments:
            breakdown = self.get_department_cost_breakdown(org_id, dept.dept_id)
            visible_costs[dept.dept_id] = breakdown

        return {
            "user_id": user_id,
            "org_id": org_id,
            "visible_departments": visible_costs,
            "total_visible_cost": sum(c["total_cost"] for c in visible_costs.values())
        }

    def compare_departments(
        self,
        org_id: str,
        dept_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Compare costs across departments"""
        comparisons = []

        for dept_id in dept_ids:
            breakdown = self.get_department_cost_breakdown(org_id, dept_id)
            comparisons.append(breakdown)

        # Sort by total cost
        comparisons.sort(key=lambda x: x["total_cost"], reverse=True)

        return comparisons

    def forecast_org_costs(
        self,
        org_id: str,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Forecast organization costs"""
        current_cost = self.get_org_total_cost(org_id)
        daily_cost = current_cost  # Simplified: assume daily = current

        return {
            "org_id": org_id,
            "current_total_cost": current_cost,
            "daily_average": daily_cost,
            "projected_30_day": daily_cost * 30,
            "projected_90_day": daily_cost * 90,
            "projected_annual": daily_cost * 365
        }
