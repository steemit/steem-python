steempy - CLI Utility for STEEM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`steempy` lets you leverage your encrypted wallet to perform various actions on your accounts.

Examples
--------
Importing a private key into your wallet:

::

   steempy addkey <private_key>

Listing accounts:

::

   steempy listaccounts


Sending funds:

::

   steempy transfer --account <account_name> 100 STEEM <recipient_name> memo

Upvoting a post:

::

   steempy upvote --account <account_name> https://steemit.com/funny/@mynameisbrian/the-content-stand-a-comic

Help
----
You can see all available commands with ``steempy -h``

::

   % steempy -h
   usage: steempy [-h] [--node NODE] [--nobroadcast] [--nowallet] [--unsigned]
                  [--expires EXPIRES] [--verbose VERBOSE] [--version]
                  {set,config,info,changewalletpassphrase,addkey,delkey,getkey,listkeys,listaccounts,upvote,downvote,replies,transfer,powerup,powerdown,powerdownroute,convert,balance,history,interest,permissions,allow,disallow,newaccount,importaccount,updatememokey,approvewitness,disapprovewitness,sign,broadcast,orderbook,buy,sell,cancel,resteem,follow,unfollow,setprofile,delprofile,witnessupdate,witnesscreate}
                  ...

   Command line tool to interact with the Steem network

   positional arguments:
     {set,config,info,changewalletpassphrase,addkey,delkey,getkey,listkeys,listaccounts,upvote,downvote,replies,transfer,powerup,powerdown,powerdownroute,convert,balance,history,interest,permissions,allow,disallow,newaccount,importaccount,updatememokey,approvewitness,disapprovewitness,sign,broadcast,orderbook,buy,sell,cancel,resteem,follow,unfollow,setprofile,delprofile,witnessupdate,witnesscreate}
                           sub-command help
       set                 Set configuration
       config              Show local configuration
       info                Show infos about piston and Steem
       changewalletpassphrase
                           Change wallet password
       addkey              Add a new key to the wallet
       delkey              Delete keys from the wallet
       getkey              Dump the privatekey of a pubkey from the wallet
       listkeys            List available keys in your wallet
       listaccounts        List available accounts in your wallet
       upvote              Upvote a post
       downvote            Downvote a post
       replies             Show recent replies to your posts
       transfer            Transfer STEEM
       powerup             Power up (vest STEEM as STEEM POWER)
       powerdown           Power down (start withdrawing STEEM from piston POWER)
       powerdownroute      Setup a powerdown route
       convert             Convert STEEMDollars to Steem (takes a week to settle)
       balance             Show the balance of one more more accounts
       history             Show the history of an account
       interest            Get information about interest payment
       permissions         Show permissions of an account
       allow               Allow an account/key to interact with your account
       disallow            Remove allowance an account/key to interact with your
                           account
       newaccount          Create a new account
       importaccount       Import an account using a passphrase
       updatememokey       Update an account's memo key
       approvewitness      Approve a witnesses
       disapprovewitness   Disapprove a witnesses
       sign                Sign a provided transaction with available and
                           required keys
       broadcast           broadcast a signed transaction
       orderbook           Obtain orderbook of the internal market
       buy                 Buy STEEM or SBD from the internal market
       sell                Sell STEEM or SBD from the internal market
       cancel              Cancel order in the internal market
       resteem             Resteem an existing post
       follow              Follow another account
       unfollow            unfollow another account
       setprofile          Set a variable in an account's profile
       delprofile          Set a variable in an account's profile
       witnessupdate       Change witness properties
       witnesscreate       Create a witness

   optional arguments:
     -h, --help            show this help message and exit
     --node NODE           Websocket URL for public Steem API (default:
                           "wss://this.piston.rocks/")
     --nobroadcast, -d     Do not broadcast anything
     --nowallet, -p        Do not load the wallet
     --unsigned, -x        Do not try to sign the transaction
     --expires EXPIRES, -e EXPIRES
                           Expiration time in seconds (defaults to 30)
     --verbose VERBOSE, -v VERBOSE
                           Verbosity
     --version             show program's version number and exit
