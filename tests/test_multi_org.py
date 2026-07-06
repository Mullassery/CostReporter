"""
Tests for multi-organization and department tracking.
"""

import pytest
from pycostaudit.multi_org_manager import (
    OrganizationManager,
    CostAggregator,
    UserRole,
    AccessLevel,
    Organization,
    Department
)


@pytest.fixture
def org_manager():
    """Create organization manager"""
    return OrganizationManager()


@pytest.fixture
def sample_org(org_manager):
    """Create sample organization"""
    return org_manager.create_organization(
        "acme",
        "ACME Corporation",
        "A sample organization",
        "billing@acme.com"
    )


class TestOrganizationManagement:
    """Test organization management"""

    def test_create_organization(self, org_manager):
        """Test creating organization"""
        org = org_manager.create_organization(
            "techcorp",
            "TechCorp Inc",
            "A tech company"
        )

        assert org.org_id == "techcorp"
        assert org.name == "TechCorp Inc"
        assert org_manager.get_organization("techcorp") == org

    def test_duplicate_organization(self, org_manager, sample_org):
        """Test duplicate organization fails"""
        with pytest.raises(ValueError):
            org_manager.create_organization("acme", "Another ACME")

    def test_get_organization(self, org_manager, sample_org):
        """Test getting organization"""
        org = org_manager.get_organization("acme")
        assert org is not None
        assert org.org_id == "acme"


class TestDepartmentManagement:
    """Test department management"""

    def test_create_department(self, org_manager, sample_org):
        """Test creating department"""
        dept = org_manager.create_department(
            "acme",
            "engineering",
            "Engineering Department",
            budget_monthly=5000.0
        )

        assert dept.dept_id == "engineering"
        assert dept.org_id == "acme"
        assert dept.budget_monthly == 5000.0

    def test_create_nested_department(self, org_manager, sample_org):
        """Test creating nested departments"""
        eng_dept = org_manager.create_department(
            "acme",
            "engineering",
            "Engineering"
        )

        backend_dept = org_manager.create_department(
            "acme",
            "backend",
            "Backend Team",
            parent_dept_id="engineering"
        )

        assert backend_dept.parent_dept_id == "engineering"
        assert "backend" in eng_dept.child_departments

    def test_get_departments_by_org(self, org_manager, sample_org):
        """Test getting departments by org"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        depts = org_manager.get_departments_by_org("acme")
        assert len(depts) == 2

    def test_invalid_parent_department(self, org_manager, sample_org):
        """Test creating dept with invalid parent"""
        with pytest.raises(ValueError):
            org_manager.create_department(
                "acme",
                "backend",
                "Backend",
                parent_dept_id="nonexistent"
            )

    def test_department_hierarchy(self, org_manager, sample_org):
        """Test getting department hierarchy"""
        org_manager.create_department("acme", "engineering", "Engineering")
        org_manager.create_department(
            "acme", "backend", "Backend", parent_dept_id="engineering"
        )
        org_manager.create_department(
            "acme", "frontend", "Frontend", parent_dept_id="engineering"
        )

        hierarchy = org_manager.get_department_hierarchy("acme", "engineering")

        assert hierarchy["dept_id"] == "engineering"
        assert len(hierarchy["children"]) == 2


class TestUserAssignment:
    """Test user assignment to departments"""

    def test_assign_user_to_department(self, org_manager, sample_org):
        """Test assigning user to department"""
        dept = org_manager.create_department("acme", "eng", "Engineering")

        user = org_manager.assign_user_to_department(
            "alice",
            "acme",
            "eng",
            UserRole.DEPARTMENT_LEAD
        )

        assert user.user_id == "alice"
        assert user.dept_id == "eng"
        assert user.role == UserRole.DEPARTMENT_LEAD

    def test_admin_user_has_org_access(self, org_manager, sample_org):
        """Test admin user has org-wide access"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        admin = org_manager.assign_user_to_department(
            "admin",
            "acme",
            "eng",
            UserRole.ADMIN
        )

        assert admin.access_level == AccessLevel.ORG_WIDE

    def test_get_user_departments(self, org_manager, sample_org):
        """Test getting departments user has access to"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        # Regular member
        org_manager.assign_user_to_department(
            "alice",
            "acme",
            "eng",
            UserRole.MEMBER
        )

        depts = org_manager.get_user_departments("acme", "alice")
        assert len(depts) == 1
        assert depts[0].dept_id == "eng"

    def test_can_user_access_department(self, org_manager, sample_org):
        """Test department access permission"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        org_manager.assign_user_to_department(
            "alice",
            "acme",
            "eng",
            UserRole.MEMBER
        )

        assert org_manager.can_user_access_department("alice", "acme", "eng")
        assert not org_manager.can_user_access_department("alice", "acme", "sales")


