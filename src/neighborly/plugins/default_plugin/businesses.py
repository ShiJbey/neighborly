#
# restaurant_type = BusinessArchetype(
#     name="Restaurant",
#     name_pattern="#restaurant_name#",
#     hours="10:00-21:00",
#     owner_type="Proprietor",
#     employees={
#         "Cook": 1,
#         "Server": 2,
#         "Host": 1,
#     },
# )
#
# bar_type = BusinessArchetype(
#     name="Bar",
#     name_pattern="#bar_name#",
#     hours="RFS 21:00-2:00",
#     owner_type="Proprietor",
#     employees={
#         "Bartender": 2,
#         "DJ": 1,
#         "Security": 1,
#         "Cook": 1
#     }
# )
#
# department_store_type = BusinessArchetype(
#     name="Department Store",
#     name_pattern="Department Store",
#     hours="MTWRF 9:00-17:00, SU 10:00-15:00",
#     owner_type="Owner",
#     employees={
#         "Cashier": 1,
#         "Sales Associate": 2,
#         "Manager": 1,
#     }
# )
#
from neighborly.core.business import OccupationDefinition

cashier_type = OccupationDefinition(
    name="Cashier",
    level=1,
)

sales_associate_type = OccupationDefinition(
    name="Sales Associate",
    level=2,
)

manager_type = OccupationDefinition(
    name="Manager",
    level=3
)

dj_type = OccupationDefinition(
    name="DJ",
    level=2
)

bartender_type = OccupationDefinition(
    name="Bartender",
    level=2
)

security_type = OccupationDefinition(
    name="Security",
    level=2
)

cook_type = OccupationDefinition(
    name="Cook",
    level=2
)

owner_type = OccupationDefinition(
    name="Owner",
    level=4,
)

proprietor_type = OccupationDefinition(
    name="Proprietor",
    level=4,
)
