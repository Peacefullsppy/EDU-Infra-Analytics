import re

import httpx
from fastapi import HTTPException


async def consultar_cep(cep: str) -> dict:
    cep_limpo = re.sub(r"\D", "", cep)
    if len(cep_limpo) != 8:
        raise HTTPException(status_code=400, detail="CEP deve possuir 8 dígitos.")

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Não foi possível consultar o ViaCEP.")

    if data.get("erro"):
        raise HTTPException(status_code=404, detail="CEP não encontrado.")

    return {
        "cep": data.get("cep", ""),
        "logradouro": data.get("logradouro", ""),
        "bairro": data.get("bairro", ""),
        "localidade": data.get("localidade", ""),
        "uf": data.get("uf", ""),
    }
