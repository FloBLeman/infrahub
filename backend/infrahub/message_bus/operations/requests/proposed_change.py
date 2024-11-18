from __future__ import annotations

import asyncio
import os
import sys
from enum import IntFlag
from pathlib import Path
from typing import TYPE_CHECKING, Union

import pytest
from prefect import flow
from pydantic import BaseModel

from infrahub import config, lock
from infrahub.core.constants import CheckType, InfrahubKind, RepositoryInternalStatus
from infrahub.core.diff.coordinator import DiffCoordinator
from infrahub.core.registry import registry
from infrahub.dependencies.registry import get_component_registry
from infrahub.git.repository import InfrahubRepository, get_initialized_repo
from infrahub.log import get_logger
from infrahub.message_bus import InfrahubMessage, messages
from infrahub.message_bus.types import (
    ProposedChangeArtifactDefinition,
    ProposedChangeBranchDiff,
    ProposedChangeRepository,
    ProposedChangeSubscriber,
)
from infrahub.proposed_change.models import (
    RequestProposedChangeDataIntegrity,
    RequestProposedChangeRunGenerators,
    RequestProposedChangeSchemaIntegrity,
)
from infrahub.pytest_plugin import InfrahubBackendPlugin
from infrahub.services import InfrahubServices  # noqa: TCH001
from infrahub.workflows.catalogue import (
    REQUEST_PROPOSED_CHANGE_DATA_INTEGRITY,
    REQUEST_PROPOSED_CHANGE_RUN_GENERATORS,
    REQUEST_PROPOSED_CHANGE_SCHEMA_INTEGRITY,
)

if TYPE_CHECKING:
    from infrahub_sdk.node import InfrahubNode


log = get_logger()


class DefinitionSelect(IntFlag):
    NONE = 0
    MODIFIED_KINDS = 1
    FILE_CHANGES = 2

    @staticmethod
    def add_flag(current: DefinitionSelect, flag: DefinitionSelect, condition: bool) -> DefinitionSelect:
        if condition:
            return current | flag
        return current

    @property
    def log_line(self) -> str:
        change_types = []
        if DefinitionSelect.MODIFIED_KINDS in self:
            change_types.append("data changes within relevant object kinds")

        if DefinitionSelect.FILE_CHANGES in self:
            change_types.append("file modifications in Git repositories")

        if self:
            return f"Requesting generation due to {' and '.join(change_types)}"

        return "Doesn't require changes due to no relevant modified kinds or file changes in Git"


