#!/usr/bin/env python
"""Adds arbitrary data to the Bitcoin blockchain.

Connects to local daemon, adds custom OP_RETURN data,
creates, signs and broadcasts a raw transaction.
"""

import redis
import binascii
import logging
import pyqrcode
from decimal import *
from bitcoinrpc import connection
import credentials

__author__ = "Justin Smith"
__credits__ = ["Justin Smith"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Justin Smith"
__email__ = "js.06@icloud.com"
__status__ = "Draft"

#Logging system
logger = logging.getLogger('create_engine_js.py')
hdlr = logging.FileHandler('/Users/rusticbison/sandbox/blockchain_data/info.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG) #change to WARNING for production, to limit logging

#connect to local bitcoin server
rpcworker = connection.BitcoinConnection(credentials.rpcuser, credentials.rpcpassword, host='localhost', port=8332, use_https=False)

#select the very first unspent transaction available on local bitcoind client
first_unspent = rpcworker.listunspent()[0]

#collect the transaction id, number of outputs and amount available from the first unspent transaction
txid = first_unspent.txid
vout = first_unspent.vout
first_unspent_amount = Decimal(first_unspent.amount)

#gather fresh addresses for change and receiving in own wallet
raw_change_address = rpcworker.getrawchangeaddress()
new_bitcoin_address = rpcworker.getnewaddress()

#specify fee
fee = Decimal(0.000005) #fee of about $0.06 USD. Probably not enough, as it is taking forever to get this into the network.

#for some reason the RPC barfs if you try to send the full amount. Splitting the value sent seems to work ok.
send_amount = first_unspent_amount / 2
change_amount = (first_unspent_amount / 2) - fee

change_amount_string = "%.8f" % change_amount
send_amount_string = "%.8f" % send_amount

# Data to insert in OP_RETURN
data = "@rusticbison"
if len(data) > 75:
    raise Exception("Too much data, use OP_PUSHDATA1 instead")
hex_format_data = binascii.hexlify(data)

#use built-in function to create raw transaction, just add data field with op-return in it:
hexstring = rpcworker.createrawtransaction(
                [{"txid": txid, "vout": vout}], {"data": hex_format_data, new_bitcoin_address: send_amount_string, raw_change_address: change_amount_string})

#fire up the redis database, start storing some data
r = redis.StrictRedis()

#lazy way to get a uniuqe ID, then save it to the redis database alongside the transaction id and hex
unique_id = rpcworker.getnewaddress()
r.hmset(unique_id, {'transactionid': txid, 'transactionhexstring': hexstring})

# sign_raw_transaction = rpcworker.signrawtransaction(hexstring, {"txid": txid, "vout": vout})
# for review: sendrawtransaction "hexstring" ( allowhighfees )
try:
    sign_raw_transaction = rpcworker.signrawtransaction(hexstring, previous_transactions=None, private_keys=None)
except SomeError as err:
    logger.warn("signing error")
    raise DifferentError()

print("Success! Search this key via redis-cli and the hgetall command to find your transaction details:")
#this is important, if you lose this you have no way to look up transaction details.
print(unique_id)

#broadcast to network
try:
    send_raw_transaction = rpcworker.sendrawtransaction(sign_raw_transaction)
except Exception:
    logger.warn("Broadcast error, probably the fee threshold issue with the daemon.")
    print("Just one thing: it wasn't broadcasted. Use https://blockr.io/tx/push to broadcast until I fix the function.")
exit()
