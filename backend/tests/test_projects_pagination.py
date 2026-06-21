import pytest


@pytest.mark.asyncio
async def test_list_projects_pagination(client):
    """分页默认 page_size=20，第一页应有 items/total/page/page_size"""
    res = await client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data, f"Expected 'items' in response, got: {data}"
    assert "total" in data, f"Expected 'total' in response, got: {data}"
    assert "page" in data, f"Expected 'page' in response, got: {data}"
    assert "page_size" in data, f"Expected 'page_size' in response, got: {data}"
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_projects_pagination_second_page(client):
    """分页第二页应返回剩余数据"""
    res = await client.get("/api/projects?page=2&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 2
    assert data["page_size"] == 5