@flow(name="proposed-changed-pipeline")
async def pipeline(message: messages.RequestProposedChangePipeline, service: InfrahubServices) -> None:
    events: list[InfrahubMessage] = []

    repositories = await _get_proposed_change_repositories(message=message, service=service)

    if message.source_branch_sync_with_git and await _validate_repository_merge_conflicts(repositories=repositories):
        for repo in repositories:
            if not repo.read_only and repo.internal_status == RepositoryInternalStatus.ACTIVE.value:
                events.append(
                    messages.RequestRepositoryChecks(
                        proposed_change=message.proposed_change,
                        repository=repo.repository_id,
                        source_branch=repo.source_branch,
                        target_branch=repo.destination_branch,
                    )
                )
        for event in events:
            event.assign_meta(parent=message)
            await service.send(message=event)
        return

    await _gather_repository_repository_diffs(repositories=repositories)

    destination_branch = await registry.get_branch(db=service.database, branch=message.destination_branch)
    source_branch = await registry.get_branch(db=service.database, branch=message.source_branch)
    component_registry = get_component_registry()
    async with service.database.start_transaction() as dbt:
        diff_coordinator = await component_registry.get_component(DiffCoordinator, db=dbt, branch=source_branch)
        await diff_coordinator.update_branch_diff(base_branch=destination_branch, diff_branch=source_branch)
    diff_summary = await service.client.get_diff_summary(branch=message.source_branch)
    branch_diff = ProposedChangeBranchDiff(diff_summary=diff_summary, repositories=repositories)
    await _populate_subscribers(branch_diff=branch_diff, service=service, branch=message.source_branch)

    if message.check_type is CheckType.ARTIFACT:
        events.append(
            messages.RequestProposedChangeRefreshArtifacts(
                proposed_change=message.proposed_change,
                source_branch=message.source_branch,
                source_branch_sync_with_git=message.source_branch_sync_with_git,
                destination_branch=message.destination_branch,
                branch_diff=branch_diff,
            )
        )

    if message.check_type in [CheckType.ALL, CheckType.GENERATOR]:
        model_proposed_change_run_generator = RequestProposedChangeRunGenerators(
            proposed_change=message.proposed_change,
            source_branch=message.source_branch,
            source_branch_sync_with_git=message.source_branch_sync_with_git,
            destination_branch=message.destination_branch,
            branch_diff=branch_diff,
            refresh_artifacts=message.check_type is CheckType.ALL,
            do_repository_checks=message.check_type is CheckType.ALL,
        )
        await service.workflow.submit_workflow(
            workflow=REQUEST_PROPOSED_CHANGE_RUN_GENERATORS, parameters={"model": model_proposed_change_run_generator}
        )

    if message.check_type in [CheckType.ALL, CheckType.DATA] and branch_diff.has_node_changes(
        branch=message.source_branch
    ):
        model_proposed_change_data_integrity = RequestProposedChangeDataIntegrity(
            proposed_change=message.proposed_change,
            source_branch=message.source_branch,
            source_branch_sync_with_git=message.source_branch_sync_with_git,
            destination_branch=message.destination_branch,
            branch_diff=branch_diff,
        )
        await service.workflow.submit_workflow(
            workflow=REQUEST_PROPOSED_CHANGE_DATA_INTEGRITY, parameters={"model": model_proposed_change_data_integrity}
        )

    if message.check_type in [CheckType.REPOSITORY, CheckType.USER]:
        events.append(
            messages.RequestProposedChangeRepositoryChecks(
                proposed_change=message.proposed_change,
                source_branch=message.source_branch,
                source_branch_sync_with_git=message.source_branch_sync_with_git,
                destination_branch=message.destination_branch,
                branch_diff=branch_diff,
            )
        )

    if message.check_type in [CheckType.ALL, CheckType.SCHEMA] and branch_diff.has_data_changes(
        branch=message.source_branch
    ):
        await service.workflow.submit_workflow(
            workflow=REQUEST_PROPOSED_CHANGE_SCHEMA_INTEGRITY,
            parameters={
                "model": RequestProposedChangeSchemaIntegrity(
                    proposed_change=message.proposed_change,
                    source_branch=message.source_branch,
                    source_branch_sync_with_git=message.source_branch_sync_with_git,
                    destination_branch=message.destination_branch,
                    branch_diff=branch_diff,
                )
            },
        )

    if message.check_type in [CheckType.ALL, CheckType.TEST]:
        events.append(
            messages.RequestProposedChangeRunTests(
                proposed_change=message.proposed_change,
                source_branch=message.source_branch,
                source_branch_sync_with_git=message.source_branch_sync_with_git,
                destination_branch=message.destination_branch,
                branch_diff=branch_diff,
            )
        )

    for event in events:
        event.assign_meta(parent=message)
        await service.send(message=event)


@flow(name="proposed-changed-repository-check")
async def repository_checks(message: messages.RequestProposedChangeRepositoryChecks, service: InfrahubServices) -> None:
    log.info(f"Got a request to process checks defined in proposed_change: {message.proposed_change}")
    events: list[InfrahubMessage] = []
    for repository in message.branch_diff.repositories:
        if (
            message.source_branch_sync_with_git
            and not repository.read_only
            and repository.internal_status == RepositoryInternalStatus.ACTIVE.value
        ):
            events.append(
                messages.RequestRepositoryChecks(
                    proposed_change=message.proposed_change,
                    repository=repository.repository_id,
                    source_branch=message.source_branch,
                    target_branch=message.destination_branch,
                )
            )

        events.append(
            messages.RequestRepositoryUserChecks(
                proposed_change=message.proposed_change,
                repository=repository.repository_id,
                source_branch=message.source_branch,
                source_branch_sync_with_git=message.source_branch_sync_with_git,
                target_branch=message.destination_branch,
                branch_diff=message.branch_diff,
            )
        )
    for event in events:
        event.assign_meta(parent=message)
        await service.send(message=event)


