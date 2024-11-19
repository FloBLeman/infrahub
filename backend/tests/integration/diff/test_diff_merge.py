import pytest
from infrahub_sdk import InfrahubClient

from infrahub.core.branch import Branch
from infrahub.core.constants import DiffAction
from infrahub.core.diff.coordinator import DiffCoordinator
from infrahub.core.diff.merger.merger import DiffMerger
from infrahub.core.diff.model.path import ConflictSelection
from infrahub.core.diff.repository.repository import DiffRepository
from infrahub.core.initialization import create_branch
from infrahub.core.manager import NodeManager
from infrahub.core.node import Node
from infrahub.core.timestamp import Timestamp
from infrahub.database import InfrahubDatabase
from infrahub.dependencies.registry import get_component_registry
from infrahub.services.adapters.cache.redis import RedisCache
from tests.adapters.message_bus import BusSimulator
from tests.constants import TestKind
from tests.helpers.schema import CAR_SCHEMA, load_schema
from tests.helpers.test_app import TestInfrahubApp

BRANCH_NAME = "this-branch"
PERSON_KIND = "TestingPerson"


class TestDiffMerge(TestInfrahubApp):
    @pytest.fixture(scope="class")
    async def initial_dataset(
        self,
        db: InfrahubDatabase,
        default_branch,
        client: InfrahubClient,
        bus_simulator: BusSimulator,
    ) -> dict[str, Node]:
        await load_schema(db, schema=CAR_SCHEMA)
        doc_brown = await Node.init(schema=TestKind.PERSON, db=db)
        await doc_brown.new(db=db, name="Doc Brown", height=175)
        await doc_brown.save(db=db)
        marty = await Node.init(schema=TestKind.PERSON, db=db)
        await marty.new(db=db, name="Marty McFly", height=155)
        await marty.save(db=db)
        biff = await Node.init(schema=TestKind.PERSON, db=db)
        await biff.new(db=db, name="Biff... something", height=177)
        await biff.save(db=db)
        dmc = await Node.init(schema=TestKind.MANUFACTURER, db=db)
        await dmc.new(db=db, name="DMC")
        await dmc.save(db=db)
        delorean = await Node.init(schema=TestKind.CAR, db=db)
        await delorean.new(
            db=db,
            name="Delorean",
            color="Silver",
            description="time-travelling coupe",
            owner=doc_brown,
            manufacturer=dmc,
        )
        await delorean.save(db=db)

        bus_simulator.service.cache = RedisCache()

        return {
            "doc_brown": doc_brown,
            "marty": marty,
            "biff": biff,
            "dmc": dmc,
            "delorean": delorean,
        }

    @pytest.fixture(scope="class")
    async def diff_branch(self, db: InfrahubDatabase, initial_dataset) -> Branch:
        return await create_branch(db=db, branch_name=BRANCH_NAME)

    @pytest.fixture(scope="class")
    async def diff_repository(self, db: InfrahubDatabase, default_branch: Branch) -> DiffRepository:
        component_registry = get_component_registry()
        return await component_registry.get_component(DiffRepository, db=db, branch=default_branch)

    @pytest.fixture(scope="class")
    async def diff_coordinator(self, db: InfrahubDatabase, default_branch: Branch) -> DiffCoordinator:
        component_registry = get_component_registry()
        return await component_registry.get_component(DiffCoordinator, db=db, branch=default_branch)

    async def _get_diff_merger(self, db: InfrahubDatabase, diff_branch: Branch) -> DiffMerger:
        component_registry = get_component_registry()
        return await component_registry.get_component(DiffMerger, db=db, branch=diff_branch)

    @pytest.fixture(scope="class")
    async def data_01_update_owner_conflict_select_base(
        self,
        db: InfrahubDatabase,
        initial_dataset,
        default_branch: Branch,
        diff_branch: Branch,
    ) -> None:
        delorean_id = initial_dataset["delorean"].get_id()
        marty_id = initial_dataset["marty"].get_id()
        biff_id = initial_dataset["biff"].get_id()

        delorean_main = await NodeManager.get_one(db=db, branch=default_branch, id=delorean_id)
        await delorean_main.owner.update(db=db, data=marty_id)
        await delorean_main.save(db=db)

        delorean_branch = await NodeManager.get_one(db=db, branch=diff_branch, id=delorean_id)
        await delorean_branch.owner.update(db=db, data=biff_id)
        await delorean_branch.save(db=db)

    async def test_select_cardinality_one_resolution_and_merge(
        self,
        db: InfrahubDatabase,
        initial_dataset,
        data_01_update_owner_conflict_select_base,
        default_branch: Branch,
        diff_branch: Branch,
        diff_coordinator: DiffCoordinator,
        diff_repository: DiffRepository,
    ):
        delorean_id = initial_dataset["delorean"].get_id()
        marty_id = initial_dataset["marty"].get_id()

        enriched_diff = await diff_coordinator.update_branch_diff(base_branch=default_branch, diff_branch=diff_branch)
        conflicts_map = enriched_diff.get_all_conflicts()
        assert len(conflicts_map) == 1
        owner_conflict = list(conflicts_map.values())[0]
        await diff_repository.update_conflict_by_id(
            conflict_id=owner_conflict.uuid, selection=ConflictSelection.BASE_BRANCH
        )
        right_now = Timestamp()
        diff_merger = await self._get_diff_merger(db=db, diff_branch=diff_branch)
        await diff_merger.merge_graph(at=right_now)

        delorean_main = await NodeManager.get_one(db=db, branch=default_branch, id=delorean_id)
        owner_peer = await delorean_main.owner.get_peer(db=db)
        assert owner_peer.get_id() == marty_id

    @pytest.mark.parametrize(
        "delete_on_branch",
        (
            True,
            False,
        ),
    )
    async def test_node_delete_conflict(
        self,
        db: InfrahubDatabase,
        initial_dataset,
        default_branch: Branch,
        diff_coordinator: DiffCoordinator,
        delete_on_branch: bool,
    ):
        new_person = await Node.init(db=db, schema=PERSON_KIND)
        await new_person.new(db=db, name="Chuck Berry")
        await new_person.save(db=db)
        diff_branch = await create_branch(db=db, branch_name="branch2")
        if delete_on_branch:
            delete_branch = default_branch
            update_branch = diff_branch
        else:
            delete_branch = diff_branch
            update_branch = default_branch
        person_main = await NodeManager.get_one(db=db, id=new_person.id, branch=delete_branch)
        await person_main.delete(db=db)

        # updates on branch for node deleted on main
        person_branch = await NodeManager.get_one(db=db, id=new_person.id, branch=update_branch)
        person_branch.description.value = "musician"
        await person_branch.save(db=db)
        new_car = await Node.init(schema=TestKind.CAR, db=db, branch=update_branch)
        await new_car.new(
            db=db,
            name="Pinto",
            color="charred",
            owner=person_branch,
            manufacturer=initial_dataset["dmc"].id,
        )
        await new_car.save(db=db)

        # check that the expected node-level conflict exists
        enriched_diff = await diff_coordinator.update_branch_diff(base_branch=default_branch, diff_branch=diff_branch)
        conflicts_map = enriched_diff.get_all_conflicts()
        assert set(conflicts_map.keys()) == {f"data/{person_branch.id}"}
        conflict = conflicts_map[f"data/{person_branch.id}"]
        if delete_on_branch:
            assert conflict.base_branch_action is DiffAction.REMOVED
            assert conflict.diff_branch_action is DiffAction.UPDATED
        else:
            assert conflict.base_branch_action is DiffAction.UPDATED
            assert conflict.diff_branch_action is DiffAction.REMOVED
        assert conflict.resolvable is False

        # manually undo updates on branch to resolve conflict
        person_branch = await NodeManager.get_one(db=db, id=new_person.id, branch=update_branch)
        person_branch.description.value = None
        await person_branch.save(db=db)
        car_branch = await NodeManager.get_one(db=db, id=new_car.id, branch=update_branch)
        await car_branch.owner.update(db=db, data=initial_dataset["biff"].id)
        await car_branch.save(db=db)

        # check that the conflict is gone
        enriched_diff = await diff_coordinator.update_branch_diff(base_branch=default_branch, diff_branch=diff_branch)
        conflicts_map = enriched_diff.get_all_conflicts()
        assert len(conflicts_map) == 0

        # merge the branch
        right_now = Timestamp()
        diff_merger = await self._get_diff_merger(db=db, diff_branch=diff_branch)
        await diff_merger.merge_graph(at=right_now)

        # check that the person is deleted on main
        person_main = await NodeManager.get_one(db=db, id=new_person.id)
        assert person_main is None
        car_main = await NodeManager.get_one(db=db, id=new_car.id)
        owner_peer = await car_main.owner.get_peer(db=db)
        assert owner_peer.id == initial_dataset["biff"].id
