from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, patch

from infrahub_sdk import Config, InfrahubClient
from infrahub_sdk.uuidt import UUIDT
from typing_extensions import Self

from infrahub.core.constants import InfrahubKind, RepositoryInternalStatus
from infrahub.exceptions import RepositoryError
from infrahub.git import InfrahubRepository
from infrahub.git.models import (
    GitRepositoryAdd,
    GitRepositoryAddReadOnly,
    GitRepositoryMerge,
    GitRepositoryPullReadOnly,
)
from infrahub.git.repository import InfrahubReadOnlyRepository
from infrahub.git.tasks import add_git_repository, add_git_repository_read_only, pull_read_only
from infrahub.lock import InfrahubLockRegistry
from infrahub.message_bus import Meta, messages
from infrahub.message_bus.messages import RefreshGitFetch
from infrahub.services import InfrahubServices, services
from infrahub.services.adapters.workflow.local import WorkflowLocalExecution
from infrahub.workflows.catalogue import GIT_REPOSITORIES_MERGE
from tests.adapters.message_bus import BusSimulator
from tests.helpers.test_client import dummy_async_request

# pylint: disable=redefined-outer-name

if TYPE_CHECKING:
    from types import TracebackType

    from infrahub_sdk.branch import BranchData

    from tests.conftest import TestHelper


class AsyncContextManagerMock:
    async def __aenter__(self, *args: Any, **kwargs: Any) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Self:
        return self


class TestAddRepository:
    def setup_method(self):
        self.default_branch_name = "default-branch"
        self.client = AsyncMock(spec=InfrahubClient)
        self.git_report = AsyncContextManagerMock()
        self.original_services = services.service
        self.recorder = BusSimulator()
        services.service = InfrahubServices(client=self.client, message_bus=self.recorder)
        services.service.git_report = self.git_report

        self.mock_repo = AsyncMock(spec=InfrahubRepository)
        self.mock_repo.default_branch = self.default_branch_name
        self.mock_repo.infrahub_branch_name = self.default_branch_name
        self.mock_repo.internal_status = "active"

    def teardown_method(self):
        patch.stopall()
        services.service = self.original_services

    async def test_git_rpc_create_successful(self, git_upstream_repo_01: dict[str, str]):
        repo_id = str(UUIDT())
        model = GitRepositoryAdd(
            repository_id=repo_id,
            repository_name=git_upstream_repo_01["name"],
            location=git_upstream_repo_01["path"],
            default_branch_name=self.default_branch_name,
            infrahub_branch_name=self.default_branch_name,
            internal_status="active",
        )

        with (
            patch("infrahub.git.tasks.lock") as mock_infra_lock,
            patch("infrahub.git.tasks.InfrahubRepository", spec=InfrahubRepository) as mock_repo_class,
        ):
            mock_infra_lock.registry = AsyncMock(spec=InfrahubLockRegistry)
            mock_repo_class.new.return_value = self.mock_repo

            await add_git_repository(model=model)

            mock_infra_lock.registry.get.assert_called_once_with(
                name=git_upstream_repo_01["name"], namespace="repository"
            )

            mock_repo_class.new.assert_awaited_once_with(
                id=repo_id,
                name=git_upstream_repo_01["name"],
                location=git_upstream_repo_01["path"],
                client=self.client,
                task_report=self.git_report,
                infrahub_branch_name=self.default_branch_name,
                internal_status="active",
                default_branch_name=self.default_branch_name,
            )
            self.mock_repo.import_objects_from_files.assert_awaited_once_with(
                infrahub_branch_name=self.default_branch_name, git_branch_name=self.default_branch_name
            )
            self.mock_repo.sync.assert_awaited_once_with()

        assert len(self.recorder.messages) > 0
        assert isinstance(self.recorder.messages[0], RefreshGitFetch)


