from infrahub_sdk import InfrahubClient
from prefect import flow, task
from prefect.logging import get_run_logger

from infrahub import lock
from infrahub.core.constants import InfrahubKind, RepositoryInternalStatus
from infrahub.core.protocols import CoreRepository
from infrahub.core.registry import registry
from infrahub.exceptions import RepositoryError
from infrahub.services import services

from ..tasks.artifact import define_artifact
from ..workflows.catalogue import REQUEST_ARTIFACT_DEFINITION_GENERATE, REQUEST_ARTIFACT_GENERATE
from ..workflows.utils import add_branch_tag, add_related_node_tag
from .models import (
    GitRepositoryMerge,
    GitRepositoryPullReadOnly,
    RequestArtifactDefinitionGenerate,
    RequestArtifactGenerate,
)
from .repository import InfrahubReadOnlyRepository, InfrahubRepository, get_initialized_repo


@flow(name="git_repositories_create_branch", flow_run_name="Create branch {branch} on all eligible repositories")
async def create_branch(branch: str, branch_id: str) -> None:
    """Request to the creation of git branches in available repositories."""
    service = services.service
    await add_branch_tag(branch_name=branch)

    repositories: list[CoreRepository] = await service.client.filters(kind=CoreRepository)

    batch = await service.client.create_batch()

    for repository in repositories:
        batch.add(
            task=git_branch_create,
            client=service.client.client,
            branch=branch,
            branch_id=branch_id,
            repository_name=repository.name.value,
            repository_id=repository.id,
        )

    async for _, _ in batch.execute():
        pass


@flow(name="git_repositories_sync", flow_run_name="Sync all repositories")
async def sync_remote_repositories() -> None:
    service = services.service

    branches = await service.client.branch.all()
    repositories = await service.client.get_list_repositories(branches=branches, kind=InfrahubKind.REPOSITORY)

    for repo_name, repository_data in repositories.items():
        async with service.git_report(
            title="Syncing repository", related_node=repository_data.repository.id, create_with_context=False
        ) as git_report:
            active_internal_status = RepositoryInternalStatus.ACTIVE.value
            default_internal_status = repository_data.branch_info[registry.default_branch].internal_status
            staging_branch = None
            if default_internal_status != RepositoryInternalStatus.ACTIVE.value:
                active_internal_status = RepositoryInternalStatus.STAGING.value
                staging_branch = repository_data.get_staging_branch()

            infrahub_branch = staging_branch or registry.default_branch

            async with lock.registry.get(name=repo_name, namespace="repository"):
                init_failed = False
                try:
                    repo = await InfrahubRepository.init(
                        service=service,
                        id=repository_data.repository.id,
                        name=repository_data.repository.name.value,
                        location=repository_data.repository.location.value,
                        client=service.client,
                        task_report=git_report,
                        internal_status=active_internal_status,
                        default_branch_name=repository_data.repository.default_branch.value,
                    )
                except RepositoryError as exc:
                    service.log.error(str(exc))
                    init_failed = True

                if init_failed:
                    try:
                        repo = await InfrahubRepository.new(
                            service=service,
                            id=repository_data.repository.id,
                            name=repository_data.repository.name.value,
                            location=repository_data.repository.location.value,
                            client=service.client,
                            task_report=git_report,
                            internal_status=active_internal_status,
                            default_branch_name=repository_data.repository.default_branch.value,
                        )
                        await repo.import_objects_from_files(
                            git_branch_name=registry.default_branch, infrahub_branch_name=infrahub_branch
                        )
                    except RepositoryError as exc:
                        await git_report.error(str(exc))
                        continue

                error: RepositoryError | None = None

                try:
                    await repo.sync(staging_branch=staging_branch)
                except RepositoryError as exc:
                    error = exc

                await git_report.set_status(
                    previous_status=repository_data.repository.operational_status.value, error=error
                )


