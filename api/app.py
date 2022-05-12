import logging
from fastapi import FastAPI, Request

from errors import Errors
from config import API_TOKEN, nodes
from functions import load_block, get_index_by_moniker, get_consensus_pubkey, slashing_signing_info, \
    get_missed_block_counter

app = FastAPI()

logging.getLogger(__name__).setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
)


@app.post('/load_validators/{platform}')
async def load_validators_by_platform(request: Request, platform: str):
    data = await request.json()
    if not data:
        return {"error": Errors.NoData, "ok": False}
    token = data.get("token")
    if token != API_TOKEN:
        return {"error": Errors.InvalidToken, "ok": False}

    parsing_application, url = nodes.get(platform, [None, None])
    if not parsing_application:
        return {"error": Errors.InvalidPlatform, "ok": False}

    block = await load_block(parsing_application, url)
    if not block:
        return {"error": Errors.NoBlocks, "ok": False}

    validators = block.get("validators")
    if not validators:
        return {"error": Errors.NoValidators, "ok": False}

    return {'ok': True, 'validators': validators}


@app.post("/{platform}")
async def parse_application(request: Request, platform: str):
    data = await request.json()
    token: str = data.get("token")
    moniker: str = data.get("moniker")

    if token != API_TOKEN:
        return {"error": Errors.InvalidToken, "ok": False}
    if not moniker:
        return {"error": Errors.NoMonikerSpecified, "ok": False}
    parsing_application, url = nodes.get(platform, [None, None])
    if not parsing_application:
        return {"error": Errors.InvalidPlatform, "ok": False}

    block = await load_block(parsing_application, url)

    if not block:
        return {"error": Errors.NoBlocks, "ok": False}

    validators = block.get("validators")
    if not validators:
        return {"error": Errors.NoValidators, "ok": False}

    moniker_index = get_index_by_moniker(moniker, validators)
    print(moniker_index)
    moniker_index += 1
    if not moniker_index:
        return {"error": Errors.NoValidatorWithMoniker, "ok": False}
    moniker_index -= 1
    consensus_pubkey = get_consensus_pubkey(validators[moniker_index])
    if not consensus_pubkey:
        return {"error": Errors.NoConsensusPubkey, "ok": False}

    slashing_info = await slashing_signing_info(parsing_application, consensus_pubkey, url)
    if not slashing_info:
        return {"error": Errors.NoSlashingInfo, "ok": False}
    else:
        return {
            'ok': True, 'missed_blocks_counter': get_missed_block_counter(slashing_info),
            'data': {'consensus_pubkey': consensus_pubkey}
        }


@app.post('/repeat/missed_block_counter')
async def repeat_missed_block_counter(request: Request):
    data = await request.json()
    if not data:
        return {"error": "No data"}
    token = data.get("token")
    platform = data.get("platform")
    consensus_pubkey = data.get("consensus_pubkey")
    if token != API_TOKEN:
        return {"error": "Invalid token", "ok": False}

    parsing_application, url = nodes.get(platform, [None, None])
    if not parsing_application:
        return {"error": "platform does not exist", "ok": False}

    slashing_info = await slashing_signing_info(parsing_application, consensus_pubkey, url)
    if not slashing_info:
        return {"error": "No slashing info", "ok": False}
    missed_block_counter = get_missed_block_counter(slashing_info)
    if missed_block_counter is not None:
        return {'ok': True, 'missed_blocks_counter': missed_block_counter}
    else:
        return {'error': 'No missed blocks', 'missed_blocks_counter': 0, "ok": False}
