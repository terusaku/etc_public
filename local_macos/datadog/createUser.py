from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.users_api import UsersApi
from datadog_api_client.v2.model.user_create_attributes import UserCreateAttributes
from datadog_api_client.v2.model.user_create_data import UserCreateData
from datadog_api_client.v2.model.user_create_request import UserCreateRequest
from datadog_api_client.v2.model.users_type import UsersType
from datadog_api_client.v2.model.user_relationships import UserRelationships
from datadog_api_client.v2.model.relationship_to_roles import RelationshipToRoles
from datadog_api_client.v2.model.relationship_to_role_data import RelationshipToRoleData
from datadog_api_client.v2.model.roles_type import RolesType

# Prerequisites:
# Set the below Environment Variables, and execute `python ./createUser.py`
# DD_SITE=datadoghq.com
# DD_API_KEY
# DD_APP_KEY


data = [
    # ["title", "name", "email"],
    ["Haruka Yamamoto", "山本春香", "furaharuk@hoshinoresorts.com"],
    ["Takata Yasuo", "高田康穂", "brainjuggler@hoshinoresorts.com"],
    ["Atsushi Okada", "岡田敦", "molehand.okada@hoshinoresorts.com"],
    ["Kazuki Komori", "小森一樹", "uraura_komori@hoshinoresorts.com"],
    ["Keiichiro Kawano", "河野圭一郎", "bird-bell-and-i@hoshinoresorts.com"],
]

for user_info in data:
    body = UserCreateRequest(
        data=UserCreateData(
            type=UsersType.USERS,
            attributes=UserCreateAttributes(
                title=user_info[0],
                name=user_info[1],
                email=user_info[2],
            ),
            relationships=UserRelationships(
                roles=RelationshipToRoles(
                    data=[
                        RelationshipToRoleData(
                            # id is role_id, which can be found in URL.
                            # https://app.datadoghq.com/organization-settings/roles?role_id={role_id}
                            id="508cb732-e15e-11e8-ad8f-f3273b623d29",
                            type=RolesType.ROLES,
                        )
                    ]
                )
            ),
        ),
    )

    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_instance = UsersApi(api_client)
        response = api_instance.create_user(body=body)

        print(response)
