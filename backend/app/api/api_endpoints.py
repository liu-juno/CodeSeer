import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.models import (
    ApiEndpoint, ApiEndpointVersion, ApiEnvironment,
    ApiTestCase, ApiTestRecord,
)
from app.schemas.schemas import (
    ApiEndpointCreate, ApiEndpointUpdate, ApiEndpointResponse,
    ApiEndpointVersionResponse,
    ApiEnvironmentCreate, ApiEnvironmentUpdate, ApiEnvironmentResponse,
    ApiTestCaseCreate, ApiTestCaseUpdate, ApiTestCaseResponse,
    ApiTestRequest, ApiTestRecordResponse,
)

router = APIRouter(prefix="/api-endpoints", tags=["api-endpoints"])


# ── 环境管理（独立资源） ──────────────────────────────────────────────

@router.get("/environments", response_model=List[ApiEnvironmentResponse])
async def list_environments(
    project_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiEnvironment)
        .where(ApiEnvironment.project_id == project_id)
        .order_by(ApiEnvironment.created_at)
    )
    return result.scalars().all()


@router.post("/environments", response_model=ApiEnvironmentResponse)
async def create_environment(data: ApiEnvironmentCreate, db: AsyncSession = Depends(get_db)):
    # 取消同项目其他默认环境
    if data.is_default:
        result = await db.execute(
            select(ApiEnvironment)
            .where(ApiEnvironment.project_id == data.project_id, ApiEnvironment.is_default == True)
        )
        for e in result.scalars().all():
            e.is_default = False
    db_env = ApiEnvironment(**data.model_dump())
    db.add(db_env)
    await db.commit()
    await db.refresh(db_env)
    return db_env


@router.put("/environments/{env_id}", response_model=ApiEnvironmentResponse)
async def update_environment(env_id: str, data: ApiEnvironmentUpdate, db: AsyncSession = Depends(get_db)):
    env = (await db.execute(select(ApiEnvironment).where(ApiEnvironment.id == env_id))).scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    body = data.model_dump(exclude_unset=True)
    if body.get("is_default"):
        result = await db.execute(
            select(ApiEnvironment)
            .where(ApiEnvironment.project_id == env.project_id, ApiEnvironment.id != env_id, ApiEnvironment.is_default == True)
        )
        for e in result.scalars().all():
            e.is_default = False
    for k, v in body.items():
        setattr(env, k, v)
    await db.commit()
    await db.refresh(env)
    return env


@router.delete("/environments/{env_id}")
async def delete_environment(env_id: str, db: AsyncSession = Depends(get_db)):
    env = (await db.execute(select(ApiEnvironment).where(ApiEnvironment.id == env_id))).scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    await db.delete(env)
    await db.commit()
    return {"message": "环境已删除"}


# ── 接口管理 ─────────────────────────────────────────────────────────────────

@router.get("/endpoints", response_model=List[ApiEndpointResponse])
async def list_endpoints(
    project_id: str = Query(...),
    method: Optional[str] = Query(None),
    module_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)
    if method:
        query = query.where(ApiEndpoint.method == method.upper())
    if module_id:
        query = query.where(ApiEndpoint.module_id == module_id)
    if status:
        query = query.where(ApiEndpoint.status == status)
    if search:
        search = f"%{search}%"
        query = query.where(
            (ApiEndpoint.path.ilike(search)) | (ApiEndpoint.summary.ilike(search))
        )
    query = query.order_by(ApiEndpoint.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/endpoints/{endpoint_id}", response_model=ApiEndpointResponse)
async def get_endpoint(endpoint_id: str, db: AsyncSession = Depends(get_db)):
    endpoint = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.id == endpoint_id))).scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="接口不存在")
    return endpoint


