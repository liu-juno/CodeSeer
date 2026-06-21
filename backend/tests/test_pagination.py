from app.schemas.schemas import PaginatedResponse

def test_paginated_response_structure():
    response = PaginatedResponse(items=[], total=0, page=1, page_size=20)
    assert response.items == []
    assert response.total == 0
    assert response.page == 1
    assert response.page_size == 20


def test_paginated_response_with_items():
    items = [{"id": "1", "name": "test"}]
    response = PaginatedResponse(items=items, total=1, page=1, page_size=20)
    assert len(response.items) == 1
    assert response.total == 1
    assert response.items[0]["name"] == "test"