@task(task_run_name="Create branch on repository {repository_name}")
async def git_branch_create(
    client: InfrahubClient, branch: str, branch_id: str, repository_id: str, repository_name: str
) -> None:
    await add_branch_tag(branch_name=branch)
    await add_related_node_tag(node_id=repository_id)

    repo = await InfrahubRepository.init(id=repository_id, name=repository_name, client=client)
    async with lock.registry.get(name=repository_name, namespace="repository"):
        await repo.create_branch_in_git(branch_name=branch, branch_id=branch_id)


@flow(
    name="artifact-definition-generate",
    description="Generate all artifact definitions on a given branch",
    flow_run_name="Generate all artifact definitions on branch {branch}",
)
async def generate_artifact_definition(branch: str) -> None:
    await add_branch_tag(branch_name=branch)

    service = services.service
    artifact_definitions = await service.client.all(kind=InfrahubKind.ARTIFACTDEFINITION, branch=branch, include=["id"])

    for artifact_definition in artifact_definitions:
        model = RequestArtifactDefinitionGenerate(branch=branch, artifact_definition=artifact_definition.id)
        await service.workflow.submit_workflow(
            workflow=REQUEST_ARTIFACT_DEFINITION_GENERATE, parameters={"model": model}
        )


@flow(
    name="artifact-generate",
    description="Generate a single artifact",
    flow_run_name="Generate Artifact: {model.artifact_name} for {model.target_name}",
)
async def generate_artifact(model: RequestArtifactGenerate) -> None:
    await add_branch_tag(branch_name=model.branch_name)
    # NOTE Not sure if we should use the target_id, the artifact or the artifact definition as the related node
    await add_related_node_tag(node_id=model.target_id)

    service = services.service

    log = get_run_logger()

    repo = await get_initialized_repo(
        repository_id=model.repository_id,
        name=model.repository_name,
        service=service,
        repository_kind=model.repository_kind,
    )

    artifact = await define_artifact(message=model, service=service)

    try:
        result = await repo.render_artifact(artifact=artifact, message=model)
        if result.changed:
            log.info("Artifact already up to date")
        else:
            log.info(
                f"New version of the artifact available in the store with the ID {result.storage_id}",
                extra={"checksum": result.checksum},
            )
    except Exception:  # pylint: disable=broad-except
        artifact.status.value = "Error"
        await artifact.save()
        raise


@flow(
    name="request_artifact_definitions_generate",
    description="Trigger rendering of all Artifacts for a given Artifact Definition",
    flow_run_name="Trigger rendering of Artifacts for {model.artifact_definition}",
)
async def generate_request_artifact_definition(model: RequestArtifactDefinitionGenerate) -> None:
    await add_branch_tag(branch_name=model.branch)
    await add_related_node_tag(node_id=model.artifact_definition)

    service = services.service
    artifact_definition = await service.client.get(
        kind=InfrahubKind.ARTIFACTDEFINITION, id=model.artifact_definition, branch=model.branch
    )

    await artifact_definition.targets.fetch()
    group = artifact_definition.targets.peer
    await group.members.fetch()

    existing_artifacts = await service.client.filters(
        kind=InfrahubKind.ARTIFACT,
        definition__ids=[model.artifact_definition],
        include=["object"],
        branch=model.branch,
    )
    artifacts_by_member = {}
    for artifact in existing_artifacts:
        artifacts_by_member[artifact.object.peer.id] = artifact.id

    await artifact_definition.transformation.fetch()
    transformation_repository = artifact_definition.transformation.peer.repository

    await transformation_repository.fetch()

    transform = artifact_definition.transformation.peer
    await transform.query.fetch()
    query = transform.query.peer
    repository = transformation_repository.peer
    branch = await service.client.branch.get(branch_name=model.branch)
    if branch.sync_with_git:
        repository = await service.client.get(
            kind=InfrahubKind.GENERICREPOSITORY, id=repository.id, branch=model.branch, fragment=True
        )
    transform_location = ""

    if transform.typename == InfrahubKind.TRANSFORMJINJA2:
        transform_location = transform.template_path.value
    elif transform.typename == InfrahubKind.TRANSFORMPYTHON:
        transform_location = f"{transform.file_path.value}::{transform.class_name.value}"

    for relationship in group.members.peers:
        member = relationship.peer
        artifact_id = artifacts_by_member.get(member.id)
        if model.limit and artifact_id not in model.limit:
            continue

        request_artifact_generate_model = RequestArtifactGenerate(
            artifact_name=artifact_definition.name.value,
            artifact_id=artifact_id,
            artifact_definition=model.artifact_definition,
            commit=repository.commit.value,
            content_type=artifact_definition.content_type.value,
            transform_type=transform.typename,
            transform_location=transform_location,
            repository_id=repository.id,
            repository_name=repository.name.value,
            repository_kind=repository.get_kind(),
            branch_name=model.branch,
            query=query.name.value,
            variables=member.extract(params=artifact_definition.parameters.value),
            target_id=member.id,
            target_name=member.display_label,
            timeout=transform.timeout.value,
        )

        await service.workflow.submit_workflow(
            workflow=REQUEST_ARTIFACT_GENERATE, parameters={"model": request_artifact_generate_model}
        )


