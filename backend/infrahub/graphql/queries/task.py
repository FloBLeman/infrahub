from __future__ import annotations

from typing import TYPE_CHECKING, Any

from graphene import Field, Int, List, ObjectType, String
from infrahub_sdk.utils import extract_fields_first_node

from infrahub.core.task.task import NewTask as TaskNewNode
from infrahub.core.task.task import Task as TaskNode
from infrahub.graphql.types.task import TaskNodes

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from infrahub.graphql.initialization import GraphqlContext


class Tasks(ObjectType):
    edges = List(TaskNodes)
    count = Int()

    @staticmethod
    async def resolve(
        root: dict,  # pylint: disable=unused-argument
        info: GraphQLResolveInfo,
        limit: int = 10,
        offset: int = 0,
        ids: list | None = None,
        branch: str | None = None,
        related_node__ids: list | None = None,
    ) -> dict[str, Any]:
        related_nodes = related_node__ids or []
        ids = ids or []
        return await Tasks.query(
            info=info, branch=branch, limit=limit, offset=offset, ids=ids, related_nodes=related_nodes
        )

    @classmethod
    async def query(
        cls,
        info: GraphQLResolveInfo,
        limit: int,
        offset: int,
        related_nodes: list[str],
        ids: list[str],
        branch: str | None,
    ) -> dict[str, Any]:
        context: GraphqlContext = info.context
        fields = await extract_fields_first_node(info)

        # During the migration, query both Prefect and Infrahub to get the list of tasks
        if not branch:
            infrahub_tasks = await TaskNode.query(
                db=context.db, fields=fields, limit=limit, offset=offset, ids=ids, related_nodes=related_nodes
            )
        else:
            infrahub_tasks = {}

        prefect_tasks = await TaskNewNode.query(
            fields=fields, branch=branch, related_nodes=related_nodes, limit=limit, offset=offset
        )

        return {
            "count": infrahub_tasks.get("count", 0) + prefect_tasks.get("count", 0),
            "edges": infrahub_tasks.get("edges", []) + prefect_tasks.get("edges", []),
        }


Task = Field(
    Tasks,
    resolver=Tasks.resolve,
    limit=Int(required=False),
    offset=Int(required=False),
    related_node__ids=List(String),
    branch=String(required=False),
    ids=List(String),
)
