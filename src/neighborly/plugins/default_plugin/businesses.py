from neighborly.core.business import OccupationType, BusinessType

restaurant_type = BusinessType(
    name="Restaurant",
    name_pattern="#restaurant_name#",
    hours="10:00-21:00",
    owner="Proprietor",
    employees={
        "Cook": 1,
        "Server": 2,
        "Host": 1,
    },
)

bar_type = BusinessType(
    name="Bar",
    name_pattern="#bar_name#",
    hours="RFS 21:00-2:00",
    owner="Proprietor",
    employees={
        "Bartender": 2,
        "DJ": 1,
        "Security": 1,
        "Cook": 1
    }
)

department_store_type = BusinessType(
    name="Department Store",
    name_pattern="Department Store",
    hours="MTWRF 9:00-17:00, SU 10:00-15:00",
    owner="Owner",
    employees={
        "Cashier": 1,
        "Sales Associate": 2,
        "Manager": 1,
    }
)

cashier_type = OccupationType(
    name="Cashier",
    level=1,
)

sales_associate_type = OccupationType(
    name="Sales Associate",
    level=2,
)

manager_type = OccupationType(
    name="Manager",
    level=3
)

dj_type = OccupationType(
    name="DJ",
    level=2
)

bartender_type = OccupationType(
    name="Bartender",
    level=2
)

security_type = OccupationType(
    name="Security",
    level=2
)

cook_type = OccupationType(
    name="Cook",
    level=2
)

owner_type = OccupationType(
    name="Owner",
    level=4,
)

proprietor_type = OccupationType(
    name="Proprietor",
    level=4,
)
