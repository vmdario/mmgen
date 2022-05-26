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
ts_regtest.py: Regtest tests for the test.py test suite
"""

import os,json
from decimal import Decimal
from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import die,gmsg
from mmgen.protocol import init_proto
from mmgen.addrlist import AddrList
from mmgen.wallet import Wallet,get_wallet_cls
from ..include.common import *
from .common import *

pat_date = r'\b\d\d-\d\d-\d\d\b'
pat_date_time = r'\b\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d\b'

dfl_wcls = get_wallet_cls('mmgen')

rt_pw = 'abc-α'
rt_data = {
	'tx_fee': {'btc':'0.0001','bch':'0.001','ltc':'0.01'},
	'rtFundAmt': {'btc':'500','bch':'500','ltc':'5500'},
	'rtFee': {
		'btc': ('20s','10s','60s','31s','10s','20s'),
		'bch': ('20s','10s','60s','0.0001','10s','20s'),
		'ltc': ('1000s','500s','1500s','0.05','400s','1000s')
	},
	'rtBals': {
		'btc': ('499.9999488','399.9998282','399.9998147','399.9996877',
				'52.99980410','946.99933647','999.99914057','52.9999',
				'946.99933647','0.4169328','6.24987417'),
		'bch': ('499.9999484','399.9999194','399.9998972','399.9997692',
				'46.78890380','953.20966920','999.99857300','46.789',
				'953.2096692','0.4169328','39.58187387'),
		'ltc': ('5499.99744','5399.994425','5399.993885','5399.987535',
				'52.98520500','10946.93753500','10999.92274000','52.99',
				'10946.937535','0.41364','6.24846787'),
	},
	'rtBals_gb': {
		'btc': {
			'0conf0': {
				'mmgen': ('283.22339537','0','283.22339537'),
				'nonmm': ('16.77647763','0','116.77629233'),
				'total': ('299.999873','0','399.9996877'),
			},
			'0conf1': {
				'mmgen': ('283.22339537','283.22339537','0'),
				'nonmm': ('16.77647763','16.77647763','99.9998147'),
				'total': ('299.999873','299.999873','99.9998147'),
			},
			'1conf1': {
				'mmgen': ('0','0','283.22339537'),
				'nonmm': ('0','0','116.77629233'),
				'total': ('0','0','399.9996877'),
			},
			'1conf2': {
				'mmgen': ('0','283.22339537','0'),
				'nonmm': ('0','16.77647763','99.9998147'),
				'total': ('0','299.999873','99.9998147'),
			},
		},
		'bch': {
			'0conf0': {
				'mmgen': ('283.22339437','0','283.22339437'),
				'nonmm': ('16.77647763','0','116.77637483'),
				'total': ('299.999872','0','399.9997692'),
			},
			'0conf1': {
				'mmgen': ('283.22339437','283.22339437','0'),
				'nonmm': ('16.77647763','16.77647763','99.9998972'),
				'total': ('299.999872','299.999872','99.9998972'),
			},
			'1conf1': {
				'mmgen': ('0','0','283.22339437'),
				'nonmm': ('0','0','116.77637483'),
				'total': ('0','0','399.9997692'),
			},
			'1conf2': {
				'mmgen': ('0','283.22339437','0'),
				'nonmm': ('0','16.77647763','99.9998972'),
				'total': ('0','299.999872','99.9998972'),
			},
		},
		'ltc': {
			'0conf0': {
				'mmgen': ('283.21717237','0','283.21717237'),
				'nonmm': ('16.77647763','0','5116.77036263'),
				'total': ('299.99365','0','5399.987535'),
			},
			'0conf1': {
				'mmgen': ('283.21717237','283.21717237','0'),
				'nonmm': ('16.77647763','16.77647763','5099.993885'),
				'total': ('299.99365','299.99365','5099.993885'),
			},
			'1conf1': {
				'mmgen': ('0','0','283.21717237'),
				'nonmm': ('0','0','5116.77036263'),
				'total': ('0','0','5399.987535'),
			},
			'1conf2': {
				'mmgen': ('0','283.21717237','0'),
				'nonmm': ('0','16.77647763','5099.993885'),
				'total': ('0','299.99365','5099.993885'),
			},
		}
	},
	'rtBobOp3': {'btc':'S:2','bch':'L:3','ltc':'S:2'},
	'rtAmts': {
		'btc': ('500','500'),
		'bch': ('500','560'),
		'ltc': ('5500','5500')
	}
}

def make_burn_addr(proto):
	from mmgen.tool.coin import tool_cmd
	return tool_cmd(
		cmdname = 'pubhash2addr',
		proto   = proto,
		mmtype  = 'compressed' ).pubhash2addr('00'*20)

from .ts_base import *
from .ts_shared import *

class TestSuiteRegtest(TestSuiteBase,TestSuiteShared):
	'transacting and tracking wallet operations via regtest mode'
	networks = ('btc','ltc','bch')
	passthru_opts = ('coin',)
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [17]
	color = True
	deterministic = False
	test_rbf = False
	cmd_group = (
		('setup',                    'regtest (Bob and Alice) mode setup'),
		('daemon_version',           'mmgen-tool daemon_version'),
		('halving_calculator_bob',   'halving calculator (Bob)'),
		('walletgen_bob',            'wallet generation (Bob)'),
		('walletgen_alice',          'wallet generation (Alice)'),
		('addrgen_bob',              'address generation (Bob)'),
		('addrgen_alice',            'address generation (Alice)'),
		('addrimport_bob',           "importing Bob's addresses"),
		('addrimport_alice',         "importing Alice's addresses"),
		('bob_import_miner_addr',    "importing miner’s coinbase addr into Bob’s wallet"),
		('fund_bob_deterministic',   "funding Bob’s first MMGen address (deterministic method)"),
		('fund_alice_deterministic', "funding Alice’s first MMGen address (deterministic method)"),
		('bob_recreate_tracking_wallet','creation of new tracking wallet (Bob)'),
		('addrimport_bob2',          "reimporting Bob's addresses"),
		('fund_bob',                 "funding Bob's wallet"),
		('fund_alice',               "funding Alice's wallet"),
		('generate',                 'mining a block'),
		('bob_bal1',                 "Bob's balance"),
		('bob_add_label',            "adding an 80-screen-width label (lat+cyr+gr)"),
		('bob_twview1',              "viewing Bob's tracking wallet"),
		('bob_split1',               "splitting Bob's funds"),
		('generate',                 'mining a block'),
		('bob_bal2',                 "Bob's balance"),
		('bob_rbf_1output_create',   'creating RBF tx with one output'),
		('bob_rbf_1output_bump',     'bumping RBF tx with one output'),
		('bob_bal2a',                "Bob's balance (age_fmt=confs)"),
		('bob_bal2b',                "Bob's balance (showempty=1)"),
		('bob_bal2c',                "Bob's balance (showempty=1 minconf=2 age_fmt=days)"),
		('bob_bal2d',                "Bob's balance (minconf=2)"),
		('bob_bal2e',                "Bob's balance (showempty=1 sort=age)"),
		('bob_bal2f',                "Bob's balance (showempty=1 sort=age,reverse)"),
		('bob_send_maybe_rbf',       'sending funds to Alice (RBF, if supported)'),
		('get_mempool1',             'mempool (before RBF bump)'),
		('bob_rbf_status1',          'getting status of transaction'),
		('bob_rbf_bump',             'bumping RBF transaction'),
		('get_mempool2',             'mempool (after RBF bump)'),
		('bob_rbf_status2',          'getting status of transaction after replacement'),
		('bob_rbf_status3',          'getting status of replacement transaction (mempool)'),
		('generate',                 'mining a block'),
		('bob_rbf_status4',          'getting status of transaction after confirmed (1) replacement'),
		('bob_rbf_status5',          'getting status of replacement transaction (confirmed)'),
		('generate',                 'mining a block'),
		('bob_rbf_status6',          'getting status of transaction after confirmed (2) replacement'),
		('bob_bal3',                 "Bob's balance"),
		('bob_pre_import',           'sending to non-imported address'),
		('generate',                 'mining a block'),
		('bob_import_addr',          'importing non-MMGen address'),
		('bob_bal4',                 "Bob's balance (after import)"),
		('bob_import_list',          'importing flat address list'),
		('bob_import_list_rescan',   'importing flat address list with --rescan'),
		('bob_resolve_addr',         'resolving an address in the tracking wallet'),
		('bob_rescan_blockchain_all','rescanning the blockchain (full rescan)'),
		('bob_rescan_blockchain_gb', 'rescanning the blockchain (Genesis block)'),
		('bob_rescan_blockchain_one','rescanning the blockchain (single block)'),
		('bob_rescan_blockchain_ss', 'rescanning the blockchain (range of blocks)'),
		('bob_split2',               "splitting Bob's funds"),
		('bob_0conf0_getbalance',    "Bob's balance (unconfirmed, minconf=0)"),
		('bob_0conf1_getbalance',    "Bob's balance (unconfirmed, minconf=1)"),
		('generate',                 'mining a block'),
		('bob_1conf1_getbalance',    "Bob's balance (confirmed, minconf=1)"),
		('bob_1conf2_getbalance',    "Bob's balance (confirmed, minconf=2)"),
		('bob_bal5',                 "Bob's balance"),
		('bob_send_non_mmgen',       'sending funds to Alice (from non-MMGen addrs)'),
		('generate',                 'mining a block'),
		('alice_send_estimatefee',   'tx creation with no fee on command line'),
		('generate',                 'mining a block'),
		('bob_bal6',                 "Bob's balance"),

		('bob_subwallet_addrgen1',     "generating Bob's addrs from subwallet 29L"),
		('bob_subwallet_addrgen2',     "generating Bob's addrs from subwallet 127S"),
		('bob_subwallet_addrimport1',  "importing Bob's addrs from subwallet 29L"),
		('bob_subwallet_addrimport2',  "importing Bob's addrs from subwallet 127S"),
		('bob_subwallet_fund',         "funding Bob's subwallet addrs"),
		('generate',                   'mining a block'),
		('bob_twview2',                "viewing Bob's tracking wallet"),
		('bob_twview3',                "viewing Bob's tracking wallet"),
		('bob_subwallet_txcreate',     'creating a transaction with subwallet inputs'),
		('bob_subwallet_txsign',       'signing a transaction with subwallet inputs'),
		('bob_subwallet_txdo',         "sending from Bob's subwallet addrs"),
		('generate',                   'mining a block'),
		('bob_twview4',                "viewing Bob's tracking wallet"),

		('bob_alice_bal',            "Bob and Alice's balances"),

		('bob_nochg_burn',           'zero-change transaction to burn address'),
		('generate',                 'mining a block'),

		('bob_txhist1',              "viewing Bob's transaction history (sort=age)"),
		('bob_txhist2',              "viewing Bob's transaction history (sort=blockheight reverse=1)"),
		('bob_txhist3',              "viewing Bob's transaction history (sort=blockheight sinceblock=-7)"),
		('bob_txhist4',              "viewing Bob's transaction history (sinceblock=399 detail=1)"),
		('bob_txhist_interactive',   "viewing Bob's transaction history (age_fmt=date_time interactive=true)"),

		('alice_bal2',               "Alice's balance"),

		('alice_add_label1',         'adding a label'),
		('alice_chk_label1',         'the label'),
		('alice_add_label2',         'adding a label'),
		('alice_chk_label2',         'the label'),
		('alice_edit_label1',        'editing a label (zh)'),
		('alice_edit_label2',        'editing a label (lat+cyr+gr)'),
		('alice_chk_label3',         'the label'),
		('alice_remove_label1',      'removing a label'),
		('alice_chk_label4',         'the label'),
		('alice_add_label_coinaddr', 'adding a label using the coin address'),
		('alice_chk_label_coinaddr', 'the label'),
		('alice_add_label_badaddr1', 'adding a label with invalid address'),
		('alice_add_label_badaddr2', 'adding a label with invalid address for this chain'),
		('alice_add_label_badaddr3', 'adding a label with wrong MMGen address'),
		('alice_add_label_badaddr4', 'adding a label with wrong coin address'),
		('alice_listaddresses1',                'listaddresses'),
		('alice_listaddresses_days',            'listaddresses (age_fmt=days)'),
		('alice_listaddresses_date',            'listaddresses (age_fmt=date)'),
		('alice_listaddresses_date_time',       'listaddresses (age_fmt=date_time)'),
		('alice_twview1',                'twview'),
		('alice_twview_days',            'twview (age_fmt=days)'),
		('alice_twview_date',            'twview (age_fmt=date)'),
		('alice_twview_date_time',       'twview (age_fmt=date_time)'),
		('alice_txcreate_info',          'txcreate -i'),

		('bob_msgcreate',          'creating a message file for signing'),
		('bob_msgsign',            'signing the message file (default wallet)'),
		('bob_walletconv_words',   'creating an MMGen mnemonic wallet'),
		('bob_subwalletgen_bip39', 'creating a BIP39 mnemonic subwallet'),
		('bob_msgsign_userwallet',  'signing the message file (user-specified wallet)'),
		('bob_msgsign_userwallets', 'signing the message file (user-specified wallets)'),
		('bob_msgverify',           'verifying the message file (all addresses)'),
		('bob_msgverify_raw',       'verifying the raw message file (all addresses)'),
		('bob_msgverify_single',    'verifying the message file (single address)'),
		('bob_msgexport_single',    'exporting the message file (single address)'),
		('bob_msgexport',           'exporting the message file (all addresses)'),
		('bob_msgverify_export',    'verifying the exported JSON data (all addresses)'),
		('bob_msgverify_export_single','verifying the exported JSON data (single address)'),

		('stop',                 'stopping regtest daemon'),
	)

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return
		if self.proto.testnet:
			die(2,'--testnet and --regtest options incompatible with regtest test suite')
		self.proto = init_proto(self.proto.coin,network='regtest',need_amt=True)
		coin = self.proto.coin.lower()

		import test.test_py_d.ts_regtest as rt_mod
		for k in rt_data:
			setattr( rt_mod, k, rt_data[k][coin] if coin in rt_data[k] else None )

		if self.proto.coin == 'BTC':
			self.test_rbf = True # tests are non-coin-dependent, so run just once for BTC
			if g.test_suite_deterministic:
				self.deterministic = True
				self.miner_addr = 'bcrt1qaq8t3pakcftpk095tnqfv5cmmczysls024atnd' # regtest.create_hdseed()
				self.miner_wif = 'cTyMdQ2BgfAsjopRVZrj7AoEGp97pKfrC2NkqLuwHr4KHfPNAKwp'

		os.environ['MMGEN_BOGUS_SEND'] = ''
		os.environ['MMGEN_TEST_SUITE_REGTEST'] = '1'
		self.write_to_tmpfile('wallet_password',rt_pw)

		self.dfl_mmtype = 'C' if self.proto.coin == 'BCH' else 'B'

	def __del__(self):
		os.environ['MMGEN_BOGUS_SEND'] = '1'
		os.environ['MMGEN_TEST_SUITE_REGTEST'] = ''

	def _add_comments_to_addr_file(self,addrfile,outfile,use_labels=False):
		silence()
		gmsg(f'Adding comments to address file {addrfile!r}')
		a = AddrList(self.proto,addrfile)
		for n,idx in enumerate(a.idxs(),1):
			if use_labels:
				a.set_comment(idx,get_label())
			else:
				if n % 2: a.set_comment(idx,f'Test address {n}')
		af = a.get_file()
		af.format(add_comments=True)
		from mmgen.fileutil import write_data_to_file
		write_data_to_file(outfile,af.fmt_data,quiet=True,ignore_opt_outdir=True)
		end_silence()

	def setup(self):
		stop_test_daemons(self.proto.network_id,force=True,remove_datadir=True)
		try: shutil.rmtree(joinpath(self.tr.data_dir,'regtest'))
		except: pass
		t = self.spawn('mmgen-regtest',['-n','setup'])
		for s in ('Starting','Creating','Creating','Creating','Mined','Setup complete'):
			t.expect(s)
		return t

	def daemon_version(self):
		t = self.spawn('mmgen-tool', ['--bob','daemon_version'])
		t.expect('version')
		return t

	def halving_calculator_bob(self):
		t = self.spawn('halving-calculator.py',['--bob'],cmd_dir='examples')
		t.expect('time until halving')
		return t

	def walletgen(self,user):
		t = self.spawn('mmgen-walletgen',['-q','-r0','-p1','--'+user])
		t.passphrase_new('new '+dfl_wcls.desc,rt_pw)
		t.label()
		t.expect('move it to the data directory? (Y/n): ','y')
		t.written_to_file(capfirst(dfl_wcls.desc))
		return t

	def walletgen_bob(self):   return self.walletgen('bob')
	def walletgen_alice(self): return self.walletgen('alice')

	def _user_dir(self,user,coin=None):
		return joinpath(self.tr.data_dir,'regtest',coin or self.proto.coin.lower(),user)

	def _user_sid(self,user):
		return os.path.basename(get_file_with_ext(self._user_dir(user),'mmdat'))[:8]

	def _get_user_subsid(self,user,subseed_idx):
		fn = get_file_with_ext(self._user_dir(user),dfl_wcls.ext)
		silence()
		w = Wallet( fn=fn, passwd_file=os.path.join(self.tmpdir,'wallet_password') )
		end_silence()
		return w.seed.subseed(subseed_idx).sid

	def addrgen(self,user,wf=None,addr_range='1-5',subseed_idx=None,mmtypes=[]):
		from mmgen.addr import MMGenAddrType
		for mmtype in mmtypes or self.proto.mmtypes:
			t = self.spawn('mmgen-addrgen',
				['--quiet','--'+user,'--type='+mmtype,f'--outdir={self._user_dir(user)}'] +
				([wf] if wf else []) +
				(['--subwallet='+subseed_idx] if subseed_idx else []) +
				[addr_range],
				extra_desc='({})'.format( MMGenAddrType.mmtypes[mmtype].name ))
			t.passphrase(dfl_wcls.desc,rt_pw)
			t.written_to_file('Addresses')
			ok_msg()
		t.skip_ok = True
		return t

	def addrgen_bob(self):   return self.addrgen('bob')
	def addrgen_alice(self): return self.addrgen('alice')

	def addrimport(self,user,sid=None,addr_range='1-5',num_addrs=5,mmtypes=[]):
		id_strs = { 'legacy':'', 'compressed':'-C', 'segwit':'-S', 'bech32':'-B' }
		if not sid: sid = self._user_sid(user)
		from mmgen.addr import MMGenAddrType
		for mmtype in mmtypes or self.proto.mmtypes:
			desc = MMGenAddrType.mmtypes[mmtype].name
			addrfile = joinpath(self._user_dir(user),
				'{}{}{}[{}]{x}.regtest.addrs'.format(
					sid,self.altcoin_pfx,id_strs[desc],addr_range,
					x='-α' if g.debug_utf8 else ''))
			if mmtype == self.proto.mmtypes[0] and user == 'bob':
				self._add_comments_to_addr_file(addrfile,addrfile,use_labels=True)
			t = self.spawn(
				'mmgen-addrimport',
				['--quiet', '--'+user, '--batch', addrfile],
				extra_desc=f'({desc})' )
			if g.debug:
				t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
			t.expect('Importing')
			t.expect(f'{num_addrs} addresses imported')
			ok_msg()

		t.skip_ok = True
		return t

	def addrimport_bob(self):   return self.addrimport('bob')
	def addrimport_alice(self): return self.addrimport('alice')

	def bob_import_miner_addr(self):
		if not self.deterministic:
			return 'skip'
		return self.spawn(
			'mmgen-addrimport',
			[ '--bob', '--rescan', '--quiet', f'--address={self.miner_addr}' ] )

	def fund_wallet_deterministic(self,user,addr,utxo_nums,skip_passphrase=False):
		"""
		the deterministic funding method using specific inputs
		"""
		if not self.deterministic:
			return 'skip'
		self.write_to_tmpfile('miner.key',f'{self.miner_wif}\n')
		keyfile = joinpath(self.tmpdir,'miner.key')

		return self.user_txdo(
			'bob', '40s',
			[ f'{addr},{rtFundAmt}', make_burn_addr(self.proto) ],
			utxo_nums,
			extra_args = [f'--keys-from-file={keyfile}'],
			skip_passphrase = skip_passphrase )

	def fund_bob_deterministic(self):
		return self.fund_wallet_deterministic( 'bob', f'{self._user_sid("bob")}:C:1', '1-11' )

	def fund_alice_deterministic(self):
		sid = self._user_sid('alice')
		mmtype = ('L','S')[self.proto.cap('segwit')]
		addr = self.get_addr_from_addrlist('alice',sid,mmtype,0,addr_range='1-5')
		return self.fund_wallet_deterministic( 'alice', addr, '1-11', skip_passphrase=True )

	async def bob_recreate_tracking_wallet(self):
		if not self.deterministic:
			return 'skip'
		self.spawn('',msg_only=True)
		from mmgen.base_proto.bitcoin.regtest import MMGenRegtest
		rt = MMGenRegtest(self.proto.coin)
		await rt.stop()
		from shutil import rmtree
		imsg(f'Deleting Bob’s old tracking wallet')
		rmtree(os.path.join(rt.d.datadir,'regtest','wallets','bob'),ignore_errors=True)
		rt.init_daemon()
		rt.d.start(silent=True)
		imsg(f'Creating Bob’s new tracking wallet')
		await rt.rpc_call('createwallet','bob',True,True,None,False,False,False)
		await rt.stop()
		await rt.start()
		return 'ok'

	def addrimport_bob2(self):
		if not self.deterministic:
			return 'skip'
		return self.addrimport('bob')

	def fund_wallet(self,user,mmtype,amt,sid=None,addr_range='1-5'):
		if self.deterministic:
			return 'skip'
		if not sid:
			sid = self._user_sid(user)
		addr = self.get_addr_from_addrlist(user,sid,mmtype,0,addr_range=addr_range)
		t = self.spawn('mmgen-regtest', ['send',str(addr),str(amt)])
		t.expect(f'Sending {amt} miner {self.proto.coin}')
		t.expect('Mined 1 block')
		return t

	def fund_bob(self):
		return self.fund_wallet('bob','C',rtFundAmt)

	def fund_alice(self):
		return self.fund_wallet('alice',('L','S')[self.proto.cap('segwit')],rtFundAmt)

	def user_twview(self,user,chk,sort='age'):
		t = self.spawn('mmgen-tool',['--'+user,'twview','sort='+sort])
		if chk:
			t.expect(r'{}\b.*\D{}\b'.format(*chk),regex=True)
		return t

	def bob_twview1(self): return self.user_twview('bob', chk = ('1',rtAmts[0]) )

	def user_bal(self,user,bal,args=['showempty=1'],skip_check=False):
		t = self.spawn('mmgen-tool',['--'+user,'listaddresses'] + args)
		if not skip_check:
			cmp_or_die(f'{bal} {self.proto.coin}',strip_ansi_escapes(t.expect_getend('TOTAL: ')))
		return t

	def alice_bal1(self):
		return self.user_bal('alice',rtFundAmt)

	def alice_bal2(self):
		return self.user_bal('alice',rtBals[8])

	def bob_bal1(self):
		return self.user_bal('bob',rtFundAmt)

	def bob_bal2(self):
		return self.user_bal('bob',rtBals[0])

	def bob_bal2a(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','age_fmt=confs'])

	def bob_bal2b(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1'])

	def bob_bal2c(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','minconf=2','age_fmt=days'],skip_check=True)

	def bob_bal2d(self):
		return self.user_bal('bob',rtBals[0],args=['minconf=2'],skip_check=True)

	def bob_bal2e(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','sort=age'])

	def bob_bal2f(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','sort=age,reverse'])

	def bob_bal3(self):
		return self.user_bal('bob',rtBals[1])

	def bob_bal4(self):
		return self.user_bal('bob',rtBals[2])

	def bob_bal5(self):
		return self.user_bal('bob',rtBals[3])

	def bob_bal6(self):
		return self.user_bal('bob',rtBals[7])

	def bob_subwallet_addrgen1(self):
		return self.addrgen('bob',subseed_idx='29L',mmtypes=['C'])  # 29L: 2FA7BBA8

	def bob_subwallet_addrgen2(self):
		return self.addrgen('bob',subseed_idx='127S',mmtypes=['C']) # 127S: '09E8E286'

	def subwallet_addrimport(self,user,subseed_idx):
		sid = self._get_user_subsid(user,subseed_idx)
		return self.addrimport(user,sid=sid,mmtypes=['C'])

	def bob_subwallet_addrimport1(self): return self.subwallet_addrimport('bob','29L')
	def bob_subwallet_addrimport2(self): return self.subwallet_addrimport('bob','127S')

	def bob_subwallet_fund(self):
		sid1 = self._get_user_subsid('bob','29L')
		sid2 = self._get_user_subsid('bob','127S')
		chg_addr = self._user_sid('bob') + (':B:1',':L:1')[self.proto.coin=='BCH']
		outputs_cl = [sid1+':C:2,0.29',sid2+':C:3,0.127',chg_addr]
		inputs = ('3','1')[self.proto.coin=='BCH']
		return self.user_txdo('bob',rtFee[1],outputs_cl,inputs,extra_args=['--subseeds=127'])

	def bob_twview2(self):
		sid1 = self._get_user_subsid('bob','29L')
		return self.user_twview('bob',chk=(sid1+':C:2','0.29'),sort='twmmid')

	def bob_twview3(self):
		sid2 = self._get_user_subsid('bob','127S')
		return self.user_twview('bob',chk=(sid2+':C:3','0.127'),sort='amt')

	def bob_subwallet_txcreate(self):
		sid1 = self._get_user_subsid('bob','29L')
		sid2 = self._get_user_subsid('bob','127S')
		outputs_cl = [sid1+':C:5,0.0159',sid2+':C:5']
		t = self.spawn('mmgen-txcreate',['-d',self.tmpdir,'-B','--bob'] + outputs_cl)
		return self.txcreate_ui_common(t,
			menu            = ['a'],
			inputs          = ('1,2','2,3')[self.proto.coin=='BCH'],
			interactive_fee = '0.00001')

	def bob_subwallet_txsign(self):
		fn = get_file_with_ext(self.tmpdir,'rawtx')
		t = self.spawn('mmgen-txsign',['-d',self.tmpdir,'--bob','--subseeds=127',fn])
		t.view_tx('t')
		t.passphrase(dfl_wcls.desc,rt_pw)
		t.do_comment(None)
		t.expect('(Y/n): ','y')
		t.written_to_file('Signed transaction')
		return t

	def bob_subwallet_txdo(self):
		outputs_cl = [self._user_sid('bob')+':L:5']
		inputs = ('1,2','2,3')[self.proto.coin=='BCH']
		return self.user_txdo('bob',rtFee[5],outputs_cl,inputs,menu=['a'],extra_args=['--subseeds=127']) # sort: amt

	def bob_twview4(self):
		sid = self._user_sid('bob')
		return self.user_twview('bob',chk=(sid+':L:5',rtBals[9]),sort='twmmid')

	def user_txhist(self,user,args,expect):
		t = self.spawn('mmgen-tool',['--'+user,'txhist'] + args)
		res = strip_ansi_escapes(t.read()).replace('\r','')
		m = re.search(expect,res,re.DOTALL)
		assert m, m
		return t

	def bob_txhist1(self):
		return self.user_txhist('bob',
			args = ['sort=age'],
			expect = fr'\s1\).*\s{rtFundAmt}\s' )

	def bob_txhist2(self):
		return self.user_txhist('bob',
			args = ['sort=blockheight','reverse=1','age_fmt=block'],
			expect = fr'\s1\).*:{self.dfl_mmtype}:1\s' )

	def bob_txhist3(self):
		return self.user_txhist('bob',
			args = ['sort=blockheight','sinceblock=-7','age_fmt=block'],
			expect = fr'Displaying transactions since block 399.*\s6\).*:C:2\s.*\s{rtBals[9]}\s.*:L:5.*\s7\)'
		)

	def bob_txhist4(self):
		return self.user_txhist('bob',
			args = ['sort=blockheight','sinceblock=399','age_fmt=block','detail=1'],
			expect = fr'Displaying transactions since block 399.*\s7\).*Block:.*406.*Value:.*{rtBals[10]}'
		)

	def bob_txhist_interactive(self):
		self.get_file_with_ext('out',delete_all=True)
		t = self.spawn('mmgen-tool',
			['--bob',f'--outdir={self.tmpdir}','txhist','age_fmt=date_time','interactive=true'] )
		for resp in ('u','i','t','a','m','T','A','r','r','D','D','D','D','p','P','b','V'):
			t.expect('draw:\b',resp,regex=True)
		txnum,idx = (8,1) if self.proto.coin == 'BCH' else (9,3)
		t.expect(f'\s{txnum}\).*Inputs:.*:L:{idx}.*Outputs \(3\):.*:C:2.*\s10\)','q',regex=True)
		return t

	def bob_getbalance(self,bals,confs=1):
		for i in (0,1,2):
			assert Decimal(bals['mmgen'][i]) + Decimal(bals['nonmm'][i]) == Decimal(bals['total'][i])
		t = self.spawn('mmgen-tool',['--bob','getbalance',f'minconf={confs}'])
		t.expect('Wallet')
		for k in ('mmgen','nonmm','total'):
			ret = strip_ansi_escapes(t.expect_getend(r'\S+: ',regex=True))
			cmp_or_die(
				' '.join(bals[k]),
				re.sub(rf'\s+{self.proto.coin}\s*',' ',ret).strip(),
				desc=k,
			)
		return t

	def bob_0conf0_getbalance(self): return self.bob_getbalance(rtBals_gb['0conf0'],confs=0)
	def bob_0conf1_getbalance(self): return self.bob_getbalance(rtBals_gb['0conf1'],confs=1)
	def bob_1conf1_getbalance(self): return self.bob_getbalance(rtBals_gb['1conf1'],confs=1)
	def bob_1conf2_getbalance(self): return self.bob_getbalance(rtBals_gb['1conf2'],confs=2)

	def bob_nochg_burn(self):
		return self.user_txdo('bob',
			fee          = '0.00009713',
			outputs_cl   = [f'{make_burn_addr(self.proto)}'],
			outputs_list = '1' )

	def bob_alice_bal(self):
		t = self.spawn('mmgen-regtest',['balances'])
		ret = t.expect_getend("Bob's balance:").strip()
		cmp_or_die(rtBals[4],ret)
		ret = t.expect_getend("Alice's balance:").strip()
		cmp_or_die(rtBals[5],ret)
		ret = t.expect_getend("Total balance:").strip()
		cmp_or_die(rtBals[6],ret)
		return t

	def user_txsend_status(self,user,tx_file,exp1='',exp2='',extra_args=[]):
		t = self.spawn('mmgen-txsend',['-d',self.tmpdir,'--'+user,'--status'] + extra_args + [tx_file])
		if exp1: t.expect(exp1,regex=True)
		if exp2: t.expect(exp2,regex=True)
		return t

	def user_txdo(  self, user, fee, outputs_cl, outputs_list,
			extra_args   = [],
			wf           = None,
			do_label     = False,
			bad_locktime = False,
			full_tx_view = False,
			menu         = ['M'],
			skip_passphrase = False ):

		t = self.spawn('mmgen-txdo',
			['-d',self.tmpdir,'-B','--'+user] +
			(['--tx-fee='+fee] if fee else []) +
			extra_args + ([],[wf])[bool(wf)] + outputs_cl)

		self.txcreate_ui_common(t,
			caller          = 'txdo',
			menu            = menu,
			inputs          = outputs_list,
			file_desc       = 'Signed transaction',
			interactive_fee = (tx_fee,'')[bool(fee)],
			add_comment     = tx_label_jp,
			view            = 't',save=True)

		if not skip_passphrase:
			t.passphrase(dfl_wcls.desc,rt_pw)

		t.written_to_file('Signed transaction')
		self._do_confirm_send(t)
		s,exit_val = (('Transaction sent',0),("can't be included",1))[bad_locktime]
		t.expect(s)
		t.req_exit_val = exit_val
		return t

	def bob_split1(self):
		sid = self._user_sid('bob')
		outputs_cl = [sid+':C:1,100', sid+':L:2,200',sid+':'+rtBobOp3]
		return self.user_txdo('bob',rtFee[0],outputs_cl,'1',do_label=True,full_tx_view=True)

	def get_addr_from_addrlist(self,user,sid,mmtype,idx,addr_range='1-5'):
		id_str = { 'L':'', 'S':'-S', 'C':'-C', 'B':'-B' }[mmtype]
		ext = '{}{}{}[{}]{x}.regtest.addrs'.format(
			sid,self.altcoin_pfx,id_str,addr_range,x='-α' if g.debug_utf8 else '')
		addrfile = get_file_with_ext(self._user_dir(user),ext,no_dot=True)
		silence()
		addr = AddrList(self.proto,addrfile).data[idx].addr
		end_silence()
		return addr

	def _create_tx_outputs(self,user,data):
		sid = self._user_sid(user)
		return [self.get_addr_from_addrlist(user,sid,mmtype,idx-1)+amt_str for mmtype,idx,amt_str in data]

	def bob_rbf_1output_create(self):
		if not self.test_rbf:
			return 'skip'
		out_addr = self._create_tx_outputs('alice',(('B',5,''),))
		t = self.spawn('mmgen-txcreate',['-d',self.tr.trash_dir,'-B','--bob','--rbf'] + out_addr)
		return self.txcreate_ui_common(t,menu=[],inputs='3',interactive_fee='3s') # out amt: 199.99999343

	def bob_rbf_1output_bump(self):
		if not self.test_rbf:
			return 'skip'
		ext = '9343,3]{x}.regtest.rawtx'.format(x='-α' if g.debug_utf8 else '')
		txfile = get_file_with_ext(self.tr.trash_dir,ext,delete=False,no_dot=True)
		return self.user_txbump('bob',
			self.tr.trash_dir,
			txfile,
			'8s',
			has_label  = False,
			signed_tx  = False,
			one_output = True )

	def bob_send_maybe_rbf(self):
		outputs_cl = self._create_tx_outputs('alice',(('L',1,',60'),('C',1,',40'))) # alice_sid:L:1, alice_sid:C:1
		outputs_cl += [self._user_sid('bob')+':'+rtBobOp3]
		return self.user_txdo('bob',rtFee[1],outputs_cl,'3',
					extra_args=([],['--rbf'])[self.proto.cap('rbf')])

	def bob_send_non_mmgen(self):
		outputs_cl = self._create_tx_outputs('alice',(
			(('L','S')[self.proto.cap('segwit')],2,',10'),
			(('L','S')[self.proto.cap('segwit')],3,'')
		)) # alice_sid:S:2, alice_sid:S:3
		keyfile = joinpath(self.tmpdir,'non-mmgen.keys')
		return self.user_txdo('bob',rtFee[3],outputs_cl,'1,4-10',
			extra_args=['--keys-from-file='+keyfile,'--vsize-adj=1.02'])

	def alice_send_estimatefee(self):
		outputs_cl = self._create_tx_outputs('bob',(('L',1,''),)) # bob_sid:L:1
		return self.user_txdo('alice',None,outputs_cl,'1') # fee=None

	def user_txbump(self,user,outdir,txfile,fee,add_args=[],has_label=True,signed_tx=True,one_output=False):
		if not self.proto.cap('rbf'):
			return 'skip'
		t = self.spawn('mmgen-txbump',
			['-d',outdir,'--'+user,'--tx-fee='+fee,'--output-to-reduce=c'] + add_args + [txfile])
		if not one_output:
			t.expect('OK? (Y/n): ','y') # output OK?
		t.expect('OK? (Y/n): ','y') # fee OK?
		t.do_comment(False,has_label=has_label)
		if signed_tx:
			t.passphrase(dfl_wcls.desc,rt_pw)
			t.written_to_file('Signed transaction')
			self.txsend_ui_common(t,caller='txdo',bogus_send=False,file_desc='Signed transaction')
		else:
			t.expect('Save fee-bumped transaction? (y/N): ','y')
			t.written_to_file('Fee-bumped transaction')
		return t

	def bob_rbf_bump(self):
		ext = ',{}]{x}.regtest.sigtx'.format(rtFee[1][:-1],x='-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,delete=False,no_dot=True)
		return self.user_txbump('bob',self.tmpdir,txfile,rtFee[2],add_args=['--send'])

	def generate(self,coin=None,num_blocks=1):
		int(num_blocks)
		t = self.spawn('mmgen-regtest',['generate',str(num_blocks)])
		t.expect(f'Mined {num_blocks} block')
		return t

	def _get_mempool(self):
		if not g.debug_utf8:
			disable_debug()
		ret = self.spawn('mmgen-regtest',['mempool']).read()
		if not g.debug_utf8:
			restore_debug()
		m = re.search(r'(\[\s*"[a-f0-9]{64}"\s*])',ret) # allow for extra output by handler at end
		return json.loads(m.group(1))

	def get_mempool1(self):
		mp = self._get_mempool()
		if len(mp) != 1:
			die(4,'Mempool has more or less than one TX!')
		self.write_to_tmpfile('rbf_txid',mp[0]+'\n')
		return 'ok'

	def bob_rbf_status(self,fee,exp1,exp2=''):
		if not self.proto.cap('rbf'):
			return 'skip'
		ext = ',{}]{x}.regtest.sigtx'.format(fee[:-1],x='-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,delete=False,no_dot=True)
		return self.user_txsend_status('bob',txfile,exp1,exp2)

	def bob_rbf_status1(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self.bob_rbf_status(rtFee[1],'in mempool, replaceable')

	def get_mempool2(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		mp = self._get_mempool()
		if len(mp) != 1:
			die(4,'Mempool has more or less than one TX!')
		chk = self.read_from_tmpfile('rbf_txid')
		if chk.strip() == mp[0]:
			die(4,'TX in mempool has not changed!  RBF bump failed')
		self.write_to_tmpfile('rbf_txid2',mp[0]+'\n')
		return 'ok'

	def bob_rbf_status2(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		new_txid = self.read_from_tmpfile('rbf_txid2').strip()
		return self.bob_rbf_status(rtFee[1],
			'Transaction has been replaced',f'{new_txid} in mempool')

	def bob_rbf_status3(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self.bob_rbf_status(rtFee[2],'status: in mempool, replaceable')

	def bob_rbf_status4(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		new_txid = self.read_from_tmpfile('rbf_txid2').strip()
		return self.bob_rbf_status(rtFee[1],
			'Replacement transaction has 1 confirmation',
			f'Replacing transactions:\s+{new_txid}' )

	def bob_rbf_status5(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self.bob_rbf_status(rtFee[2],'Transaction has 1 confirmation')

	def bob_rbf_status6(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		new_txid = self.read_from_tmpfile('rbf_txid2').strip()
		return self.bob_rbf_status(rtFee[1],
			'Replacement transaction has 2 confirmations',
			f'Replacing transactions:\s+{new_txid}' )

	def _gen_pairs(self,n):
		from mmgen.tool.api import tool_api
		t = tool_api()
		t.init_coin(self.proto.coin,self.proto.network)

		def gen_addr(Type):
			t.addrtype = Type
			wif = t.hex2wif(getrandhex(32))
			return ( wif, t.wif2addr(wif) )

		return [gen_addr('legacy')] + [gen_addr('compressed') for i in range(n-1)]

	def bob_pre_import(self):
		pairs = self._gen_pairs(5)
		self.write_to_tmpfile('non-mmgen.keys','\n'.join([a[0] for a in pairs])+'\n')
		self.write_to_tmpfile('non-mmgen.addrs','\n'.join([a[1] for a in pairs])+'\n')
		return self.user_txdo('bob',rtFee[4],[pairs[0][1]],'3')

	def user_import(self,user,args,nAddr):
		t = self.spawn('mmgen-addrimport',['--'+user]+args)
		if g.debug:
			t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
		t.expect(f'Importing {nAddr} address')
		if '--rescan' in args:
			for i in range(nAddr):
				t.expect('OK')
		return t

	def bob_import_addr(self):
		addr = self.read_from_tmpfile('non-mmgen.addrs').split()[0]
		return self.user_import('bob',['--quiet','--address='+addr],nAddr=1)

	def bob_resolve_addr(self):
		mmaddr = '{}:C:1'.format(self._user_sid('bob'))
		t = self.spawn('mmgen-tool',['--bob','resolve_address',mmaddr])
		coinaddr = t.read().split()[0].strip()
		t = self.spawn('mmgen-tool',['--bob','resolve_address',coinaddr],no_msg=True)
		mmaddr_res = t.read().split()[0].strip()
		assert mmaddr == mmaddr_res, f'{mmaddr} != {mmaddr_res}'
		return t

	def bob_import_list(self):
		addrfile = joinpath(self.tmpdir,'non-mmgen.addrs')
		return self.user_import('bob',['--quiet','--addrlist',addrfile],nAddr=5)

	def bob_import_list_rescan(self):
		addrfile = joinpath(self.tmpdir,'non-mmgen.addrs')
		return self.user_import('bob',['--quiet','--rescan','--addrlist',addrfile],nAddr=5)

	def bob_rescan_blockchain(self,add_args,expect):
		t = self.spawn('mmgen-tool',['--bob','rescan_blockchain'] + add_args)
		t.expect(f'Scanning blocks {expect}')
		t.expect('Done')
		return t

	def bob_rescan_blockchain_all(self):
		return self.bob_rescan_blockchain([],'400-400')

	def bob_rescan_blockchain_gb(self):
		return self.bob_rescan_blockchain(['start_block=0','stop_block=0'],'0-0')

	def bob_rescan_blockchain_one(self):
		return self.bob_rescan_blockchain(['start_block=300','stop_block=300'],'300-300')

	def bob_rescan_blockchain_ss(self):
		return self.bob_rescan_blockchain(['start_block=300','stop_block=302'],'300-302')

	def bob_split2(self):
		addrs = self.read_from_tmpfile('non-mmgen.addrs').split()
		amts = (1.12345678,2.87654321,3.33443344,4.00990099,5.43214321)
		outputs1 = list(map('{},{}'.format,addrs,amts))
		sid = self._user_sid('bob')
		l1,l2 = (
			(':S',':B') if 'B' in self.proto.mmtypes else
			(':S',':S') if self.proto.cap('segwit') else
			(':L',':L') )
		outputs2 = [sid+':C:2,6.333', sid+':L:3,6.667',sid+l1+':4,0.123',sid+l2+':5']
		return self.user_txdo('bob',rtFee[5],outputs1+outputs2,'1-2')

	def user_add_label(self,user,addr,label):
		t = self.spawn('mmgen-tool',['--'+user,'add_label',addr,label])
		t.expect('Added label.*in tracking wallet',regex=True)
		return t

	def user_remove_label(self,user,addr):
		t = self.spawn('mmgen-tool',['--'+user,'remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		return t

	def bob_add_label(self):
		sid = self._user_sid('bob')
		return self.user_add_label('bob',sid+':C:1',tw_label_lat_cyr_gr)

	def alice_add_label1(self):
		sid = self._user_sid('alice')
		return self.user_add_label('alice',sid+':C:1','Original Label - 月へ')

	def alice_add_label2(self):
		sid = self._user_sid('alice')
		return self.user_add_label('alice',sid+':C:1','Replacement Label')

	def _user_chk_label(self,user,addr,label):
		t = self.spawn('mmgen-tool',['--'+user,'listaddresses','all_labels=1'])
		ret = strip_ansi_escapes(t.expect_getend(addr)).strip().split(None,1)[1]
		cmp_or_die(ret[:len(label)],label)
		return t

	def alice_add_label_coinaddr(self):
		mmid = self._user_sid('alice') + (':S:1',':L:1')[self.proto.coin=='BCH']
		t = self.spawn('mmgen-tool',['--alice','listaddress',mmid],no_msg=True)
		addr = [i for i in strip_ansi_escapes(t.read()).splitlines() if i.startswith(mmid)][0].split()[1]
		return self.user_add_label('alice',addr,'Label added using coin address of MMGen address')

	def alice_chk_label_coinaddr(self):
		mmid = self._user_sid('alice') + (':S:1',':L:1')[self.proto.coin=='BCH']
		return self._user_chk_label('alice',mmid,'Label added using coin address of MMGen address')

	def alice_add_label_badaddr(self,addr,reply):
		if os.getenv('PYTHONOPTIMIZE'):
			omsg(yellow(f'PYTHONOPTIMIZE set, skipping test {self.test_name!r}'))
			return 'skip'
		t = self.spawn('mmgen-tool',['--alice','add_label',addr,'(none)'])
		t.expect(reply,regex=True)
		return t

	def alice_add_label_badaddr1(self):
		return self.alice_add_label_badaddr( rt_pw,'Invalid coin address for this chain: ')

	def alice_add_label_badaddr2(self):
		addr = init_proto(self.proto.coin,network='mainnet').pubhash2addr(bytes(20),False) # mainnet zero address
		return self.alice_add_label_badaddr( addr, f'Invalid coin address for this chain: {addr}' )

	def alice_add_label_badaddr3(self):
		addr = self._user_sid('alice') + ':C:123'
		return self.alice_add_label_badaddr( addr, f'MMGen address {addr!r} not found in tracking wallet' )

	def alice_add_label_badaddr4(self):
		addr = self.proto.pubhash2addr(bytes(20),False) # regtest (testnet) zero address
		return self.alice_add_label_badaddr( addr, f'Address {addr!r} not found in tracking wallet' )

	def alice_remove_label1(self):
		sid = self._user_sid('alice')
		mmid = sid + (':S:3',':L:3')[self.proto.coin=='BCH']
		return self.user_remove_label('alice',mmid)

	def alice_chk_label1(self):
		sid = self._user_sid('alice')
		return self._user_chk_label('alice',sid+':C:1','Original Label - 月へ')

	def alice_chk_label2(self):
		sid = self._user_sid('alice')
		return self._user_chk_label('alice',sid+':C:1','Replacement Label')

	def alice_edit_label1(self): return self.user_edit_label('alice','4',tw_label_lat_cyr_gr)
	def alice_edit_label2(self): return self.user_edit_label('alice','3',tw_label_zh)

	def alice_chk_label3(self):
		sid = self._user_sid('alice')
		mmid = sid + (':S:3',':L:3')[self.proto.coin=='BCH']
		return self._user_chk_label('alice',mmid,tw_label_lat_cyr_gr)

	def alice_chk_label4(self):
		sid = self._user_sid('alice')
		mmid = sid + (':S:3',':L:3')[self.proto.coin=='BCH']
		return self._user_chk_label('alice',mmid,'-')

	def user_edit_label(self,user,output,label):
		t = self.spawn('mmgen-txcreate',['-B','--'+user,'-i'])
		t.expect(r'add \[l\]abel:.','M',regex=True)
		t.expect(r'add \[l\]abel:.','l',regex=True)
		t.expect(r"Enter unspent.*return to main menu\):.",output+'\n',regex=True)
		t.expect(r"Enter label text.*return to main menu\):.",label+'\n',regex=True)
		t.expect(r'\[q\]uit view, .*?:.','q',regex=True)
		return t

	def alice_listaddresses(self,args,expect):
		t = self.spawn('mmgen-tool',['--alice','listaddresses','showempty=1'] + args)
		expect_str = r'\D{}\D.*\b{}'.format(*expect)
		t.expect(expect_str,regex=True)
		return t

	def alice_listaddresses1(self):
		return self.alice_listaddresses(
			args = [],
			expect = (rtAmts[1],r'\d+') )

	def alice_listaddresses_days(self):
		return self.alice_listaddresses(
			args = ['age_fmt=days'],
			expect = (rtAmts[1],r'\d+') )

	def alice_listaddresses_date(self):
		return self.alice_listaddresses(
			args = ['age_fmt=date'],
			expect = (rtAmts[1],pat_date) )

	def alice_listaddresses_date_time(self):
		return self.alice_listaddresses(
			args = ['age_fmt=date_time'],
			expect = (rtAmts[1],pat_date_time) )

	def alice_twview(self,args,expect):
		t = self.spawn('mmgen-tool',['--alice','twview'] + args)
		expect_str = r'\D{}\D.*\b{}'.format(*expect)
		t.expect(expect_str,regex=True)
		return t

	def alice_twview1(self):
		return self.alice_twview(
			args = [],
			expect = (rtAmts[0],r'\d+') )

	def alice_twview_days(self):
		return self.alice_twview(
			args = ['age_fmt=days'],
			expect = (rtAmts[0],r'\d+') )

	def alice_twview_date(self):
		return self.alice_twview(
			args = ['age_fmt=date'],
			expect = (rtAmts[0],pat_date) )

	def alice_twview_date_time(self):
		return self.alice_twview(
			args = ['age_fmt=date_time'],
			expect = (rtAmts[0],pat_date_time) )

	def alice_txcreate_info(self,args=[]):
		t = self.spawn('mmgen-txcreate',['--alice','-Bi'])
		pats = (
				( '\d+',                       'D'),
				( '\d+',                       'D'),
				( '\d+',                       'D'),
				( pat_date,                    'q'),
		) if opt.pexpect_spawn else (
				( '\d+',                       'D'),
				( '\d+',                       'D'),
				( '\d+',                       'D'),
				( pat_date,                    'w'),
				( '\d+\s+\d+\s+'+pat_date_time,'q'),
		)
		for d,s in pats:
			t.expect(
				r'\D{}\D.*\b{}\b'.format( rtAmts[0], d ),
				s,
				regex=True )
		return t

	def bob_msgcreate(self):
		sid1 = self._user_sid('bob')
		sid2 = self._get_user_subsid('bob','29L')
		return self.spawn(
			'mmgen-msg', [
				'--bob',
				f'--outdir={self.tmpdir}',
				'create',
				'16/3/2022 Earthquake strikes Fukushima coast',
				f'{sid1}:{self.dfl_mmtype}:1-4',
				f'{sid2}:C:3-7,87,98'
			])

	def bob_msgsign(self,wallets=[]):
		fn = get_file_with_ext(self.tmpdir,'rawmsg.json')
		t = self.spawn(
			'mmgen-msg', [
				'--bob',
				f'--outdir={self.tmpdir}',
				'sign',
				fn
			] + wallets )
		if not wallets:
			t.passphrase(dfl_wcls.desc,rt_pw)
		return t

	def bob_walletconv_words(self):
		t = self.spawn(
			'mmgen-walletconv', [ '--bob', f'--outdir={self.tmpdir}', '--out-fmt=words' ] )
		t.passphrase(dfl_wcls.desc,rt_pw)
		t.written_to_file('data')
		return t

	def bob_subwalletgen_bip39(self):
		t = self.spawn(
			'mmgen-subwalletgen', [ '--bob', f'--outdir={self.tmpdir}', '--out-fmt=bip39', '29L' ] )
		t.passphrase(dfl_wcls.desc,rt_pw)
		t.written_to_file('data')
		return t

	def bob_msgsign_userwallet(self):
		fn1 = get_file_with_ext(self.tmpdir,'mmwords')
		return self.bob_msgsign([fn1])

	def bob_msgsign_userwallets(self):
		fn1 = get_file_with_ext(self.tmpdir,'mmwords')
		fn2 = get_file_with_ext(self.tmpdir,'bip39')
		return self.bob_msgsign([fn2,fn1])

	def bob_msgverify(self,addr=None,ext='sigmsg.json',cmd='verify',msgfile=None):
		return self.spawn(
			'mmgen-msg', [
				'--bob',
				f'--outdir={self.tmpdir}',
				cmd,
				msgfile or get_file_with_ext(self.tmpdir,ext),
			] + ([addr] if addr else []) )

	def bob_msgverify_raw(self):
		t = self.bob_msgverify(ext='rawmsg.json')
		t.req_exit_val = 1
		return t

	def bob_msgverify_single(self):
		sid = self._user_sid('bob')
		return self.bob_msgverify(addr=f'{sid}:{self.dfl_mmtype}:1')

	def bob_msgexport(self,addr=None):
		t = self.bob_msgverify( addr=addr, cmd='export' )
		t.written_to_file('data')
		return t

	def bob_msgexport_single(self):
		sid = self._user_sid('bob')
		return self.bob_msgexport(addr=f'{sid}:{self.dfl_mmtype}:1')

	def bob_msgverify_export(self):
		return self.bob_msgverify(
			msgfile = os.path.join(self.tmpdir,'signatures.json')
		)

	def bob_msgverify_export_single(self):
		sid = self._user_sid('bob')
		mmid = f'{sid}:{self.dfl_mmtype}:1'
		t = self.spawn('mmgen-tool', [ '--bob', '--color=0', 'listaddress', mmid ], no_msg=True)
		addr = t.expect_getend(mmid).split()[0]
		t.close()
		return self.bob_msgverify(
			addr = addr,
			msgfile = os.path.join(self.tmpdir,'signatures.json')
		)

	def stop(self):
		if opt.no_daemon_stop:
			self.spawn('',msg_only=True)
			msg_r('(leaving daemon running by user request)')
			return 'ok'
		else:
			return self.spawn('mmgen-regtest',['stop'])
