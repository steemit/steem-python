Examples
~~~~~~~~

Syncing Blockchain to a Flat File
=================================

Here is a relatively simple script built on top of ``steem-python`` that will let you sync
STEEM blockchain into a simple file.
You can run this script as many times as you like, and it will continue from the last block it synced.

    ::

        import json
        import os
        
        from steem.blockchain import Blockchain


        def get_last_line(filename):
            if os.path.isfile(filename):
                if os.stat(filename).st_size == 0:
                    fp = open(filename)
                    return fp.read()
                with open(filename, 'rb') as f:
                    f.seek(-2, 2)
                    while f.read(1) != b"\n":
                        f.seek(-2, 1)
                    return f.readline()


        def get_previous_block_num(block):
            if not block:
                return -1

            if type(block) == bytes:
                block = block.decode('utf-8')

            if type(block) == str:
                block = json.loads(block)

            return int(block['previous'][:8], base=16)


        def run(filename):
            b = Blockchain()
            # automatically resume from where we left off
            # previous + last + 1
            start_block = get_previous_block_num(get_last_line(filename)) + 2
            with open(filename, 'a+') as file:
                for block in b.stream_from(start_block=start_block, full_blocks=True):
                    file.write(json.dumps(block, sort_keys=True) + '\n')


        if __name__ == '__main__':
            output_file = '/home/user/Downloads/steem.blockchain.json'
            try:
                run(output_file)
            except KeyboardInterrupt:
                pass


To see how many blocks we currently have, we can simply perform a line count.

    ::


        wc -l steem.blockchain.json


We can also inspect an arbitrary block, and pretty-print it.
*Replace 10000 with desired block_number + 1.*

    ::

        sed '10000q;d' steem.blockchain.json | python -m json.tool



Witness Killswitch
==================

Occasionally things go wrong: software crashes, servers go down...
One of the main roles for STEEM witnesses is to reliably mint blocks.
This script acts as a kill-switch to protect the network from missed blocks and
prevents embarrassment when things go totally wrong.

    ::

        import time
        from steem import Steem

        steem = Steem()

        # variables
        disable_after = 10  # disable witness after 10 blocks are missed
        witness_name = 'furion'
        witness_url = "https://steemit.com/steemit/@furion/power-down-no-more"
        witness_props = {
            "account_creation_fee": "0.500 STEEM",
            "maximum_block_size": 65536,
            "sbd_interest_rate": 15,
        }


        def total_missed():
            return steem.get_witness_by_account(witness_name)['total_missed']


        if __name__ == '__main__':
            treshold = total_missed() + disable_after
            while True:
                if total_missed() > treshold:
                    tx = steem.commit.witness_update(
                        signing_key=None,
                        url=witness_url,
                        props=witness_props,
                        account=witness_name)

                    print("Witness %s Disabled!" % witness_name)
                    quit(0)

                time.sleep(60)

Batching Operations
===================

Most of the time each transaction contains only one operation (for example, an upvote, a transfer or a new post).
We can however cram multiple operations in a single transaction, to achieve better efficiency and size reduction.

This script will also teach us how to create and sign transactions ourselves.

    ::

        from steem.transactionbuilder import TransactionBuilder
        from steembase import operations

        # lets create 3 transfers, to 3 different people
        transfers = [
            {
                'from': 'richguy',
                'to': 'recipient1',
                'amount': '0.001 STEEM',
                'memo': 'Test Transfer 1'
            },
            {
                'from': 'richguy',
                'to': 'recipient2',
                'amount': '0.002 STEEM',
                'memo': 'Test Transfer 2'
            },
            {
                'from': 'richguy',
                'to': 'recipient3',
                'amount': '0.003 STEEM',
                'memo': 'Test Transfer 3'
            }

        ]

        # now we can construct the transaction
        # we will set no_broadcast to True because
        # we don't want to really send funds, just testing.
        tb = TransactionBuilder(no_broadcast=True)

        # lets serialize our transfers into a format Steem can understand
        operations = [operations.Transfer(**x) for x in transfers]

        # tell TransactionBuilder to use our serialized transfers
        tb.appendOps(operations)

        # we need to tell TransactionBuilder about
        # everyone who needs to sign the transaction.
        # since all payments are made from `richguy`,
        # we just need to do this once
        tb.appendSigner('richguy', 'active')

        # sign the transaction
        tb.sign()

        # broadcast the transaction (publish to steem)
        # since we specified no_broadcast=True earlier
        # this method won't actually do anything
        tx = tb.broadcast()

Simple Voting Bot
=================

Here is a simple bot that will reciprocate by upvoting all new posts that mention us.
Make sure to set ``whoami`` to your Steem username before running.

    ::

        from steem.blockchain import Blockchain
        from steem.post import Post


        def run():
            # upvote posts with 30% weight
            upvote_pct = 30
            whoami = 'my-steem-username'

            # stream comments as they are published on the blockchain
            # turn them into convenient Post objects while we're at it
            b = Blockchain()
            stream = map(Post, b.stream(filter_by=['comment']))

            for post in stream:
                if post.json_metadata:
                    mentions = post.json_metadata.get('users', [])

                    # if post mentions more than 10 people its likely spam
                    if mentions and len(mentions) < 10:
                        post.upvote(weight=upvote_pct, voter=whoami)

        if __name__ == '__main__':
            try:
                run()
            except KeyboardInterrupt:
                pass
