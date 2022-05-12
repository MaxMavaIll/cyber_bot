import environs

env = environs.Env()
env.read_env()
API_TOKEN = env.str("MINT_SCAN_API_TOKEN")

nodes = {
    "bostrom": ["/root/go/bin/cyber","https://rpc.bostrom.cybernode.ai:443"],
    #"juno": ["/root/go/bin/junod", "https://juno-rpc.polkachu.com:443"],
    # "stargaze": ["/root/go/bin/starsd", "https://stargaze-rpc.polkachu.com:443"],
    #"umee": ["/root/go/bin/umeed", "https://umee-rpc.polkachu.com:443"],
}