async def test_git_rpc_merge(git_repo_01: InfrahubRepository, branch01: BranchData, helper: TestHelper):
    repo = git_repo_01

    await repo.create_branch_in_git(branch_name=branch01.name, branch_id=branch01.id)

    commit_main_before = repo.get_commit_value(branch_name="main")

    model = GitRepositoryMerge(
        repository_id=str(repo.id),
        repository_name=repo.name,
        source_branch="branch01",
        destination_branch="main",
        internal_status=RepositoryInternalStatus.ACTIVE.value,
        default_branch="main",
    )

    client_config = Config(requester=dummy_async_request)
    bus_simulator = helper.get_message_bus_simulator()
    service = InfrahubServices(
        client=InfrahubClient(config=client_config), message_bus=bus_simulator, workflow=WorkflowLocalExecution()
    )
    bus_simulator.service = service

    original_services = services.service
    services.service = service
    await service.workflow.submit_workflow(workflow=GIT_REPOSITORIES_MERGE, parameters={"model": model})

    # Restore original services to not impact other tests. This global variable might/should be redesigned at some point.
    service.service = original_services

    commit_main_after = repo.get_commit_value(branch_name="main")

    assert commit_main_before != commit_main_after


async def test_git_rpc_diff(
    git_repo_01: InfrahubRepository, branch01: BranchData, branch02: BranchData, helper: TestHelper
):
    repo = git_repo_01

    await repo.create_branch_in_git(branch_name=branch01.name, branch_id=branch01.id)
    await repo.create_branch_in_git(branch_name=branch02.name, branch_id=branch02.id)

    commit_main = repo.get_commit_value(branch_name="main", remote=False)
    commit_branch01 = repo.get_commit_value(branch_name=branch01.name, remote=False)
    commit_branch02 = repo.get_commit_value(branch_name=branch02.name, remote=False)

    # Diff Between Branch01 and Branch02
    correlation_id = str(UUIDT())
    message = messages.GitDiffNamesOnly(
        repository_id=str(repo.id),
        repository_name=repo.name,
        repository_kind=InfrahubKind.REPOSITORY,
        first_commit=commit_branch01,
        second_commit=commit_branch02,
        meta=Meta(reply_to="ci-testing", correlation_id=correlation_id),
    )

    bus_simulator = helper.get_message_bus_simulator()
    service = InfrahubServices(client=InfrahubClient(), message_bus=bus_simulator)
    bus_simulator.service = service
    result = await service.message_bus.rpc(message=message, response_class=messages.GitDiffNamesOnlyResponse)
    assert result.data.files_changed == ["README.md", "test_files/sports.yml"]

    message = messages.GitDiffNamesOnly(
        repository_id=str(repo.id),
        repository_name=repo.name,
        repository_kind=InfrahubKind.REPOSITORY,
        first_commit=commit_branch01,
        second_commit=commit_main,
        meta=Meta(reply_to="ci-testing", correlation_id=correlation_id),
    )
    result = await service.message_bus.rpc(message=message, response_class=messages.GitDiffNamesOnlyResponse)
    assert result.data.files_changed == ["test_files/sports.yml"]


class TestAddReadOnly:
    def setup_method(self):
        self.client = AsyncMock(spec=InfrahubClient)
        self.git_report = AsyncContextManagerMock()
        self.original_services = services.service
        self.recorder = BusSimulator()
        services.service = InfrahubServices(client=self.client, message_bus=self.recorder)
        services.service.git_report = self.git_report

        lock_patcher = patch("infrahub.git.tasks.lock")
        self.mock_infra_lock = lock_patcher.start()
        self.mock_infra_lock.registry = AsyncMock(spec=InfrahubLockRegistry)
        repo_class_patcher = patch("infrahub.git.tasks.InfrahubReadOnlyRepository", spec=InfrahubReadOnlyRepository)
        self.mock_repo_class = repo_class_patcher.start()
        self.mock_repo = AsyncMock(spec=InfrahubReadOnlyRepository)
        self.mock_repo_class.new.return_value = self.mock_repo

    def teardown_method(self):
        patch.stopall()
        services.service = self.original_services

    async def test_git_rpc_add_read_only_success(self, git_upstream_repo_01: dict[str, str]):
        repo_id = str(UUIDT())
        model = GitRepositoryAddReadOnly(
            repository_id=repo_id,
            repository_name=git_upstream_repo_01["name"],
            location=git_upstream_repo_01["path"],
            ref="branch01",
            infrahub_branch_name="read-only-branch",
            internal_status="active",
        )

        await add_git_repository_read_only(model=model)

        self.mock_infra_lock.registry.get(name=git_upstream_repo_01["name"], namespace="repository")
        self.mock_repo_class.new.assert_awaited_once_with(
            id=repo_id,
            name=git_upstream_repo_01["name"],
            location=git_upstream_repo_01["path"],
            client=self.client,
            ref="branch01",
            infrahub_branch_name="read-only-branch",
            task_report=self.git_report,
        )
        self.mock_repo.import_objects_from_files.assert_awaited_once_with(infrahub_branch_name="read-only-branch")
        self.mock_repo.sync_from_remote.assert_awaited_once_with()

        assert len(self.recorder.messages) > 0
        assert isinstance(self.recorder.messages[0], RefreshGitFetch)


