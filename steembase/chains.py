default_prefix = "STM"

known_chains = {
    "STEEM": {
        "chain_id": "0" * int(256 / 4),
        "prefix": "STM",
        "steem_symbol": "STEEM",
        "sbd_symbol": "SBD",
        "vests_symbol": "VESTS",
    },
    "TEST": {
        "chain_id": "18dcf0a285365fc58b71f18b3d3fec954aa0c141c44e4e5cb4cf777b9eab274e",
        "prefix": "TST",
        "steem_symbol": "CORE",
        "sbd_symbol": "TEST",
        "vests_symbol": "CESTS",
    },
}
