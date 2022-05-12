import json
import logging
# import subprocess
from typing import Union

from fastapi import FastAPI, Request
import asyncio
import environs

app = FastAPI()
env = environs.Env()
env.read_env()
API_TOKEN = env.str("TOKEN")

nodes = {
    "juno": ["/root/go/bin/junod", "https://juno-rpc.polkachu.com:443"],
    "stargaze": ["/root/go/bin/starsd", "https://stargaze-rpc.polkachu.com:443"],
}

logging.getLogger(__name__).setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
)


async def load_block(parsing_application: str, url: str) -> Union[dict, None]:
    cmd = f"{parsing_application} q staking validators --node {url} -o json"

    return await run_app(cmd.split())


def get_index_by_moniker(moniker: str, validators: list):
    for index, val in enumerate(validators):
        if val.get("description").get("moniker") == moniker:
            return index


def get_consensus_pubkey(validator):
    return validator.get("consensus_pubkey").get("key")


async def slashing_signing_info(parsing_application, key, url):
    p_variable = {
        "@type": "/cosmos.crypto.ed25519.PubKey",
        "key": key,
    }
    p_json = json.dumps(p_variable)

    cmd = [parsing_application, 'q', 'slashing', 'signing-info', p_json, '--node', url, '-o', 'json']
    result = await run_app(cmd)
    return result


def get_missed_block_counter(result: dict):
    if missed_blocks_counter := result.get("missed_blocks_counter"):
        return int(missed_blocks_counter)


async def run_app(cmd: list) -> dict:
    # result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    # return result.stdout.decode('utf-8')
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    logging.info("cmd: %s", cmd)
    logging.info(f"stdout: {stdout.decode('utf-8')}, stderr: {stderr.decode('utf-8')}")
    result = stdout.decode('utf-8')
    if result:
        result = json.loads(result)
        return result


@app.post("/{platform}")
async def parse_application(request: Request, platform: str):
    data = await request.json()
    token: str = data.get("token")
    moniker: str = data.get("moniker")

    if token != API_TOKEN:
        return {"error": "Invalid token"}
    if not moniker:
        return {"error": "moniker is not defined"}
    parsing_application, url = nodes.get(platform, [None, None])
    if not parsing_application:
        return {"error": "platform does not exist"}

    block = await load_block(parsing_application, url)

    if not block:
        return {"error": "Invalid platform"}

    validators = block.get("validators")
    if not validators:
        return {"error": "No validators"}

    moniker_index = get_index_by_moniker(moniker, validators)
    if not moniker_index:
        return {"error": "No validator with this moniker"}

    consensus_pubkey = get_consensus_pubkey(validators[moniker_index])
    if not consensus_pubkey:
        return {"error": "No consensus pubkey"}

    slashing_info = await slashing_signing_info(parsing_application, consensus_pubkey, url)
    if not slashing_info:
        return {"error": "No slashing info"}
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
        return {"error": "Invalid token"}

    parsing_application, url = nodes.get(platform, [None, None])
    if not parsing_application:
        return {"error": "platform does not exist"}

    slashing_info = await slashing_signing_info(parsing_application, consensus_pubkey, url)
    if not slashing_info:
        return {"error": "No slashing info"}
    missed_block_counter = get_missed_block_counter(slashing_info)
    if missed_block_counter is not None:
        return {'ok': True, 'missed_blocks_counter': missed_block_counter}
    else:
        return {'error': 'No missed blocks', 'missed_blocks_counter': 0}