class TestPullReadOnly:
    def setup_method(self):
        self.client = AsyncMock(spec=InfrahubClient)
        self.git_report = AsyncContextManagerMock()
        self.original_services = services.service
        self.recorder = BusSimulator()
        services.service = InfrahubServices(
            client=self.client, workflow=WorkflowLocalExecution(), message_bus=self.recorder
        )
        services.service.git_report = self.git_report

        self.commit = str(UUIDT())
        self.infrahub_branch_name = "read-only-branch"
        self.repo_id = str(UUIDT())
        self.location = "/some/directory/over/here"
        self.repo_name = "dont-update-this-dude"
        self.ref = "stable-branch"

        self.model = GitRepositoryPullReadOnly(
            location=self.location,
            repository_id=self.repo_id,
            repository_name=self.repo_name,
            ref=self.ref,
            commit=self.commit,
            infrahub_branch_name=self.infrahub_branch_name,
        )

        lock_patcher = patch("infrahub.git.tasks.lock")
        self.mock_infra_lock = lock_patcher.start()
        self.mock_infra_lock.registry = AsyncMock(spec=InfrahubLockRegistry)  # TODO fix mock?
        repo_class_patcher = patch("infrahub.git.tasks.InfrahubReadOnlyRepository", spec=InfrahubReadOnlyRepository)
        self.mock_repo_class = repo_class_patcher.start()
        self.mock_repo = AsyncMock(spec=InfrahubReadOnlyRepository)
        self.mock_repo_class.new.return_value = self.mock_repo
        self.mock_repo_class.init.return_value = self.mock_repo

    def teardown_method(self):
        patch.stopall()
        services.service = self.original_services

    async def test_improper_message(self):
        self.model.ref = None
        self.model.commit = None

        await pull_read_only(model=self.model)

        self.mock_repo_class.new.assert_not_awaited()
        self.mock_repo_class.init.assert_not_awaited()

    async def test_existing_repository(self):
        await pull_read_only(model=self.model)

        self.mock_infra_lock.registry.get(name=self.repo_name, namespace="repository")
        self.mock_repo_class.init.assert_awaited_once_with(
            id=self.repo_id,
            name=self.repo_name,
            location=self.location,
            client=self.client,
            ref=self.ref,
            infrahub_branch_name=self.infrahub_branch_name,
            task_report=self.git_report,
        )
        self.mock_repo.import_objects_from_files.assert_awaited_once_with(
            infrahub_branch_name=self.infrahub_branch_name, commit=self.commit
        )
        self.mock_repo.sync_from_remote.assert_awaited_once_with(commit=self.commit)

        assert len(self.recorder.messages) > 0
        assert isinstance(self.recorder.messages[0], RefreshGitFetch)

    async def test_new_repository(self):
        self.mock_repo_class.init.side_effect = RepositoryError(self.repo_name, "it is broken")

        await pull_read_only(model=self.model)

        self.mock_infra_lock.registry.get(name=self.repo_name, namespace="repository")
        self.mock_repo_class.init.assert_awaited_once_with(
            id=self.repo_id,
            name=self.repo_name,
            location=self.location,
            client=self.client,
            ref=self.ref,
            infrahub_branch_name=self.infrahub_branch_name,
            task_report=self.git_report,
        )
        self.mock_repo_class.new.assert_awaited_once_with(
            id=self.repo_id,
            name=self.repo_name,
            location=self.location,
            client=self.client,
            ref=self.ref,
            infrahub_branch_name=self.infrahub_branch_name,
            task_report=self.git_report,
        )
        self.mock_repo.import_objects_from_files.assert_awaited_once_with(
            infrahub_branch_name=self.infrahub_branch_name, commit=self.commit
        )
        self.mock_repo.sync_from_remote.assert_awaited_once_with(commit=self.commit)

        assert len(self.recorder.messages) > 0
        assert isinstance(self.recorder.messages[0], RefreshGitFetch)
