import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .board import get_node


CONTRACTS_PATH = Path(__file__).resolve().parent / 'data' / 'contracts.json'


class InvalidContractConfiguration(RuntimeError):
    """Raised when the contract catalog is inconsistent."""


@lru_cache(maxsize=1)
def load_contracts() -> list[dict[str, Any]]:
    with CONTRACTS_PATH.open(encoding='utf-8') as contracts_file:
        contracts = json.load(contracts_file)

    if not isinstance(contracts, list) or not contracts:
        raise InvalidContractConfiguration('O catálogo de contratos deve ser uma lista preenchida.')

    contract_ids: set[str] = set()
    image_keys: set[str] = set()
    for contract in contracts:
        contract_id = contract.get('id')
        image_key = contract.get('imageKey')
        if not contract_id or contract_id in contract_ids:
            raise InvalidContractConfiguration('Os IDs dos contratos devem ser únicos.')
        if not image_key or image_key in image_keys:
            raise InvalidContractConfiguration('As imagens dos contratos devem ser únicas.')
        contract_ids.add(contract_id)
        image_keys.add(image_key)
        for field in ('title', 'cargo'):
            if not isinstance(contract.get(field), str) or not contract[field].strip():
                raise InvalidContractConfiguration(f'Campo {field} inválido no contrato {contract_id}.')
        try:
            origin = get_node(contract.get('originId', ''))
            destination = get_node(contract.get('destinationId', ''))
        except RuntimeError as error:
            raise InvalidContractConfiguration(
                f'Contrato {contract_id} referencia uma cidade inexistente.'
            ) from error
        if origin['type'] != 'CITY' or destination['type'] != 'CITY':
            raise InvalidContractConfiguration(
                f'Origem e destino do contrato {contract_id} precisam ser cidades.'
            )
        reward = contract.get('reward')
        if isinstance(reward, bool) or not isinstance(reward, int) or reward <= 0:
            raise InvalidContractConfiguration(f'Recompensa inválida no contrato {contract_id}.')

    return contracts


def get_contract(contract_id: str) -> dict[str, Any]:
    for contract in load_contracts():
        if contract['id'] == contract_id:
            return contract
    raise InvalidContractConfiguration(f'Contrato desconhecido: {contract_id}.')


def get_contracts_from_city(city_id: str) -> list[dict[str, Any]]:
    return [
        contract
        for contract in load_contracts()
        if contract['originId'] == city_id
    ]
