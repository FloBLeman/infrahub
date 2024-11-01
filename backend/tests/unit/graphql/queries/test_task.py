from typing import Any, Dict
from uuid import uuid4

import pytest
from graphql import ExecutionResult, graphql
from prefect.client.orchestration import PrefectClient, get_client
from prefect.states import State
from prefect.testing.utilities import prefect_test_harness

from infrahub.core.branch import Branch
from infrahub.core.constants import InfrahubKind
from infrahub.core.node import Node
from infrahub.database import InfrahubDatabase
from infrahub.graphql.initialization import prepare_graphql_params
from infrahub.tasks.dummy import dummy_flow
from infrahub.workflows.constants import TAG_NAMESPACE, WorkflowTag

CREATE_TASK = """
mutation CreateTask(
    $conclusion: TaskConclusion!,
    $title: String!,
    $task_id: UUID,
    $created_by: String,
    $related_node: String!,
    $logs: [RelatedTaskLogCreateInput]
    ) {
    InfrahubTaskCreate(
        data: {
            id: $task_id,
            created_by: $created_by,
            title: $title,
            conclusion: $conclusion,
            related_node: $related_node,
            logs: $logs
        }
    ) {
        ok
        object {
            id
        }
    }
}
"""

QUERY_TASK = """
query TaskQuery(
    $related_nodes: [String]
) {
  InfrahubTask(related_node__ids: $related_nodes) {
    count
    edges {
      node {
        conclusion
        created_at
        id
        related_node
        related_node_kind
        title
        updated_at
      }
    }
  }
}
"""

QUERY_TASK_WITH_LOGS = """
query TaskQuery(
    $related_nodes: [String]
) {
  InfrahubTask(related_node__ids: $related_nodes) {
    count
    edges {
      node {
        conclusion
        created_at
        id
        related_node
        related_node_kind
        title
        updated_at
        logs {
            edges {
                node {
                    id
                    message
                    severity
                    timestamp
                }
            }
        }
      }
    }
  }
}
"""


@pytest.fixture
def local_prefect_server():
    with prefect_test_harness():
        yield


@pytest.fixture
async def tag_blue(db: InfrahubDatabase, default_branch: Branch) -> Node:
    blue = await Node.init(db=db, schema=InfrahubKind.TAG, branch=default_branch)
    await blue.new(db=db, name="Blue", description="The Blue tag")
    await blue.save(db=db)
    return blue


@pytest.fixture
async def account_bob(db: InfrahubDatabase, default_branch: Branch) -> Node:
    bob = await Node.init(db=db, schema=InfrahubKind.ACCOUNT, branch=default_branch)
    await bob.new(db=db, name="bob", password=str(uuid4()))
    await bob.save(db=db)
    return bob


@pytest.fixture
async def prefect_client(local_prefect_server):
    async with get_client(sync_client=False) as client:
        yield client


@pytest.fixture
async def flow_runs_data(prefect_client: PrefectClient, tag_blue):
    branch1_tag = WorkflowTag.BRANCH.render(identifier="branch1")

    items = [
        await prefect_client.create_flow_run(
            flow=dummy_flow,
            name="dummy-completed-internal-tag-br1",
            parameters={"firstname": "john", "lastname": "doe"},
            tags=[TAG_NAMESPACE, branch1_tag],
            state=State(type="COMPLETED"),
        ),
        await prefect_client.create_flow_run(
            flow=dummy_flow,
            name="dummy-completed-no-tag",
            parameters={"firstname": "jane", "lastname": "doe"},
            tags=[],
            state=State(type="COMPLETED"),
        ),
        await prefect_client.create_flow_run(
            flow=dummy_flow,
            name="dummy-scheduled-internal-tag",
            parameters={"firstname": "xxxx", "lastname": "yyy"},
            tags=[TAG_NAMESPACE, WorkflowTag.RELATED_NODE.render(identifier=tag_blue.get_id())],
            state=State(type="SCHEDULED"),
        ),
    ]

    return {item.name: item for item in items}


async def run_query(db: InfrahubDatabase, branch: Branch, query: str, variables: Dict[str, Any]) -> ExecutionResult:
    gql_params = prepare_graphql_params(db=db, include_subscription=False, branch=branch)
    return await graphql(
        schema=gql_params.schema,
        source=query,
        context_value=gql_params.context,
        root_value=None,
        variable_values=variables,
    )


