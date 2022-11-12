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
tw.txhistory: Tracking wallet transaction history class for the MMGen suite
"""

from collections import namedtuple

from ..util import fmt
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import CoinTxID,MMGenList,Int
from ..rpc import rpc_init
from .view import TwView

class TwTxHistory(TwView,metaclass=AsyncInit):

	class display_type(TwView.display_type):

		class squeezed(TwView.display_type.squeezed):
			cols = ('num','txid','date','inputs','amt','outputs','comment')

		class detail(TwView.display_type.detail):
			need_column_widths = False
			item_separator = '\n\n'

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,'tw','txhistory'))

	txid_w = 64
	show_txid = False
	show_unconfirmed = False
	show_total_amt = False
	update_widths_on_age_toggle = True
	print_output_types = ('squeezed','detail')
	filters = ('show_unconfirmed',)

	async def __init__(self,proto,sinceblock=0):
		self.proto        = proto
		self.rpc          = await rpc_init(proto)
		self.sinceblock   = Int( sinceblock if sinceblock >= 0 else self.rpc.blockcount + sinceblock )

	@property
	def no_rpcdata_errmsg(self):
		return 'No transaction history {}found!'.format(
			f'from block {self.sinceblock} ' if self.sinceblock else '')

	def filter_data(self):
		return (d for d in self.data if d.confirmations > 0 or self.show_unconfirmed)

	def get_column_widths(self,data,wide=False):

		# var cols: inputs outputs comment [txid]
		if not hasattr(self,'varcol_maxwidths'):
			self.varcol_maxwidths = {
				'inputs': max(len(d.vouts_disp('inputs',width=None,color=False)) for d in data),
				'outputs': max(len(d.vouts_disp('outputs',width=None,color=False)) for d in data),
				'comment': max(len(d.comment) for d in data),
			}

		maxws = self.varcol_maxwidths.copy()
		minws = {
			'inputs': 15,
			'outputs': 15,
			'comment': len('Comment'),
		}
		if self.show_txid:
			maxws['txid'] = self.txid_w
			minws['txid'] = 8
			maxws_nice = {'txid': 20}
		else:
			maxws['txid'] = 0
			minws['txid'] = 0
			maxws_nice = {}

		widths = { # fixed cols
			'num': max(2,len(str(len(data)))+1),
			'date': self.age_w,
			'amt': self.disp_prec + 5,
			'spc': 6 + self.show_txid, # 5(6) spaces between cols + 1 leading space in fs
		}

		return self.compute_column_widths(widths,maxws,minws,maxws_nice,wide=wide)

	def gen_squeezed_display(self,data,cw,hdr_fs,fs,color):

		if self.sinceblock:
			yield f'Displaying transactions since block {self.sinceblock.hl(color=color)}'
		yield 'Only wallet-related outputs are shown'
		yield 'Comment is from first wallet address in outputs or inputs'
		if (cw.inputs < self.varcol_maxwidths['inputs'] or
			cw.outputs < self.varcol_maxwidths['outputs'] ):
			yield 'Due to screen width limitations, not all addresses could be displayed'
		yield ''

		yield hdr_fs.format(
			n = '',
			t = 'TxID',
			d = self.age_hdr,
			i = 'Inputs',
			A = 'Amt({})'.format('TX' if self.show_total_amt else 'Wallet'),
			o = 'Outputs',
			c = 'Comment' ).rstrip()

		for n,d in enumerate(data,1):
			yield fs.format(
				n = str(n) + ')',
				t = d.txid_disp( width=cw.txid, color=color ) if hasattr(cw,'txid') else None,
				d = d.age_disp( self.age_fmt, width=self.age_w, color=color ),
				i = d.vouts_disp( 'inputs', width=cw.inputs, color=color ),
				A = d.amt_disp(self.show_total_amt).fmt( prec=self.disp_prec, color=color ),
				o = d.vouts_disp( 'outputs', width=cw.outputs, color=color ),
				c = d.comment.fmt( width=cw.comment, color=color, nullrepl='-' ) ).rstrip()

	def gen_detail_display(self,data,cw,hdr_fs,fs,color):

		if self.sinceblock:
			yield f'Displaying transactions since block {self.sinceblock.hl(color=color)}'
		yield 'Only wallet-related outputs are shown'

		fs = fmt("""
		{n}
		    Block:        [{d}] {b}
		    TxID:         [{D}] {t}
		    Value:        {A}
		    Wallet Value: {B}
		    Fee:          {f}
		    Inputs:
		        {i}
		    Outputs ({N}):
		        {o}
		""",strip_char='\t').strip()

		for n,d in enumerate(data,1):
			yield fs.format(
				n = str(n) + ')',
				d = d.age_disp( 'date_time', width=None, color=None ),
				b = d.blockheight_disp(color=color),
				D = d.txdate_disp( 'date_time' ),
				t = d.txid_disp( width=None, color=color ),
				A = d.amt_disp(True).hl( color=color ),
				B = d.amt_disp(False).hl( color=color ),
				f = d.fee_disp( color=color ),
				i = d.vouts_list_disp( 'inputs', color=color, indent=' '*8 ),
				N = d.nOutputs,
				o = d.vouts_list_disp( 'outputs', color=color, indent=' '*8 ),
			)

	sort_disp = {
		'age':         'Age',
		'blockheight': 'Block Height',
		'amt':         'Wallet Amt',
		'total_amt':   'TX Amt',
		'txid':        'TxID',
	}

	sort_funcs = {
		'age':         lambda i: i.time,
		'blockheight': lambda i: 0 - abs(i.confirmations), # old/altcoin daemons return no 'blockheight' field
		'amt':         lambda i: i.wallet_outputs_total,
		'total_amt':   lambda i: i.outputs_total,
		'txid':        lambda i: i.txid,
	}

	async def set_dates(self,foo):
		pass

	@property
	def dump_fn_pfx(self):
		return 'transaction-history' + (f'-since-block-{self.sinceblock}' if self.sinceblock else '')

	class action(TwView.action):

		def s_amt(self,parent):
			parent.do_sort('amt')
			parent.show_total_amt = False

		def s_total_amt(self,parent):
			parent.do_sort('total_amt')
			parent.show_total_amt = True

		def d_show_txid(self,parent):
			parent.show_txid = not parent.show_txid

		def d_show_unconfirmed(self,parent):
			parent.show_unconfirmed = not parent.show_unconfirmed

		def d_show_total_amt(self,parent):
			parent.show_total_amt = not parent.show_total_amt