@flow(
    name="proposed-changed-refresh-artifact",
    flow_run_name="Refreshing artifacts for change_proposal={message.proposed_change}",
)
async def refresh_artifacts(message: messages.RequestProposedChangeRefreshArtifacts, service: InfrahubServices) -> None:
    definition_information = await service.client.execute_graphql(
        query=GATHER_ARTIFACT_DEFINITIONS,
        branch_name=message.source_branch,
    )
    artifact_definitions = _parse_artifact_definitions(
        definitions=definition_information[InfrahubKind.ARTIFACTDEFINITION]["edges"]
    )

    for artifact_definition in artifact_definitions:
        # Request artifact definition checks if the source branch that is managed in combination
        # to the Git repository containing modifications which could indicate changes to the transforms
        # in code
        # Alternatively if the queries used touches models that have been modified in the path
        # impacted artifact definitions will be included for consideration

        select = DefinitionSelect.NONE
        select = select.add_flag(
            current=select,
            flag=DefinitionSelect.FILE_CHANGES,
            condition=message.source_branch_sync_with_git and message.branch_diff.has_file_modifications,
        )

        for changed_model in message.branch_diff.modified_kinds(branch=message.source_branch):
            condition = False
            if (changed_model in artifact_definition.query_models) or (
                changed_model.startswith("Profile")
                and changed_model.replace("Profile", "", 1) in artifact_definition.query_models
            ):
                condition = True

            select = select.add_flag(
                current=select,
                flag=DefinitionSelect.MODIFIED_KINDS,
                condition=condition,
            )

        if select:
            msg = messages.RequestArtifactDefinitionCheck(
                artifact_definition=artifact_definition,
                branch_diff=message.branch_diff,
                proposed_change=message.proposed_change,
                source_branch=message.source_branch,
                source_branch_sync_with_git=message.source_branch_sync_with_git,
                destination_branch=message.destination_branch,
            )

            msg.assign_meta(parent=message)
            await service.send(message=msg)


GATHER_ARTIFACT_DEFINITIONS = """
query GatherArtifactDefinitions {
  CoreArtifactDefinition {
    edges {
      node {
        id
        name {
          value
        }
        content_type {
            value
        }
        transformation {
          node {
            __typename
            timeout {
                value
            }
            query {
              node {
                models {
                  value
                }
                name {
                  value
                }
              }
            }
            ... on CoreTransformJinja2 {
              template_path {
                value
              }
            }
            ... on CoreTransformPython {
              class_name {
                value
              }
              file_path {
                value
              }
            }
            repository {
              node {
                id
              }
            }
          }
        }
      }
    }
  }
}
"""

GATHER_GRAPHQL_QUERY_SUBSCRIBERS = """
query GatherGraphQLQuerySubscribers($members: [ID!]) {
  CoreGraphQLQueryGroup(members__ids: $members) {
    edges {
      node {
        subscribers {
          edges {
            node {
              id
              __typename
            }
          }
        }
      }
    }
  }
}
"""


@flow(
    name="proposed-changed-run-tests",
    flow_run_name="Running_repository_tests on proposed change {message.proposed_change}",
)
async def run_tests(message: messages.RequestProposedChangeRunTests, service: InfrahubServices) -> None:
    proposed_change = await service.client.get(kind=InfrahubKind.PROPOSEDCHANGE, id=message.proposed_change)

    def _execute(
        directory: Path, repository: ProposedChangeRepository, proposed_change: InfrahubNode
    ) -> Union[int, pytest.ExitCode]:
        config_file = str(directory / ".infrahub.yml")
        test_directory = directory / "tests"

        if not test_directory.is_dir():
            log.debug(
                event="repository_tests_ignored",
                proposed_change=proposed_change,
                repository=repository.repository_name,
                message="tests directory not found",
            )
            return 1

        # Redirect stdout/stderr to avoid showing pytest lines in the git agent
        old_out = sys.stdout
        old_err = sys.stderr

        with Path(os.devnull).open(mode="w", encoding="utf-8") as devnull:
            sys.stdout = devnull
            sys.stderr = devnull

            exit_code = pytest.main(
                [
                    str(test_directory),
                    f"--infrahub-repo-config={config_file}",
                    f"--infrahub-address={config.SETTINGS.main.internal_address}",
                    "-qqqq",
                    "-s",
                ],
                plugins=[InfrahubBackendPlugin(service.client.config, repository.repository_id, proposed_change.id)],
            )

        # Restore stdout/stderr back to their orignal states
        sys.stdout = old_out
        sys.stderr = old_err

        return exit_code

    for repository in message.branch_diff.repositories:
        if message.source_branch_sync_with_git:
            repo = await get_initialized_repo(
                repository_id=repository.repository_id,
                name=repository.repository_name,
                service=service,
                repository_kind=repository.kind,
            )
            commit = repo.get_commit_value(proposed_change.source_branch.value)
            worktree_directory = Path(repo.get_commit_worktree(commit=commit).directory)

            return_code = await asyncio.to_thread(_execute, worktree_directory, repository, proposed_change)
            log.info(
                event="repository_tests_completed",
                proposed_change=message.proposed_change,
                repository=repository.repository_name,
                return_code=return_code,
            )


