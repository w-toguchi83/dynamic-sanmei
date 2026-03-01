"""Integration tests for Query API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def entity_type_with_data(client: AsyncClient) -> dict[str, str | list[str]]:
    """Create entity type with sample entities for query testing.

    Creates:
    - Entity type 'Product' with name (string), price (integer), category (string)
    - 5 product entities with various prices and categories

    Returns:
        Dictionary with entity_type_name, entity_type_id, and entity_ids list.
    """
    # Create entity type with unique name
    unique_suffix = uuid4().hex[:8]
    type_name = f"Product_{unique_suffix}"
    entity_type_payload = {
        "name": type_name,
        "description": "Product entity type for query tests",
        "properties": {
            "name": {
                "type": "string",
                "required": True,
                "indexed": True,
            },
            "price": {
                "type": "integer",
                "required": True,
                "indexed": True,
            },
            "category": {
                "type": "string",
                "required": True,
                "indexed": True,
            },
        },
        "custom_validators": [],
    }
    et_response = await client.post(
        "/schema/entity-types", json=entity_type_payload
    )
    assert et_response.status_code == 201
    entity_type_id = et_response.json()["id"]

    # Create sample products
    products = [
        {"name": "Laptop", "price": 1000, "category": "electronics"},
        {"name": "Phone", "price": 500, "category": "electronics"},
        {"name": "Desk", "price": 200, "category": "furniture"},
        {"name": "Chair", "price": 100, "category": "furniture"},
        {"name": "Tablet", "price": 300, "category": "electronics"},
    ]

    entity_ids: list[str] = []
    for product in products:
        payload = {
            "type_id": entity_type_id,
            "properties": product,
        }
        response = await client.post("/entities", json=payload)
        assert response.status_code == 201
        entity_ids.append(response.json()["id"])

    return {
        "entity_type_name": type_name,
        "entity_type_id": entity_type_id,
        "entity_ids": entity_ids,
    }


@pytest.fixture
async def setup_with_relationships(client: AsyncClient) -> dict[str, str | list[str]]:
    """Create entity types, entities, and relationships for traversal testing.

    Creates:
    - EntityType 'Author' with name property
    - EntityType 'Book' with title, year properties
    - RelationshipType 'wrote' (directional)
    - 2 authors, 3 books, relationships between them

    Returns:
        Dictionary with type names, IDs, entity IDs, and relationship type name.
    """
    unique_suffix = uuid4().hex[:8]

    # Create Author entity type
    author_type_name = f"Author_{unique_suffix}"
    author_type_payload = {
        "name": author_type_name,
        "description": "Author entity type",
        "properties": {
            "name": {
                "type": "string",
                "required": True,
                "indexed": True,
            },
        },
        "custom_validators": [],
    }
    at_response = await client.post(
        "/schema/entity-types", json=author_type_payload
    )
    assert at_response.status_code == 201
    author_type_id = at_response.json()["id"]

    # Create Book entity type
    book_type_name = f"Book_{unique_suffix}"
    book_type_payload = {
        "name": book_type_name,
        "description": "Book entity type",
        "properties": {
            "title": {
                "type": "string",
                "required": True,
                "indexed": True,
            },
            "year": {
                "type": "integer",
                "required": True,
            },
        },
        "custom_validators": [],
    }
    bt_response = await client.post("/schema/entity-types", json=book_type_payload)
    assert bt_response.status_code == 201
    book_type_id = bt_response.json()["id"]

    # Create relationship type
    rel_type_name = f"wrote_{unique_suffix}"
    rel_type_payload = {
        "name": rel_type_name,
        "description": "Author wrote book",
        "directional": True,
        "properties": {},
        "custom_validators": [],
    }
    rt_response = await client.post(
        "/schema/relationship-types", json=rel_type_payload
    )
    assert rt_response.status_code == 201
    rel_type_id = rt_response.json()["id"]

    # Create authors
    author1_payload = {"type_id": author_type_id, "properties": {"name": "Alice Writer"}}
    a1_response = await client.post("/entities", json=author1_payload)
    assert a1_response.status_code == 201
    author1_id = a1_response.json()["id"]

    author2_payload = {"type_id": author_type_id, "properties": {"name": "Bob Author"}}
    a2_response = await client.post("/entities", json=author2_payload)
    assert a2_response.status_code == 201
    author2_id = a2_response.json()["id"]

    # Create books
    book1_payload = {"type_id": book_type_id, "properties": {"title": "First Book", "year": 2020}}
    b1_response = await client.post("/entities", json=book1_payload)
    assert b1_response.status_code == 201
    book1_id = b1_response.json()["id"]

    book2_payload = {"type_id": book_type_id, "properties": {"title": "Second Book", "year": 2021}}
    b2_response = await client.post("/entities", json=book2_payload)
    assert b2_response.status_code == 201
    book2_id = b2_response.json()["id"]

    book3_payload = {"type_id": book_type_id, "properties": {"title": "Third Book", "year": 2022}}
    b3_response = await client.post("/entities", json=book3_payload)
    assert b3_response.status_code == 201
    book3_id = b3_response.json()["id"]

    # Create relationships: Alice wrote book1 and book2, Bob wrote book3
    rel1_payload = {
        "type_id": rel_type_id,
        "from_entity_id": author1_id,
        "to_entity_id": book1_id,
        "properties": {},
    }
    await client.post("/relationships", json=rel1_payload)

    rel2_payload = {
        "type_id": rel_type_id,
        "from_entity_id": author1_id,
        "to_entity_id": book2_id,
        "properties": {},
    }
    await client.post("/relationships", json=rel2_payload)

    rel3_payload = {
        "type_id": rel_type_id,
        "from_entity_id": author2_id,
        "to_entity_id": book3_id,
        "properties": {},
    }
    await client.post("/relationships", json=rel3_payload)

    return {
        "author_type_name": author_type_name,
        "author_type_id": author_type_id,
        "book_type_name": book_type_name,
        "book_type_id": book_type_id,
        "rel_type_name": rel_type_name,
        "rel_type_id": rel_type_id,
        "author1_id": author1_id,
        "author2_id": author2_id,
        "book1_id": book1_id,
        "book2_id": book2_id,
        "book3_id": book3_id,
    }


class TestQueryAPI:
    """Tests for Query API endpoint."""

    async def test_query_simple(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with just entity_type returns all entities of that type."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        # Should have 5 products
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["limit"] == 100  # default
        assert data["offset"] == 0  # default

    async def test_query_with_filter(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with filter returns matching entities."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "filter": {
                "field": "category",
                "op": "eq",
                "value": "electronics",
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should have 3 electronics products: Laptop, Phone, Tablet
        assert data["total"] == 3
        assert len(data["items"]) == 3
        for item in data["items"]:
            assert item["properties"]["category"] == "electronics"

    async def test_query_with_and_filter(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with AND filter returns entities matching all conditions."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "filter": {
                "and": [
                    {"field": "category", "op": "eq", "value": "electronics"},
                    {"field": "price", "op": "gt", "value": 400},
                ],
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Electronics with price > 400: Laptop (1000), Phone (500)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["properties"]["category"] == "electronics"
            assert item["properties"]["price"] > 400

    async def test_query_with_sort_and_pagination(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with sort and pagination returns correct pages."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        # Test pagination with sort by name (string) - string sorting is reliable
        payload = {
            "entity_type": type_name,
            "sort": [{"field": "name", "order": "asc"}],
            "limit": 2,
            "offset": 0,
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # Total count remains 5
        assert len(data["items"]) == 2  # But only 2 returned
        assert data["limit"] == 2
        assert data["offset"] == 0
        # Should be sorted by name ascending
        first_page_names = [item["properties"]["name"] for item in data["items"]]
        # Alphabetically: Chair, Desk, Laptop, Phone, Tablet
        assert first_page_names == ["Chair", "Desk"]

        # Get second page
        payload["offset"] = 2
        response2 = await client.post("/query", json=payload)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2
        assert data2["offset"] == 2
        second_page_names = [item["properties"]["name"] for item in data2["items"]]
        assert second_page_names == ["Laptop", "Phone"]

        # Get third page (should have only 1 item)
        payload["offset"] = 4
        response3 = await client.post("/query", json=payload)
        assert response3.status_code == 200
        data3 = response3.json()
        assert len(data3["items"]) == 1
        assert data3["items"][0]["properties"]["name"] == "Tablet"

    async def test_query_with_aggregation(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with aggregation returns computed values."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "aggregate": {
                "count": True,
                "sum": "price",
                "avg": "price",
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Aggregation queries return empty items
        assert len(data["items"]) == 0
        assert "aggregations" in data
        assert data["aggregations"] is not None
        # Count should be 5
        assert data["aggregations"]["count"] == 5
        # Sum: 1000 + 500 + 200 + 100 + 300 = 2100
        assert data["aggregations"]["sum"] == 2100
        # Avg: 2100 / 5 = 420
        assert data["aggregations"]["avg"] == 420

    async def test_query_with_aggregation_group_by(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with group_by aggregation returns grouped results."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "aggregate": {
                "count": True,
                "group_by": ["category"],
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "aggregations" in data
        assert data["aggregations"] is not None
        assert "groups" in data["aggregations"]
        groups = data["aggregations"]["groups"]
        assert len(groups) == 2  # electronics and furniture

        # Find electronics group
        electronics_group = next((g for g in groups if g.get("category") == "electronics"), None)
        assert electronics_group is not None
        assert electronics_group["count"] == 3

        # Find furniture group
        furniture_group = next((g for g in groups if g.get("category") == "furniture"), None)
        assert furniture_group is not None
        assert furniture_group["count"] == 2

    async def test_query_invalid_entity_type(self, client: AsyncClient) -> None:
        """POST /query with non-existent entity_type returns empty result."""
        payload = {
            "entity_type": "NonExistentType_abc123",
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should return empty result, not error
        assert data["items"] == []
        assert data["total"] == 0

    async def test_query_invalid_filter_operator(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with invalid operator returns 400 error."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "filter": {
                "field": "price",
                "op": "invalid_operator",
                "value": 100,
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid_operator" in data["detail"].lower()

    async def test_query_invalid_sort_order(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with invalid sort order returns 400 error."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "sort": [{"field": "price", "order": "invalid"}],
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()

    async def test_query_with_traversal(
        self, client: AsyncClient, setup_with_relationships: dict[str, str | list[str]]
    ) -> None:
        """POST /query with traverse returns related entities."""
        author_type_name = setup_with_relationships["author_type_name"]
        rel_type_name = setup_with_relationships["rel_type_name"]
        author1_id = setup_with_relationships["author1_id"]

        assert isinstance(author_type_name, str)
        assert isinstance(rel_type_name, str)
        assert isinstance(author1_id, str)

        payload = {
            "entity_type": author_type_name,
            "filter": {
                "field": "name",
                "op": "eq",
                "value": "Alice Writer",
            },
            "traverse": {
                "type": rel_type_name,
                "direction": "outgoing",
                "depth": 1,
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should return Alice as the item
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["properties"]["name"] == "Alice Writer"

        # Should have related entities
        assert "related_entities" in data
        assert data["related_entities"] is not None
        assert len(data["related_entities"]) == 1

        # Alice wrote 2 books
        related = data["related_entities"][0]
        assert related["entity_id"] == author1_id
        assert len(related["related"]) == 2

    async def test_query_with_or_filter(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with OR filter returns entities matching any condition."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "filter": {
                "or": [
                    {"field": "price", "op": "eq", "value": 100},
                    {"field": "price", "op": "eq", "value": 1000},
                ],
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Chair (100) and Laptop (1000)
        assert data["total"] == 2
        prices = [item["properties"]["price"] for item in data["items"]]
        assert 100 in prices
        assert 1000 in prices

    async def test_query_with_in_operator(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with IN operator returns matching entities."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        payload = {
            "entity_type": type_name,
            "filter": {
                "field": "name",
                "op": "in",
                "value": ["Laptop", "Phone", "Desk"],
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        names = [item["properties"]["name"] for item in data["items"]]
        assert "Laptop" in names
        assert "Phone" in names
        assert "Desk" in names


class TestQueryAPIRegexFilter:
    """Tests for REGEX filter in Query API."""

    async def test_query_with_regex_filter(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with REGEX filter should match patterns."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        # Query products starting with 'La' (Laptop)
        payload = {
            "entity_type": type_name,
            "filter": {
                "field": "name",
                "op": "regex",
                "value": "^La.*",
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["properties"]["name"] == "Laptop"


class TestQueryAPIFullTextFilter:
    """Tests for FULL_TEXT filter in Query API."""

    async def test_query_with_full_text_filter(
        self, client: AsyncClient, entity_type_with_data: dict[str, str | list[str]]
    ) -> None:
        """POST /query with FULL_TEXT filter should match words."""
        type_name = entity_type_with_data["entity_type_name"]
        assert isinstance(type_name, str)

        # Full-text search for "electronics" category
        payload = {
            "entity_type": type_name,
            "filter": {
                "field": "category",
                "op": "full_text",
                "value": "electronics",
            },
        }

        response = await client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should match: Laptop, Phone, Tablet (all in electronics category)
        assert data["total"] == 3
        names = {item["properties"]["name"] for item in data["items"]}
        assert names == {"Laptop", "Phone", "Tablet"}
