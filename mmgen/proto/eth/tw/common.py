#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.eth.tw.common: Ethereum base protocol tracking wallet dependency classes
"""

from ....tw.ctl import TrackingWallet
from ....addr import CoinAddr
from ....tw.common import TwLabel

class EthereumTwCommon:

	async def get_addr_label_pairs(self,twmmid=None):
		wallet = (
			self if isinstance(self,TrackingWallet) else
			(self.wallet or await TrackingWallet(self.proto,mode='w'))
		)

		ret = [(
				TwLabel( self.proto, mmid + ' ' + d['comment'] ),
				CoinAddr( self.proto, d['addr'] )
			) for mmid,d in wallet.mmid_ordered_dict.items() ]

		if wallet is not self:
			del wallet

		if twmmid:
			ret = [e for e in ret if e[0].mmid == twmmid]

		return ret or None