DESTINATION_ALLREPOSITORIES = """
query DestinationBranchRepositories {
  CoreGenericRepository {
    edges {
      node {
        __typename
        id
        name {
          value
        }
        internal_status {
          value
        }
        ... on CoreRepository {
          commit {
            value
          }
        }
        ... on CoreReadOnlyRepository {
          commit {
            value
          }
        }
      }
    }
  }
}
"""

SOURCE_REPOSITORIES = """
query MyQuery {
  CoreRepository {
    edges {
      node {
        __typename
        id
        name {
          value
        }
        internal_status {
          value
        }
        commit {
          value
        }
      }
    }
  }
}
"""
SOURCE_READONLY_REPOSITORIES = """
query MyQuery {
  CoreReadOnlyRepository {
    edges {
      node {
        __typename
        id
        name {
          value
        }
        internal_status {
          value
        }
        commit {
          value
        }
      }
    }
  }
}
"""


class Repository(BaseModel):
    repository_id: str
    repository_name: str
    read_only: bool
    commit: str
    internal_status: str


def _parse_proposed_change_repositories(
    message: messages.RequestProposedChangePipeline, source: list[dict], destination: list[dict]
) -> list[ProposedChangeRepository]:
    """This function assumes that the repos is a list of the edges

    The data should come from the queries:
    * DESTINATION_ALLREPOSITORIES
    * SOURCE_REPOSITORIES
    * SOURCE_READONLY_REPOSITORIES
    """
    destination_repos = _parse_repositories(repositories=destination)
    source_repos = _parse_repositories(repositories=source)
    pc_repos: dict[str, ProposedChangeRepository] = {}
    for repo in destination_repos:
        if repo.repository_id not in pc_repos:
            pc_repos[repo.repository_id] = ProposedChangeRepository(
                repository_id=repo.repository_id,
                repository_name=repo.repository_name,
                read_only=repo.read_only,
                internal_status=repo.internal_status,
                destination_commit=repo.commit,
                source_branch=message.source_branch,
                destination_branch=message.destination_branch,
            )
        else:
            pc_repos[repo.repository_id].destination_commit = repo.commit

    for repo in source_repos:
        if repo.repository_id not in pc_repos:
            pc_repos[repo.repository_id] = ProposedChangeRepository(
                repository_id=repo.repository_id,
                repository_name=repo.repository_name,
                read_only=repo.read_only,
                internal_status=repo.internal_status,
                source_commit=repo.commit,
                source_branch=message.source_branch,
                destination_branch=message.destination_branch,
            )
        else:
            pc_repos[repo.repository_id].source_commit = repo.commit
            pc_repos[repo.repository_id].internal_status = repo.internal_status

    return list(pc_repos.values())


def _parse_repositories(repositories: list[dict]) -> list[Repository]:
    """This function assumes that the repos is a list of the edges

    The data should come from the queries:
    * DESTINATION_ALLREPOSITORIES
    * SOURCE_REPOSITORIES
    * SOURCE_READONLY_REPOSITORIES
    """
    parsed = []
    for repo in repositories:
        parsed.append(
            Repository(
                repository_id=repo["node"]["id"],
                repository_name=repo["node"]["name"]["value"],
                read_only=repo["node"]["__typename"] == InfrahubKind.READONLYREPOSITORY,
                commit=repo["node"]["commit"]["value"] or "",
                internal_status=repo["node"]["internal_status"]["value"],
            )
        )
    return parsed


