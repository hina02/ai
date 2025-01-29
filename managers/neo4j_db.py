from neo4j import AsyncGraphDatabase, AsyncResult, Record

from config import settings

URI = settings.neo4j_uri
AUTH = ("neo4j", settings.neo4j_auth)

DIMENSION = 1536


async def get_10records(result: AsyncResult) -> list[Record]:
    records = await result.fetch(10)
    return records


class Neo4jDBManager:
    """TODO apoc.map.removeKeys vectorProperty"""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(URI, auth=AUTH)

    async def upsert_node(self, label: str, name: str, properties: dict) -> None:
        query = f"""
                CREATE (n:{label} {{name: $name}})
                SET n += $properties
                RETURN n
                """
        params = {"name": name, "properties": properties}
        record = await self.driver.execute_query(
            query, params, result_transformer_=AsyncResult.graph
        )
        return record

    async def get_node(self, label: str, name: str) -> Record | None:
        """指定したラベルのノードを取得する。"""
        query = f"""
                MATCH (n:{label})
                WHERE n.name = $name
                RETURN {{labels: labels(n), properties: properties(n)}} AS node
                """
        params = {"name": name}

        record = await self.driver.execute_query(
            query, params, result_transformer_=AsyncResult.single
        )
        return record

    async def get_nodes(self, label: str) -> list[Record]:
        """指定したラベルのノードを複数取得する。"""
        query = f"""
                MATCH (n:{label})
                RETURN {{labels: labels(n), properties: properties(n)}} AS node
                """

        records = await self.driver.execute_query(query, result_transformer_=get_10records)
        return records

    async def delete_node(self, name: str, label: str):
        query = f"""
                MATCH (n:{label} {{name: $name}})
                DETACH DELETE n
                """
        params = {"name": name}
        await self.driver.execute_query(query, params)

    async def create_relationship(
        self, type: str, label1: str, name1: str, label2: str, name2: str, properties: dict
    ):
        query = f"""
                MATCH (a:{label1} {{name: $name1}}),
                        (b:{label2} {{name: $name2}})
                CREATE (a)-[r:{type} {{timestamp: datetime({{timezone:"Asia/Tokyo"}})}}]->(b)
                SET r += $properties
                """
        params = {"name1": name1, "name2": name2, "properties": properties}

        await self.driver.execute_query(query, params)

    async def get_node_relationships_between(
        self, label1: str, name1: str, label2: str, name2: str
    ) -> list[Record]:
        query = f"""
                MATCH (a:{label1})-[r]-(b:{label2})
                WHERE a.name = $name1
                    AND b.name = $name2
                RETURN {{type: type(r), properties: properties(r)}} AS relationship
                """
        params = {"name1": name1, "name2": name2}

        return await self.driver.execute_query(query, params, result_transformer_=get_10records)

    async def get_relationships(self, type: str) -> list[Record]:
        query = f"""
                MATCH (a)-[r:{type}]-(b)
                RETURN {{type: type(r), properties: properties(r)}} AS relationship
                """

        return await self.driver.execute_query(query, result_transformer_=get_10records)