@flow(
    name="git-repository-pull-read-only",
    flow_run_name="Pulling read only repository",
)
async def pull_read_only(model: GitRepositoryPullReadOnly) -> None:
    await add_branch_tag(branch_name=model.infrahub_branch_name)
    await add_related_node_tag(node_id=model.repository_id)

    log = get_run_logger()

    service = services.service
    if not model.ref and not model.commit:
        log.warning("No commit or ref in GitRepositoryPullReadOnly message")
        return

    async with lock.registry.get(name=model.repository_name, namespace="repository"):
        init_failed = False
        try:
            repo = await InfrahubReadOnlyRepository.init(
                id=model.repository_id,
                name=model.repository_name,
                location=model.location,
                client=service.client,
                ref=model.ref,
                infrahub_branch_name=model.infrahub_branch_name,
                # task_report=git_report,
            )
        except RepositoryError:
            init_failed = True

        if init_failed:
            repo = await InfrahubReadOnlyRepository.new(
                id=model.repository_id,
                name=model.repository_name,
                location=model.location,
                client=service.client,
                ref=model.ref,
                infrahub_branch_name=model.infrahub_branch_name,
                # task_report=git_report,
            )

        await repo.import_objects_from_files(infrahub_branch_name=model.infrahub_branch_name, commit=model.commit)
        await repo.sync_from_remote(commit=model.commit)


@flow(
    name="git-repository-merge",
    description="merge a branch on a given Git Pepository",
    flow_run_name="Merge branch {model.source_branch} into {model.destination_branch} [{model.repository_name}]",
)
async def merge_git_repository(model: GitRepositoryMerge) -> None:
    await add_branch_tag(branch_name=model.destination_branch)
    await add_related_node_tag(node_id=model.repository_id)
    service = services.service

    log = get_run_logger()

    repo = await InfrahubRepository.init(
        id=model.repository_id,
        name=model.repository_name,
        client=service.client,
        default_branch_name=model.default_branch,
    )

    if model.internal_status == RepositoryInternalStatus.STAGING.value:
        repo_source = await service.client.get(
            kind=InfrahubKind.GENERICREPOSITORY, id=model.repository_id, branch=model.source_branch
        )
        repo_main = await service.client.get(kind=InfrahubKind.GENERICREPOSITORY, id=model.repository_id)
        repo_main.internal_status.value = RepositoryInternalStatus.ACTIVE.value
        repo_main.sync_status.value = repo_source.sync_status.value

        commit = repo.get_commit_value(branch_name=repo.default_branch, remote=False)
        repo_main.commit.value = commit
        await repo_main.save()
        log.info(f"Internal Status updated to {RepositoryInternalStatus.ACTIVE.value}")
        log.debug(f"Commit updated to {commit}")

    else:
        async with lock.registry.get(name=model.repository_name, namespace="repository"):
            log.debug(f"Lock acquired for repository:{model.repository_name}")
            await repo.merge(source_branch=model.source_branch, dest_branch=model.destination_branch)
