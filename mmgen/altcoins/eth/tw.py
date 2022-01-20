#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
altcoins.eth.tw: Ethereum tracking wallet dependency classes for the MMGen suite
"""

from mmgen.addrdata import AddrData,TwAddrData

class EthereumTwAddrData(TwAddrData):

	async def get_tw_data(self,wallet=None):
		from mmgen.twctl import TrackingWallet
		from mmgen.util import vmsg
		vmsg('Getting address data from tracking wallet')
		tw = (wallet or await TrackingWallet(self.proto)).mmid_ordered_dict
		# emulate the output of RPC 'listaccounts' and 'getaddressesbyaccount'
		return [(mmid+' '+d['comment'],[d['addr']]) for mmid,d in list(tw.items())]

class EthereumTokenTwAddrData(EthereumTwAddrData): pass

class EthereumAddrData(AddrData): pass
class EthereumTokenAddrData(EthereumAddrData): pass
