from prefect import flow

from infrahub.core import registry
from infrahub.core.diff.coordinator import DiffCoordinator
from infrahub.core.diff.models import RequestDiffUpdate
from infrahub.dependencies.registry import get_component_registry
from infrahub.log import get_logger
from infrahub.services import services

log = get_logger()


@flow(name="diff-update")
async def update_diff(model: RequestDiffUpdate) -> None:
    service = services.service
    component_registry = get_component_registry()
    base_branch = await registry.get_branch(db=service.database, branch=registry.default_branch)
    diff_branch = await registry.get_branch(db=service.database, branch=model.branch_name)

    diff_coordinator = await component_registry.get_component(DiffCoordinator, db=service.database, branch=diff_branch)

    await diff_coordinator.run_update(
        base_branch=base_branch,
        diff_branch=diff_branch,
        from_time=model.from_time,
        to_time=model.to_time,
        name=model.name,
    )
