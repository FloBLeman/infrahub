from datetime import timedelta
from typing import TYPE_CHECKING

from prefect import flow
from prefect.automations import AutomationCore
from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import DeploymentFilter, DeploymentFilterName
from prefect.events.actions import (
    RunDeployment,
)
from prefect.events.schemas.automations import EventTrigger, Posture
from prefect.events.schemas.events import ResourceSpecification
from prefect.logging import get_run_logger

from infrahub.core.registry import registry
from infrahub.services import services
from infrahub.support.macro import MacroDefinition
from infrahub.workflows.catalogue import PROCESS_COMPUTED_MACRO

if TYPE_CHECKING:
    from infrahub.core.schema.schema_branch import ComputedAttributeTarget
UPDATE_ATTRIBUTE = """
mutation UpdateAttribute(
    $id: String!,
    $kind: String!,
    $attribute: String!,
    $value: String!
  ) {
  InfrahubUpdateComputedAttribute(
    data: {id: $id, attribute: $attribute, value: $value, kind: $kind}
  ) {
    ok
  }
}
"""


@flow(name="process-computed-macro", log_prints=True)
async def process_macro(
    branch_name: str, node_kind: str, object_id: str, updated_fields: list[str] | None = None
) -> None:
    """Request to the creation of git branches in available repositories."""
    service = services.service
    schema_branch = registry.schema.get_schema_branch(name=branch_name)

    computed_macros = schema_branch.get_impacted_macros(kind=node_kind, updates=updated_fields)
    for computed_macro in computed_macros:
        found = []
        for id_filter in computed_macro.node_filters:
            filters = {id_filter: object_id}
            characters = await service.client.filters(
                kind=computed_macro.kind, prefetch_relationships=True, populate_store=True, **filters
            )
            found.extend(characters)

        if not found:
            print("No nodes found to apply Macro to")

        macro_definition = MacroDefinition(macro=computed_macro.attribute.computation_logic or "n/a")
        for node in found:
            my_filter = {}
            for variable in macro_definition.variables:
                components = variable.split("__")
                if len(components) == 2:
                    property_name = components[0]
                    property_value = components[1]
                    attribute_property = getattr(node, property_name)
                    my_filter[variable] = getattr(attribute_property, property_value)
                elif len(components) == 3:
                    relationship_name = components[0]
                    property_name = components[1]
                    property_value = components[2]
                    relationship = getattr(node, relationship_name)
                    try:
                        attribute_property = getattr(relationship.peer, property_name)
                        my_filter[variable] = getattr(attribute_property, property_value)
                    except ValueError:
                        my_filter[variable] = "MISSING"

            await service.client.execute_graphql(
                query=UPDATE_ATTRIBUTE,
                variables={
                    "id": node.id,
                    "kind": computed_macro.kind,
                    "attribute": computed_macro.attribute.name,
                    "value": macro_definition.render(variables=my_filter),
                },
                branch_name=branch_name,
            )
            print("#" * 40)
            print(f"node: {node.id}")
            print(f"attribute: {computed_macro.attribute.name}")
            print(f"value: {macro_definition.render(variables=my_filter)}")
            print()


@flow(name="computed-attribute-setup")
async def computed_attribute_setup() -> None:
    # service = services.service
    schema_branch = registry.schema.get_schema_branch(name=registry.default_branch)
    log = get_run_logger()
    async with get_client(sync_client=False) as client:
        deployments = {
            item.name: item
            for item in await client.read_deployments(
                deployment_filter=DeploymentFilter(name=DeploymentFilterName(any_=[PROCESS_COMPUTED_MACRO.name]))
            )
        }
        if PROCESS_COMPUTED_MACRO.name not in deployments:
            raise ValueError("Unable to find the deployment for PROCESS_COMPUTED_MACRO")
        deployment_id = deployments[PROCESS_COMPUTED_MACRO.name].id

        # TODO need to pull the existing automation to see if we need to create or update each object
        # automations = await client.read_automations()

        computed_attributes: dict[str, ComputedAttributeTarget] = {}
        for item in schema_branch._computed_macro_map.values():
            for attrs in list(item.local_fields.values()) + list(item.relationships.values()):
                for attr in attrs:
                    if attr.key_name in computed_attributes:
                        continue
                    log.info(f"found {attr.key_name}")
                    computed_attributes[attr.key_name] = attr

        for identifier, computed_attribute in computed_attributes.items():
            log.info(f"processing {computed_attribute.key_name}")
            automation = AutomationCore(
                name=f"computed-attribute-process-{identifier}",
                description=f"Process value of the computed attribute for {identifier}",
                enabled=True,
                trigger=EventTrigger(
                    posture=Posture.Reactive,
                    expect={"infrahub.node.*"},
                    within=timedelta(0),
                    match=ResourceSpecification({"infrahub.node.kind": [computed_attribute.kind]}),
                    threshold=1,
                ),
                actions=[
                    RunDeployment(
                        source="selected",
                        deployment_id=deployment_id,
                        parameters={
                            "branch_name": "{{ event.resource['infrahub.branch.name'] }}",
                            "node_kind": "{{ event.resource['infrahub.node.kind'] }}",
                            "object_id": "{{ event.resource['infrahub.node.id'] }}",
                        },
                        job_variables={},
                    )
                ],
            )

            response = await client.create_automation(automation=automation)
            log.info(f"Processed: {computed_attribute.key_name} : {response}")
