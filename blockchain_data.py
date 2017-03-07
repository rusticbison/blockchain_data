#!/usr/bin/env python
"""Adds arbitrary data to the Bitcoin blockchain.

Connects to local daemon, pulls relevent data,
creates, signs and broadcasts a raw transaction.
"""

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
hdlr = logging.FileHandler('/Users/rusticbison/sandbox/blockchain_data_project/info.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG) #change to WARNING for production, to limit logging

#connect to local bitcoin server
rpcworker = connection.BitcoinConnection(credentials.rpcuser, credentials.rpcpassword, host='localhost', port=8332, use_https=False)

#select the very first unspent transaction available on local bitcoind client
first_unspent = rpcworker.listunspent()[0]

txid = first_unspent.txid
vout = first_unspent.vout
input_amount = first_unspent.amount

#set fee and precision, type decimal
fee_amount = Decimal("0.00002").quantize(Decimal("0.00000001"), rounding=ROUND_UP) #one satoshi for rounding

#calculate the amount to be sent to the raw change address, type decimal
# change_amount = input_amount - fee_amount


#some light error handling, in case there's not enough money available
# if change_amount <= 0:
#     logger.error('Insufficient funds. Change amount is %s' % change_amount)
#     print('Insufficient funds. Current balance is %s' % input_amount)
#     exit()

#cheater hard coded change address - add getrawchangeaddress to the library ASAP!
# change_address = rpcworker.getnewaddress()
raw_change_address = rpcworker.getrawchangeaddress()
new_bitcoin_address = rpcworker.getnewaddress()
primary_output_value = 0.0001
primary_change_value = round((primary_output_value - 0.00003),8)

# print(primary_change_value)
# exit()

# Data to insert
data = "@rusticbison"
if len(data) > 75:
    raise Exception("Too much data, use OP_PUSHDATA1 instead")
hex_format_data = binascii.hexlify(data)

#use built-in function to create raw transaction, just add data field with op-return in it:
hexstring = rpcworker.createrawtransaction(
                [{"txid": txid, "vout": vout}], {"data": hex_format_data, new_bitcoin_address: primary_output_value, raw_change_address: primary_change_value})
logger.info(hexstring)



# sign_raw_transaction = rpcworker.signrawtransaction(hexstring, {"txid": txid, "vout": vout})
sign_raw_transaction = rpcworker.signrawtransaction(hexstring, previous_transactions=None, private_keys=None)

logger.info(sign_raw_transaction)

#added getrawchangeaddress
#added sendrawtransaction

send_raw_transaction = rpcworker.sendrawtransaction(sign_raw_transaction)


#reference:

# > curl --user myusername --data-binary '{"jsonrpc": "1.0", "id":"curltest", "method": "createrawtransaction", "params": ["[{\"txid\":\"myid\",\"vout\":0}]",
#                 "{\"data\":\"00010203\"}"] }' -H 'content-type: text/plain;' http://127.0.0.1:8332/
#
#                 '[{"txid": txid,"vout":1,"scriptPubKey":"scriptPubKey"}]' '{"mtRWdkBpAyz8pUoCYobABvnEe1xFPqvkJN":0.36972432}'
#                 '[{"txid":"scriptPubKey","vout":1,"scriptPubKey":"scriptPubKey"}]' '{"receiveingaddress":0.1,"changeaddress":0.26972432}'


# external examples
# rawtxn = rpcworker.createrawtransaction(
#                 [{"txid": "a9d4599e15b53f3eb531608ddb31f48c695c3d0b3538a6bda871e8b34f2f430c",
#                   "vout": 0}],
#                 {"1B9nCoZxEdKspVJ3xxqUN97FtgqGzLY9Ba":50})
# print(rpcworker.getconnectioncount())
# print(rpcworker.getdifficulty())
# print(rpcworker.getinfo())
# print(rpcworker.getbalance())
# new_bitcoin_address = rpcworker.getnewaddress()
# new_qr_code = pyqrcode.create(new_bitcoin_address, version=5)

#To create an OP_RETURN transaction yourself, you may use this template:
#0100000001AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABB00000000ffffffff0100000000000000004e6a4cCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC00000000
#Replace AA...A with the input transaction hash flipped, BB with vout, CC...C with your payload/message.

# Go back to your debug console and type "decoderawtransaction XXX", whereby XXX is your modified transaction hex. If everything is fine, this should return some information about your transaction.
#
# You may adjust the payload length by changing the 4e and 4c. Use a calculator to convert the numbers.
#
# http://brainwallet.org/#converter has a hex to text and vice versa converter.
#
# When you are finished, type: "signrawtransaction XXX", whereby XXX is your transaction hex. It should show a longer hex followed by "complete".
#
# Copy that longer hash and type "sendrawtransaction YYY", whereby YYY is the signed transaction hex.
#
# Last note: make sure you use only an input with 0.0001-ish BTC. It will all be considered as miner fee unless you add more outputs.

exit()