def _parse_artifact_definitions(definitions: list[dict]) -> list[ProposedChangeArtifactDefinition]:
    """This function assumes that definitions is a list of the edges

    The edge should be of type CoreArtifactDefinition from the query
    * GATHER_ARTIFACT_DEFINITIONS
    """

    parsed = []
    for definition in definitions:
        artifact_definition = ProposedChangeArtifactDefinition(
            definition_id=definition["node"]["id"],
            definition_name=definition["node"]["name"]["value"],
            content_type=definition["node"]["content_type"]["value"],
            timeout=definition["node"]["transformation"]["node"]["timeout"]["value"],
            query_name=definition["node"]["transformation"]["node"]["query"]["node"]["name"]["value"],
            query_models=definition["node"]["transformation"]["node"]["query"]["node"]["models"]["value"] or [],
            repository_id=definition["node"]["transformation"]["node"]["repository"]["node"]["id"],
            transform_kind=definition["node"]["transformation"]["node"]["__typename"],
        )
        if artifact_definition.transform_kind == InfrahubKind.TRANSFORMJINJA2:
            artifact_definition.template_path = definition["node"]["transformation"]["node"]["template_path"]["value"]
        elif artifact_definition.transform_kind == InfrahubKind.TRANSFORMPYTHON:
            artifact_definition.class_name = definition["node"]["transformation"]["node"]["class_name"]["value"]
            artifact_definition.file_path = definition["node"]["transformation"]["node"]["file_path"]["value"]

        parsed.append(artifact_definition)

    return parsed


async def _get_proposed_change_repositories(
    message: messages.RequestProposedChangePipeline, service: InfrahubServices
) -> list[ProposedChangeRepository]:
    destination_all = await service.client.execute_graphql(
        query=DESTINATION_ALLREPOSITORIES, branch_name=message.destination_branch
    )
    source_managed = await service.client.execute_graphql(query=SOURCE_REPOSITORIES, branch_name=message.source_branch)
    source_readonly = await service.client.execute_graphql(
        query=SOURCE_READONLY_REPOSITORIES, branch_name=message.source_branch
    )

    destination_all = destination_all[InfrahubKind.GENERICREPOSITORY]["edges"]
    source_all = (
        source_managed[InfrahubKind.REPOSITORY]["edges"] + source_readonly[InfrahubKind.READONLYREPOSITORY]["edges"]
    )

    return _parse_proposed_change_repositories(message=message, source=source_all, destination=destination_all)


async def _validate_repository_merge_conflicts(repositories: list[ProposedChangeRepository]) -> bool:
    conflicts = False
    for repo in repositories:
        if repo.has_diff and not repo.is_staging:
            git_repo = await InfrahubRepository.init(id=repo.repository_id, name=repo.repository_name)
            async with lock.registry.get(name=repo.repository_name, namespace="repository"):
                repo.conflicts = await git_repo.get_conflicts(
                    source_branch=repo.source_branch, dest_branch=repo.destination_branch
                )
                if repo.conflicts:
                    conflicts = True

    return conflicts


async def _gather_repository_repository_diffs(repositories: list[ProposedChangeRepository]) -> None:
    for repo in repositories:
        if repo.has_diff and repo.source_commit and repo.destination_commit:
            # TODO we need to find a way to return all files in the repo if the repo is new
            git_repo = await InfrahubRepository.init(id=repo.repository_id, name=repo.repository_name)

            files_changed: list[str] = []
            files_added: list[str] = []
            files_removed: list[str] = []

            if repo.destination_branch:
                files_changed, files_added, files_removed = await git_repo.calculate_diff_between_commits(
                    first_commit=repo.source_commit, second_commit=repo.destination_commit
                )
            else:
                files_added = await git_repo.list_all_files(commit=repo.source_commit)

            repo.files_removed = files_removed
            repo.files_added = files_added
            repo.files_changed = files_changed


async def _populate_subscribers(branch_diff: ProposedChangeBranchDiff, service: InfrahubServices, branch: str) -> None:
    result = await service.client.execute_graphql(
        query=GATHER_GRAPHQL_QUERY_SUBSCRIBERS,
        branch_name=branch,
        variables={"members": branch_diff.modified_nodes(branch=branch)},
    )

    for group in result[InfrahubKind.GRAPHQLQUERYGROUP]["edges"]:
        for subscriber in group["node"]["subscribers"]["edges"]:
            branch_diff.subscribers.append(
                ProposedChangeSubscriber(subscriber_id=subscriber["node"]["id"], kind=subscriber["node"]["__typename"])
            )
