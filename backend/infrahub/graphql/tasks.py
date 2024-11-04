from typing import List

from infrahub_sdk import InfrahubClient
from infrahub_sdk.node import InfrahubNode
from infrahub_sdk.utils import dict_hash
from prefect import flow

from infrahub.core.constants import InfrahubKind
from infrahub.graphql.models import RequestGraphQLQueryGroupUpdate
from infrahub.services import services
from infrahub.workflows.utils import add_branch_tag


async def _group_add_subscriber(
    client: InfrahubClient, group: InfrahubNode, subscribers: List[str], branch: str
) -> dict:
    subscribers_str = ["{ id: " + f'"{subscriber}"' + " }" for subscriber in subscribers]
    query = """
    mutation {
        RelationshipAdd(
            data: {
                id: "%s",
                name: "subscribers",
                nodes: [ %s ]
            }
        ) {
            ok
        }
    }
    """ % (
        group.id,
        ", ".join(subscribers_str),
    )

    return await client.execute_graphql(query=query, branch_name=branch, tracker="mutation-relationshipadd")


@flow(name="request_graphql_query_group_update")
async def request_graphql_query_group_update(model: RequestGraphQLQueryGroupUpdate) -> None:
    """Create or Update a GraphQLQueryGroup."""

    await add_branch_tag(branch_name=model.branch)
    service = services.service

    params_hash = dict_hash(model.params)
    group_name = f"{model.query_name}__{params_hash}"
    group_label = f"Query {model.query_name} Hash({params_hash[:8]})"
    group = await service.client.create(
        kind=InfrahubKind.GRAPHQLQUERYGROUP,
        branch=model.branch,
        name=group_name,
        label=group_label,
        group_type="internal",
        query=model.query_id,
        parameters=model.params,
        members=model.related_node_ids,
    )
    await group.save(allow_upsert=True)

    if model.subscribers:
        await _group_add_subscriber(
            client=service.client, group=group, subscribers=model.subscribers, branch=model.branch
        )