@router.post("/endpoints", response_model=ApiEndpointResponse)
async def create_endpoint(data: ApiEndpointCreate, db: AsyncSession = Depends(get_db)):
    endpoint = ApiEndpoint(
        project_id=data.project_id,
        method=data.method.upper(),
        path=data.path,
        summary=data.summary,
        description=data.description,
        request_schema=data.request_schema,
        response_schema=data.response_schema,
        headers=data.headers,
        module_id=data.module_id,
        status="draft",
        version=1,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return endpoint


@router.put("/endpoints/{endpoint_id}", response_model=ApiEndpointResponse)
async def update_endpoint(endpoint_id: str, data: ApiEndpointUpdate, db: AsyncSession = Depends(get_db)):
    endpoint = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.id == endpoint_id))).scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="接口不存在")
    body = data.model_dump(exclude_unset=True)
    schema_changed = (
        ("request_schema" in body and body["request_schema"] != endpoint.request_schema) or
        ("response_schema" in body and body["response_schema"] != endpoint.response_schema)
    )
    if schema_changed:
        endpoint.version += 1
        version = ApiEndpointVersion(
            endpoint_id=endpoint.id,
            version=endpoint.version,
            request_schema=body.get("request_schema", endpoint.request_schema),
            response_schema=body.get("response_schema", endpoint.response_schema),
            change_note=body.get("change_note", "Schema 更新"),
        )
        db.add(version)
    if "method" in body:
        body["method"] = body["method"].upper()
    for k, v in body.items():
        setattr(endpoint, k, v)
    await db.commit()
    await db.refresh(endpoint)
    return endpoint


@router.delete("/endpoints/{endpoint_id}")
async def delete_endpoint(endpoint_id: str, db: AsyncSession = Depends(get_db)):
    endpoint = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.id == endpoint_id))).scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="接口不存在")
    await db.delete(endpoint)
    await db.commit()
    return {"message": "接口已删除"}


@router.get("/endpoints/{endpoint_id}/versions", response_model=List[ApiEndpointVersionResponse])
async def list_endpoint_versions(endpoint_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiEndpointVersion)
        .where(ApiEndpointVersion.endpoint_id == endpoint_id)
        .order_by(ApiEndpointVersion.version.desc())
    )
    return result.scalars().all()


# ── 测试用例 ──────────────────────────────────────────────────────────────────

@router.get("/endpoints/{endpoint_id}/test-cases", response_model=List[ApiTestCaseResponse])
async def list_test_cases(endpoint_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiTestCase)
        .where(ApiTestCase.endpoint_id == endpoint_id)
        .order_by(ApiTestCase.created_at.desc())
    )
    return result.scalars().all()


