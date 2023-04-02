from asyncio import run as aiorun

from rich import print as rprint

from infrahub_client import InfrahubClient


async def main():
    client = await InfrahubClient.init(address="http://localhost:8000")
    accounts = await client.all(kind="Account")
    rprint(accounts)

if __name__ == "__main__":
    aiorun(main())