class TestCostAllocation:
    """Test cost allocation rules"""

    def test_create_cost_allocation(self, org_manager, sample_org):
        """Test creating cost allocation"""
        org_manager.create_department("acme", "shared", "Shared Resources")
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        allocation = org_manager.create_cost_allocation(
            "acme",
            "shared",
            [
                {"dept_id": "eng", "percentage": 60},
                {"dept_id": "sales", "percentage": 40}
            ]
        )

        assert allocation.is_active
        assert len(allocation.allocation_rules) == 2

    def test_apply_cost_allocation(self, org_manager, sample_org):
        """Test applying cost allocation"""
        org_manager.create_department("acme", "shared", "Shared")
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        org_manager.create_cost_allocation(
            "acme",
            "shared",
            [
                {"dept_id": "eng", "percentage": 60},
                {"dept_id": "sales", "percentage": 40}
            ]
        )

        allocated = org_manager.apply_cost_allocation(100.0, "acme", "shared")

        assert allocated["eng"] == 60.0
        assert allocated["sales"] == 40.0

    def test_allocation_without_rules(self, org_manager, sample_org):
        """Test cost stays with source when no allocation"""
        org_manager.create_department("acme", "eng", "Engineering")

        allocated = org_manager.apply_cost_allocation(100.0, "acme", "eng")

        assert allocated["eng"] == 100.0


class TestCostAggregation:
    """Test cost aggregation"""

    def test_record_and_get_cost(self, org_manager, sample_org):
        """Test recording and retrieving cost"""
        org_manager.create_department("acme", "eng", "Engineering")
        agg = CostAggregator(org_manager)

        agg.record_cost("acme", "eng", 100.0)
        agg.record_cost("acme", "eng", 50.0)

        assert agg.get_department_cost("acme", "eng") == 150.0

    def test_department_total_cost_with_children(self, org_manager, sample_org):
        """Test getting total cost including children"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department(
            "acme", "backend", "Backend", parent_dept_id="eng"
        )

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 100.0)
        agg.record_cost("acme", "backend", 50.0)

        assert agg.get_department_cost("acme", "eng") == 100.0
        assert agg.get_department_total_cost("acme", "eng") == 150.0

    def test_org_total_cost(self, org_manager, sample_org):
        """Test getting organization total cost"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 100.0)
        agg.record_cost("acme", "sales", 50.0)

        assert agg.get_org_total_cost("acme") == 150.0

    def test_department_cost_breakdown(self, org_manager, sample_org):
        """Test detailed department cost breakdown"""
        dept = org_manager.create_department(
            "acme", "eng", "Engineering", budget_monthly=500.0
        )

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 300.0)

        breakdown = agg.get_department_cost_breakdown("acme", "eng")

        assert breakdown["dept_id"] == "eng"
        assert breakdown["direct_cost"] == 300.0
        assert breakdown["budget_monthly"] == 500.0
        assert breakdown["budget_utilization_percent"] == 60.0
        assert not breakdown["is_over_budget"]

    def test_budget_exceeded(self, org_manager, sample_org):
        """Test budget exceeded detection"""
        org_manager.create_department(
            "acme", "eng", "Engineering", budget_monthly=100.0
        )

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 150.0)

        breakdown = agg.get_department_cost_breakdown("acme", "eng")

        assert breakdown["is_over_budget"]
        assert breakdown["budget_utilization_percent"] == 150.0

    def test_org_cost_breakdown(self, org_manager, sample_org):
        """Test organization cost breakdown"""
        org_manager.create_department("acme", "eng", "Engineering", budget_monthly=1000.0)
        org_manager.create_department("acme", "sales", "Sales", budget_monthly=500.0)

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 300.0)
        agg.record_cost("acme", "sales", 200.0)

        breakdown = agg.get_org_cost_breakdown("acme")

        assert breakdown["total_cost"] == 500.0
        assert len(breakdown["departments"]) == 2

    def test_user_visible_costs(self, org_manager, sample_org):
        """Test getting costs visible to user"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        org_manager.assign_user_to_department("alice", "acme", "eng", UserRole.MEMBER)

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 300.0)
        agg.record_cost("acme", "sales", 200.0)

        visible = agg.get_user_visible_costs("alice", "acme")

        assert visible["total_visible_cost"] == 300.0
        assert "eng" in visible["visible_departments"]
        assert "sales" not in visible["visible_departments"]

    def test_compare_departments(self, org_manager, sample_org):
        """Test comparing departments"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")
        org_manager.create_department("acme", "ops", "Operations")

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 500.0)
        agg.record_cost("acme", "sales", 300.0)
        agg.record_cost("acme", "ops", 200.0)

        comparison = agg.compare_departments(
            "acme",
            ["eng", "sales", "ops"]
        )

        # Should be sorted by cost (highest first)
        assert comparison[0]["dept_id"] == "eng"
        assert comparison[1]["dept_id"] == "sales"
        assert comparison[2]["dept_id"] == "ops"

    def test_forecast_org_costs(self, org_manager, sample_org):
        """Test forecasting organization costs"""
        org_manager.create_department("acme", "eng", "Engineering")
        org_manager.create_department("acme", "sales", "Sales")

        agg = CostAggregator(org_manager)
        agg.record_cost("acme", "eng", 1000.0)
        agg.record_cost("acme", "sales", 500.0)

        forecast = agg.forecast_org_costs("acme", days_ahead=30)

        assert forecast["current_total_cost"] == 1500.0
        assert forecast["projected_30_day"] == 1500.0 * 30
        assert forecast["projected_annual"] == 1500.0 * 365


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