@router.post("/endpoints/{endpoint_id}/test-cases", response_model=ApiTestCaseResponse)
async def create_test_case(endpoint_id: str, data: ApiTestCaseCreate, db: AsyncSession = Depends(get_db)):
    case = ApiTestCase(endpoint_id=endpoint_id, **data.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.put("/test-cases/{case_id}", response_model=ApiTestCaseResponse)
async def update_test_case(case_id: str, data: ApiTestCaseUpdate, db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(ApiTestCase).where(ApiTestCase.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(case, k, v)
    await db.commit()
    await db.refresh(case)
    return case


@router.delete("/test-cases/{case_id}")
async def delete_test_case(case_id: str, db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(ApiTestCase).where(ApiTestCase.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    await db.delete(case)
    await db.commit()
    return {"message": "测试用例已删除"}


# ── 在线测试 ──────────────────────────────────────────────────────────────────

async def _build_request(url: str, method: str, req_params: Optional[str], env: ApiEnvironment, endpoint: ApiEndpoint) -> dict:
    import httpx
    headers = {}
    if endpoint.headers:
        try:
            headers.update(json.loads(endpoint.headers))
        except Exception:
            pass
    if env.variables:
        try:
            headers.update(json.loads(env.variables))
        except Exception:
            pass
    params = None
    json_body = None
    if req_params:
        try:
            parsed = json.loads(req_params)
            if method.upper() == "GET":
                params = parsed
            else:
                json_body = parsed
        except Exception:
            pass
    return {"url": url, "method": method.upper(), "params": params, "json": json_body, "headers": headers}


async def _do_request(method: str, url: str, params, json_body, headers) -> tuple:
    import httpx
    start = datetime.utcnow()
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method=method, url=url, params=params, json=json_body, headers=headers)
        elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        return response, elapsed_ms


@router.post("/endpoints/{endpoint_id}/test")
async def test_endpoint(endpoint_id: str, req: ApiTestRequest, db: AsyncSession = Depends(get_db)):
    endpoint = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.id == endpoint_id))).scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="接口不存在")
    env = (await db.execute(select(ApiEnvironment).where(ApiEnvironment.id == req.environment_id))).scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="测试环境不存在")
    url = f"{env.base_url.rstrip('/')}{endpoint.path}"
    req_info = await _build_request(url, endpoint.method, req.request_params, env, endpoint)
    try:
        response, elapsed_ms = await _do_request(**req_info)
        result_val = "pass" if response.status_code < 400 else "fail"
        record = ApiTestRecord(
            endpoint_id=endpoint_id,
            environment_id=env.id,
            request_params=req.request_params,
            response_status=response.status_code,
            response_body=response.text[:5000],
            response_time_ms=elapsed_ms,
            result=result_val,
        )
        db.add(record)
        await db.commit()
        return {
            "status_code": response.status_code,
            "body": response.text,
            "elapsed_ms": elapsed_ms,
            "result": result_val,
            "record_id": record.id,
        }
    except httpx.TimeoutException:
        record = ApiTestRecord(
            endpoint_id=endpoint_id, environment_id=env.id,
            request_params=req.request_params, response_status=0, response_body="",
            response_time_ms=0, result="error", error_message="请求超时",
        )
        db.add(record)
        await db.commit()
        raise HTTPException(status_code=504, detail="请求超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-cases/{case_id}/run")
async def run_test_case(case_id: str, environment_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(ApiTestCase).where(ApiTestCase.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    endpoint = (await db.execute(select(ApiEndpoint).where(ApiEndpoint.id == case.endpoint_id))).scalar_one_or_none()
    env = (await db.execute(select(ApiEnvironment).where(ApiEnvironment.id == environment_id))).scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="测试环境不存在")
    url = f"{env.base_url.rstrip('/')}{endpoint.path}"
    req_info = await _build_request(url, endpoint.method, case.request_params, env, endpoint)
    try:
        response, elapsed_ms = await _do_request(**req_info)
        result_val = "pass" if (
            (case.expected_status and response.status_code == case.expected_status) or
            (not case.expected_status and response.status_code < 400)
        ) else "fail"
        record = ApiTestRecord(
            endpoint_id=case.endpoint_id, test_case_id=case.id, environment_id=env.id,
            request_params=case.request_params,
            response_status=response.status_code,
            response_body=response.text[:5000],
            response_time_ms=elapsed_ms,
            result=result_val,
        )
        db.add(record)
        await db.commit()
        return {
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "result": result_val,
            "record_id": record.id,
        }
    except httpx.TimeoutException:
        record = ApiTestRecord(
            endpoint_id=case.endpoint_id, test_case_id=case.id, environment_id=env.id,
            request_params=case.request_params, response_status=0, response_body="",
            response_time_ms=0, result="error", error_message="请求超时",
        )
        db.add(record)
        await db.commit()
        raise HTTPException(status_code=504, detail="请求超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 测试记录 ────────────────────────────────────────────────────────────────────

@router.get("/endpoints/{endpoint_id}/test-records", response_model=List[ApiTestRecordResponse])
async def list_test_records(
    endpoint_id: str,
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiTestRecord)
        .where(ApiTestRecord.endpoint_id == endpoint_id)
        .order_by(ApiTestRecord.executed_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
