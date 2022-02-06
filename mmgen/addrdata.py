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
addrdata.py: MMGen AddrData and related classes
"""

from .util import vmsg,base_proto_subclass,fmt,die
from .base_obj import AsyncInit
from .obj import MMGenObject,MMGenDict,get_obj
from .addr import MMGenID,AddrListID
from .addrlist import AddrListEntry,AddrListData,AddrList

class AddrData(MMGenObject):

	def __init__(self,proto,*args,**kwargs):
		self.al_ids = {}
		self.proto = proto
		self.rpc = None

	def seed_ids(self):
		return list(self.al_ids.keys())

	def addrlist(self,al_id):
		# TODO: Validate al_id
		if al_id in self.al_ids:
			return self.al_ids[al_id]

	def mmaddr2coinaddr(self,mmaddr):
		al_id,idx = MMGenID(self.proto,mmaddr).rsplit(':',1)
		coinaddr = ''
		if al_id in self.al_ids:
			coinaddr = self.addrlist(al_id).coinaddr(int(idx))
		return coinaddr or None

	def coinaddr2mmaddr(self,coinaddr):
		d = self.make_reverse_dict([coinaddr])
		return (list(d.values())[0][0]) if d else None

	def add(self,addrlist):
		from .addrlist import AddrList
		if type(addrlist) == AddrList:
			self.al_ids[addrlist.al_id] = addrlist
			return True
		else:
			raise TypeError(f'Error: object {addrlist!r} is not of type AddrList')

	def make_reverse_dict(self,coinaddrs):
		d = MMGenDict()
		for al_id in self.al_ids:
			d.update(self.al_ids[al_id].make_reverse_dict_addrlist(coinaddrs))
		return d

class TwAddrData(AddrData,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(base_proto_subclass(cls,proto,'tw'))

	async def __init__(self,proto,wallet=None):
		from .rpc import rpc_init
		from .tw import TwLabel
		from .globalvars import g
		from .seed import SeedID
		self.proto = proto
		self.rpc = await rpc_init(proto)
		self.al_ids = {}
		twd = await self.get_tw_data(wallet)
		out,i = {},0
		for acct,addr_array in twd:
			l = get_obj(TwLabel,proto=self.proto,text=acct,silent=True)
			if l and l.mmid.type == 'mmgen':
				obj = l.mmid.obj
				if len(addr_array) != 1:
					message = self.msgs['multiple_acct_addrs'].strip().format( acct=acct, proj=g.proj_name )
					die(3, fmt( message, indent='  ' ))
				al_id = AddrListID(SeedID(sid=obj.sid),self.proto.addr_type(obj.mmtype))
				if al_id not in out:
					out[al_id] = []
				out[al_id].append(AddrListEntry(self.proto,idx=obj.idx,addr=addr_array[0],label=l.comment))
				i += 1

		vmsg(f'{i} {g.prog_name} addresses found, {len(twd)} accounts total')

		for al_id in out:
			self.add(AddrList(self.proto,al_id=al_id,adata=AddrListData(sorted(out[al_id],key=lambda a: a.idx))))
