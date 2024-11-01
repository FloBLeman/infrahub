from collections import defaultdict
from typing import TYPE_CHECKING, Any, Optional

from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterTags,
    LogFilter,
    LogFilterFlowRunId,
)
from prefect.client.schemas.sorting import (
    FlowRunSort,
)
from pydantic import ConfigDict, Field

from infrahub.core.constants import TaskConclusion
from infrahub.core.node.standard import StandardNode
from infrahub.core.protocols import CoreNode
from infrahub.core.query.standard_node import StandardNodeQuery
from infrahub.core.query.task import TaskNodeCreateQuery, TaskNodeQuery, TaskNodeQueryWithLogs
from infrahub.core.timestamp import current_timestamp
from infrahub.database import InfrahubDatabase
from infrahub.utils import get_nested_dict
from infrahub.workflows.constants import TAG_NAMESPACE, WorkflowTag

from .task_log import TaskLog

if TYPE_CHECKING:
    from prefect.client.schemas.objects import Log as PrefectLog

LOG_LEVEL_MAPPING = {10: "debug", 20: "info", 30: "warning", 40: "error", 50: "critical"}


class Task(StandardNode):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    conclusion: TaskConclusion
    account_id: Optional[str] = Field(default=None, description="The ID of the account that created this task")
    created_at: str = Field(default_factory=current_timestamp, description="The time when this task was created")
    updated_at: str = Field(default_factory=current_timestamp, description="The time when this task was last updated")
    related_node: Optional[CoreNode] = Field(default=None, description="The Infrahub node that this object refers to")

    _exclude_attrs: list[str] = ["id", "uuid", "account_id", "_query", "related_node"]
    _query: type[StandardNodeQuery] = TaskNodeCreateQuery

    @property
    def related(self) -> CoreNode:
        if self.related_node:
            return self.related_node
        raise ValueError("The related_node field has not been populated")

    @classmethod
    async def query(
        cls,
        db: InfrahubDatabase,
        fields: dict[str, Any],
        limit: int,
        offset: int,
        ids: list[str],
        related_nodes: list[str],
    ) -> dict[str, Any]:
        log_fields = get_nested_dict(nested_dict=fields, keys=["edges", "node", "logs", "edges", "node"])
        count = None
        if "count" in fields:
            query = await TaskNodeQuery.init(db=db, ids=ids, related_nodes=related_nodes)
            count = await query.count(db=db)

        if log_fields:
            query = await TaskNodeQueryWithLogs.init(
                db=db, limit=limit, offset=offset, ids=ids, related_nodes=related_nodes
            )
            await query.execute(db=db)
        else:
            query = await TaskNodeQuery.init(db=db, limit=limit, offset=offset, ids=ids, related_nodes=related_nodes)
            await query.execute(db=db)

        nodes: list[dict] = []
        for result in query.get_results():
            related_node = result.get("rn")
            task_result = result.get_node("n")
            logs = []
            if log_fields:
                logs_results = result.get_node_collection("logs")
                logs = [
                    {
                        "node": await TaskLog.from_db(result, extras={"task_id": task_result.get("uuid")}).to_graphql(
                            fields=log_fields
                        )
                    }
                    for result in logs_results
                ]

            task = cls.from_db(task_result)
            nodes.append(
                {
                    "node": {
                        "title": task.title,
                        "conclusion": task.conclusion,
                        "related_node": related_node.get("uuid"),
                        "related_node_kind": related_node.get("kind"),
                        "created_at": task.created_at,
                        "updated_at": task.updated_at,
                        "id": task_result.get("uuid"),
                        "logs": {"edges": logs},
                    }
                }
            )

        return {"count": count, "edges": nodes}


class NewTask:
    @classmethod
    async def query(
        cls,
        fields: dict[str, Any],
        related_nodes: list[str],
        branch: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        nodes: list[dict] = []
        count = None

        log_fields = get_nested_dict(nested_dict=fields, keys=["edges", "node", "logs", "edges", "node"])
        logs_flow: dict[str, list[PrefectLog]] = defaultdict(list)

        async with get_client(sync_client=False) as client:
            tags = [TAG_NAMESPACE]

            if branch:
                tags.append(WorkflowTag.BRANCH.render(identifier=branch))

            # We only support one related node for now, need to investigate HOW (and IF) we can support more
            if related_nodes:
                tags.append(WorkflowTag.RELATED_NODE.render(identifier=related_nodes[0]))

            flow_run_filters = FlowRunFilter(
                tags=FlowRunFilterTags(all_=tags),
            )

            flows = await client.read_flow_runs(
                flow_run_filter=flow_run_filters,
                limit=limit,
                offset=offset,
                sort=FlowRunSort.START_TIME_DESC,
            )

            # For now count will just return the number of objects in the response
            # it won't work well with pagination but it doesn't look like Prefect provide a good option to count all flows
            if "count" in fields:
                count = len(flows)

            if log_fields:
                flow_ids = [flow.id for flow in flows]
                all_logs = await client.read_logs(log_filter=LogFilter(flow_run_id=LogFilterFlowRunId(any_=flow_ids)))
                for log in all_logs:
                    logs_flow[log.flow_run_id].append(log)

            for flow in flows:
                logs = []
                if log_fields:
                    logs = [
                        {
                            "node": {
                                "message": log.message,
                                "severity": LOG_LEVEL_MAPPING.get(log.level, "error"),
                                "timestamp": log.timestamp.to_iso8601_string(),
                            }
                        }
                        for log in logs_flow[flow.id]
                    ]

                nodes.append(
                    {
                        "node": {
                            "title": flow.name,
                            "conclusion": flow.state_name,
                            "related_node": "",
                            "related_node_kind": "",
                            "created_at": flow.created.to_iso8601_string(),
                            "updated_at": flow.updated.to_iso8601_string(),
                            "id": flow.id,
                            "logs": {"edges": logs},
                        }
                    }
                )

        return {"count": count or 0, "edges": nodes}
