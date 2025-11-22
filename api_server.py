#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Server для Real Estate Parser
Принимает GET/POST запросы с JSON и возвращает результаты парсинга
"""

import json
from typing import Any, Optional
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from parser import RealEstateParser

app = FastAPI(title="Real Estate Parser API", version="1.0.0")


@app.get("/parse")
async def parse_get(
    data: Optional[str] = Query(None, description="JSON строка с данными для парсинга"),
    json_data: Optional[str] = Query(None, alias="json", description="JSON строка с данными для парсинга")
):
    """
    Endpoint для парсинга недвижимости (GET)
    
    Принимает JSON через query параметр 'data' или 'json'
    """
    json_str = data or json_data
    
    if not json_str:
        raise HTTPException(
            status_code=400,
            detail="No data provided. Use 'data' or 'json' query parameter"
        )
    
    try:
        data_list = json.loads(json_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in query parameter")
    
    return await _process_parse_request(data_list)


@app.post("/parse")
async def parse_post(request: Request):
    """
    Endpoint для парсинга недвижимости (POST)
    
    Принимает JSON в теле запроса.
    Может быть один объект: {"site_url": "...", "selectors": {...}}
    Или массив объектов: [{"site_url": "...", "selectors": {...}}, ...]
    """
    try:
        data = await request.json()
    except Exception:
        # Пробуем прочитать как raw JSON
        try:
            body = await request.body()
            data = json.loads(body.decode('utf-8'))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in request body: {str(e)}")
    
    return _process_parse_request(data)


async def _process_parse_request(data: Any) -> JSONResponse:
    """
    Обрабатывает запрос на парсинг
    
    Принимает как один объект, так и массив объектов
    
    Args:
        data: Объект сайта или список сайтов для парсинга
        
    Returns:
        JSONResponse с результатами парсинга
    """
    # Нормализуем данные: если пришел один объект, оборачиваем в массив
    if isinstance(data, dict):
        # Один объект - оборачиваем в массив
        data_list = [data]
    elif isinstance(data, list):
        # Уже массив
        data_list = data
    else:
        raise HTTPException(
            status_code=400, 
            detail="Expected an object with 'site_url' and 'selectors' or an array of such objects"
        )
    
    # Валидация структуры данных
    for site in data_list:
        if not isinstance(site, dict):
            raise HTTPException(status_code=400, detail="Each site must be an object")
        if "site_url" not in site:
            raise HTTPException(status_code=400, detail="Each site must have 'site_url' field")
        if "selectors" not in site:
            raise HTTPException(status_code=400, detail="Each site must have 'selectors' field")
    
    try:
        # Создаем парсер и парсим
        parser = RealEstateParser(headless=True)
        try:
            results = await parser.parse_all_sites(data_list)
            # Возвращаем результаты в виде чистого JSON
            return JSONResponse(
                content=results,
                media_type='application/json'
            )
        finally:
            # Очищаем ресурсы браузера
            await parser.cleanup()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)

