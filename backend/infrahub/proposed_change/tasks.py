from __future__ import annotations

from infrahub_sdk.protocols import CoreProposedChange
from prefect import flow, task
from prefect.logging import get_run_logger

from infrahub.core import registry
from infrahub.core.constants import ProposedChangeState
from infrahub.core.diff.coordinator import DiffCoordinator
from infrahub.dependencies.registry import get_component_registry
from infrahub.proposed_change.models import (
    RequestProposedChangeDataIntegrity,  # noqa: TCH001. as symbol is required by prefect flow
)
from infrahub.services import services


@flow(name="proposed-changes-cancel-branch", description="Cancel all Proposed change associated with a branch.")
async def cancel_proposed_changes_branch(branch_name: str) -> None:
    service = services.service
    proposed_changed_opened = await service.client.filters(
        kind=CoreProposedChange,
        include=["id", "source_branch"],
        state__value=ProposedChangeState.OPEN.value,
        source_branch__value=branch_name,
    )
    proposed_changed_closed = await service.client.filters(
        kind=CoreProposedChange,
        include=["id", "source_branch"],
        state__value=ProposedChangeState.CLOSED.value,
        source_branch__value=branch_name,
    )

    for proposed_change in proposed_changed_opened + proposed_changed_closed:
        await cancel_proposed_change(proposed_change=proposed_change)


@task(description="Cancel a propose change")
async def cancel_proposed_change(proposed_change: CoreProposedChange) -> None:
    service = services.service
    log = get_run_logger()

    log.info("Canceling proposed change as the source branch was deleted")
    proposed_change = await service.client.get(kind=CoreProposedChange, id=proposed_change.id)
    proposed_change.state.value = ProposedChangeState.CANCELED.value
    await proposed_change.save()


@flow(
    name="proposed-changed-data-integrity",
    flow_run_name="Triggers data integrity check",
)
async def run_proposed_change_data_integrity_check(model: RequestProposedChangeDataIntegrity) -> None:
    """Triggers a data integrity validation check on the provided proposed change to start."""

    service = services.service
    destination_branch = await registry.get_branch(db=service.database, branch=model.destination_branch)
    source_branch = await registry.get_branch(db=service.database, branch=model.source_branch)
    component_registry = get_component_registry()
    async with service.database.start_transaction() as dbt:
        diff_coordinator = await component_registry.get_component(DiffCoordinator, db=dbt, branch=source_branch)
        await diff_coordinator.update_branch_diff(base_branch=destination_branch, diff_branch=source_branch)
