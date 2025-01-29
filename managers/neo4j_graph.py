import json

from neo4j import GraphDatabase, Record, Result
from neo4j_graphrag import indexes
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import VectorRetriever

from config import settings

URI = settings.neo4j_uri
AUTH = ("neo4j", settings.neo4j_auth)

DIMENSION = 1536


def get_10records(result: Result) -> list[Record]:
    records = result.fetch(10)
    return records


class Neo4jGraphManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=AUTH)
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    def __del__(self):
        self.driver.close()

    def create_index(self, label: str, index_name: str):
        create_vector_index(
            self.driver,
            index_name,
            label=label,
            embedding_property="vectorProperty",
            dimensions=DIMENSION,
            similarity_fn="euclidean",
        )

    def get_node_ids(self, label: str) -> list[Record]:
        """指定したラベルのノードのelementIDを取得する。"""
        query = f"""
                MATCH (n:{label})
                RETURN {{
                    id: elementId(n),
                    properties: apoc.map.removeKeys(properties(n), ['vectorProperty', 'timestamp'])
                }} AS node
                """

        records = self.driver.execute_query(query, result_transformer_=get_10records)
        return records

    def get_relationship_ids(self, type: str) -> list[Record]:
        query = f"""
                MATCH (a)-[r:{type}]-(b)
                RETURN {{
                    id: elementId(r),
                    properties: apoc.map.removeKeys(properties(r), ['vectorProperty', 'timestamp'])
                }} AS relationship
                """

        records = self.driver.execute_query(query, result_transformer_=get_10records)
        return records

    def upsert_vector(self, node_id: str, node_props: dict):
        """
        Example:
        create_index("Person")

        records = get_node_ids("Person")
        for node in records:
            upsert_vector(node.get("id"), node.get("properties"))
        """
        dict_json = json.dumps(node_props)
        embeddings = self.embedder.embed_query(dict_json)
        indexes.upsert_vector(  # async_upsert_vectorはエラー
            self.driver,
            node_id=node_id,  # element id
            embedding_property="vectorProperty",
            vector=embeddings,
        )

    def upsert_vector_on_relationship(self, rel_id: str, rel_props: dict):
        """
        Example:
        create_index("KNOWS", "relationship-index")

        records = get_relationship_ids("KNOWS")
        for item in records:
            rel = item.get("relationship")
            upsert_vector_on_relationship(rel.get("id"), rel.get("properties"))
        """
        dict_json = json.dumps(rel_props)
        embeddings = self.embedder.embed_query(dict_json)
        indexes.upsert_vector_on_relationship(  # async_upsert_vector_on_relationshipはエラー
            self.driver,
            rel_id=rel_id,
            embedding_property="vectorProperty",
            vector=embeddings,
        )

    async def query(self, query: str, index_name: str):
        retriever = VectorRetriever(self.driver, index_name, self.embedder)
        llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
        rag = GraphRAG(retriever=retriever, llm=llm)

        response = rag.search(query_text=query, retriever_config={"top_k": 5})
        return response.answer
