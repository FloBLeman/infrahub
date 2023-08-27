import pytest

from infrahub.core.initialization import create_branch
from infrahub.core.node import Node
from infrahub_client import Config, InfrahubClientSync
from infrahub_client.node import InfrahubNodeSync

from .conftest import InfrahubTestClient

# pylint: disable=unused-argument


class TestInfrahubClientSync:
    @pytest.fixture(scope="class")
    async def test_client(self):
        # pylint: disable=import-outside-toplevel
        from infrahub.server import app

        return InfrahubTestClient(app)

    @pytest.fixture
    def client(self, test_client):
        config = Config(sync_requester=test_client.sync_request)
        return InfrahubClientSync.init(config=config)

    @pytest.fixture(scope="class")
    async def base_dataset(self, session):
        await create_branch(branch_name="branch01", session=session)

        query_string = """
        query {
            branch {
                id
                name
            }
        }
        """
        obj1 = await Node.init(schema="CoreGraphQLQuery", session=session)
        await obj1.new(session=session, name="test_query2", description="test query", query=query_string)
        await obj1.save(session=session)

        obj2 = await Node.init(schema="CoreRepository", session=session)
        await obj2.new(
            session=session, name="repository1", description="test repository", location="git@github.com:mock/test.git"
        )
        await obj2.save(session=session)

        obj3 = await Node.init(schema="CoreRFile", session=session)
        await obj3.new(
            session=session,
            name="rfile1",
            description="test rfile",
            template_path="mytemplate.j2",
            repository=obj2,
            query=obj1,
        )
        await obj3.save(session=session)

        obj4 = await Node.init(schema="CoreTransformPython", session=session)
        await obj4.new(
            session=session,
            name="transform01",
            description="test transform01",
            file_path="mytransformation.py",
            class_name="Transform01",
            query=obj1,
            url="tf01",
            repository=obj2,
            rebase=False,
        )
        await obj4.save(session=session)

    async def test_query_branches(self, client: InfrahubClientSync, init_db_base, base_dataset):
        branches = client.branch.all()

        assert "main" in branches
        assert "branch01" in branches

    async def test_branch_delete(self, client: InfrahubClientSync, init_db_base, base_dataset, session):
        async_branch = "async-delete-branch"
        await create_branch(branch_name=async_branch, session=session)

        pre_delete = client.branch.all()
        client.branch.delete(async_branch)
        post_delete = client.branch.all()
        assert async_branch in pre_delete.keys()
        assert async_branch not in post_delete.keys()

    async def test_get_all(self, client: InfrahubClientSync, session, init_db_base):
        obj1 = await Node.init(schema="BuiltinLocation", session=session)
        await obj1.new(session=session, name="jfk1", description="new york", type="site")
        await obj1.save(session=session)

        obj2 = await Node.init(schema="BuiltinLocation", session=session)
        await obj2.new(session=session, name="sfo1", description="san francisco", type="site")
        await obj2.save(session=session)

        nodes = client.all(kind="BuiltinLocation")
        assert len(nodes) == 2
        assert isinstance(nodes[0], InfrahubNodeSync)
        assert sorted([node.name.value for node in nodes]) == ["jfk1", "sfo1"]  # type: ignore[attr-defined]

    async def test_get_one(self, client: InfrahubClientSync, session, init_db_base):
        obj1 = await Node.init(schema="BuiltinLocation", session=session)
        await obj1.new(session=session, name="jfk2", description="new york", type="site")
        await obj1.save(session=session)

        obj2 = await Node.init(schema="BuiltinLocation", session=session)
        await obj2.new(session=session, name="sfo2", description="san francisco", type="site")
        await obj2.save(session=session)

        node1 = client.get(kind="BuiltinLocation", id=obj1.id)
        assert isinstance(node1, InfrahubNodeSync)
        assert node1.name.value == "jfk2"  # type: ignore[attr-defined]

        node2 = client.get(kind="BuiltinLocation", id="jfk2")
        assert isinstance(node2, InfrahubNodeSync)
        assert node2.name.value == "jfk2"  # type: ignore[attr-defined]

    async def test_get_related_nodes(self, client: InfrahubClientSync, session, init_db_base):
        nodes = client.all(kind="CoreRepository")
        assert len(nodes) == 1
        repo = nodes[0]

        assert repo.transformations.peers == []  # type: ignore[attr-defined]
        repo.transformations.fetch()  # type: ignore[attr-defined]
        assert len(repo.transformations.peers) == 2  # type: ignore[attr-defined]