async def test_task_query_infrahub(
    db: InfrahubDatabase, default_branch: Branch, register_core_models_schema: None, local_prefect_server
):
    red = await Node.init(db=db, schema=InfrahubKind.TAG, branch=default_branch)
    await red.new(db=db, name="Red", description="The Red tag")
    await red.save(db=db)

    green = await Node.init(db=db, schema=InfrahubKind.TAG, branch=default_branch)
    await green.new(db=db, name="Green", description="The Green tag")
    await green.save(db=db)

    blue = await Node.init(db=db, schema=InfrahubKind.TAG, branch=default_branch)
    await blue.new(db=db, name="Blue", description="The Blue tag")
    await blue.save(db=db)

    bob = await Node.init(db=db, schema=InfrahubKind.ACCOUNT, branch=default_branch)
    await bob.new(db=db, name="bob", password=str(uuid4()))
    await bob.save(db=db)

    result = await run_query(
        db=db,
        branch=default_branch,
        query=CREATE_TASK,
        variables={
            "conclusion": "UNKNOWN",
            "title": "Blue Task 1",
            "related_node": blue.get_id(),
            "created_by": bob.get_id(),
            "logs": {"message": "Starting task", "severity": "INFO"},
        },
    )
    assert result.errors is None
    assert result.data

    result = await run_query(
        db=db,
        branch=default_branch,
        query=CREATE_TASK,
        variables={
            "conclusion": "UNKNOWN",
            "title": "Red Task 1",
            "related_node": red.get_id(),
            "created_by": bob.get_id(),
            "logs": {"message": "Starting task", "severity": "INFO"},
        },
    )
    assert result.errors is None
    assert result.data

    result = await run_query(
        db=db,
        branch=default_branch,
        query=CREATE_TASK,
        variables={
            "conclusion": "UNKNOWN",
            "title": "Green Task 1",
            "related_node": green.get_id(),
            "created_by": bob.get_id(),
            "logs": {"message": "Starting task", "severity": "INFO"},
        },
    )
    assert result.errors is None
    assert result.data

    result = await run_query(
        db=db,
        branch=default_branch,
        query=CREATE_TASK,
        variables={
            "conclusion": "UNKNOWN",
            "title": "Blue Task 1",
            "related_node": blue.get_id(),
            "created_by": bob.get_id(),
            "logs": {"message": "Starting task", "severity": "INFO"},
        },
    )
    assert result.errors is None
    assert result.data

    result = await run_query(
        db=db,
        branch=default_branch,
        query=CREATE_TASK,
        variables={
            "conclusion": "SUCCESS",
            "title": "Blue Task 2",
            "related_node": blue.get_id(),
            "created_by": bob.get_id(),
            "logs": [
                {"message": "Starting task", "severity": "INFO"},
                {"message": "Finalizing task", "severity": "INFO"},
            ],
        },
    )
    assert result.errors is None
    assert result.data

    all_tasks = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY_TASK,
        variables={},
    )
    assert all_tasks.errors is None
    assert all_tasks.data
    assert all_tasks.data["InfrahubTask"]["count"] == 5

    blue_tasks = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY_TASK,
        variables={"related_nodes": blue.get_id()},
    )
    assert blue_tasks.errors is None
    assert blue_tasks.data
    assert blue_tasks.data["InfrahubTask"]["count"] == 3

    red_blue_tasks = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY_TASK,
        variables={"related_nodes": [red.get_id(), blue.get_id()]},
    )
    assert red_blue_tasks.errors is None
    assert red_blue_tasks.data
    assert red_blue_tasks.data["InfrahubTask"]["count"] == 4

    all_logs = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY_TASK_WITH_LOGS,
        variables={},
    )
    assert all_logs.errors is None
    assert all_logs.data
    logs = []
    for task in all_logs.data["InfrahubTask"]["edges"]:
        [logs.append(log) for log in task["node"]["logs"]["edges"]]

    assert len(logs) == 6


async def test_task_query_prefect(
    db: InfrahubDatabase, default_branch: Branch, register_core_models_schema: None, flow_runs_data
):
    result = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY_TASK_WITH_LOGS,
        variables={},
    )
    assert result.errors is None
    assert result.data

    assert len(result.data["InfrahubTask"]["edges"]) == 2
    assert result.data["InfrahubTask"]["count"] == 2


async def test_task_query_filter_branch(
    db: InfrahubDatabase, default_branch: Branch, register_core_models_schema: None, flow_runs_data
):
    QUERY = """
    query TaskQuery(
        $branch_name: String!
    ) {
        InfrahubTask(branch: $branch_name) {
            count
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    result = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY,
        variables={"branch_name": "branch1"},
    )
    assert result.errors is None
    assert result.data

    assert len(result.data["InfrahubTask"]["edges"]) == 1
    assert result.data["InfrahubTask"]["count"] == 1


async def test_task_query_filter_node(
    db: InfrahubDatabase,
    default_branch: Branch,
    register_core_models_schema: None,
    tag_blue,
    account_bob,
    flow_runs_data,
):
    QUERY = """
    query TaskQuery(
        $related_nodes: [String]
    ) {
        InfrahubTask(related_node__ids: $related_nodes) {
            count
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    result = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY,
        variables={"related_nodes": [tag_blue.get_id()]},
    )
    assert result.errors is None
    assert result.data

    assert len(result.data["InfrahubTask"]["edges"]) == 1
    assert result.data["InfrahubTask"]["count"] == 1

    result = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY,
        variables={"related_nodes": [account_bob.get_id()]},
    )
    assert result.errors is None
    assert result.data

    assert len(result.data["InfrahubTask"]["edges"]) == 0
    assert result.data["InfrahubTask"]["count"] == 0


async def test_task_query_both(
    db: InfrahubDatabase,
    default_branch: Branch,
    register_core_models_schema: None,
    tag_blue,
    account_bob,
    flow_runs_data,
):
    result = await run_query(
        db=db,
        branch=default_branch,
        query=CREATE_TASK,
        variables={
            "conclusion": "UNKNOWN",
            "title": "Blue Task 1",
            "related_node": tag_blue.get_id(),
            "created_by": account_bob.get_id(),
            "logs": {"message": "Starting task", "severity": "INFO"},
        },
    )
    assert result.errors is None
    assert result.data

    all_logs = await run_query(
        db=db,
        branch=default_branch,
        query=QUERY_TASK_WITH_LOGS,
        variables={},
    )
    assert all_logs.errors is None
    assert all_logs.data

    assert len(all_logs.data["InfrahubTask"]["edges"]) == 3
    assert all_logs.data["InfrahubTask"]["count"] == 3
