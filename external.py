import re

import httpx
from fastapi import HTTPException

VIA_CEP_URL = "https://viacep.com.br/ws/{cep}/json/"


async def consultar_cep(cep: str) -> dict:
    cep_limpo = re.sub(r"\D", "", cep)
    if len(cep_limpo) != 8:
        raise HTTPException(status_code=400, detail="O CEP deve possuir 8 dígitos.")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(VIA_CEP_URL.format(cep=cep_limpo))
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar o serviço externo de CEP.",
        ) from exc

    if data.get("erro"):
        raise HTTPException(status_code=404, detail="CEP não encontrado.")

    return {
        "cep": data.get("cep", cep_limpo),
        "logradouro": data.get("logradouro") or None,
        "complemento": data.get("complemento") or None,
        "bairro": data.get("bairro") or None,
        "cidade": data.get("localidade", ""),
        "uf": data.get("uf", ""),
        "ibge": data.get("ibge") or None,
    }
