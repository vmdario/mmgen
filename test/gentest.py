#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
test/gentest.py:  Cryptocoin key/address generation tests for the MMGen suite
"""

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))
os.environ['MMGEN_TEST_SUITE'] = '1'

# Import these _after_ local path's been added to sys.path
from mmgen.common import *

rounds = 100
opts_data = {
	'text': {
		'desc': 'Test key/address generation of the MMGen suite in various ways',
		'usage':'[options] [spec] [rounds | dump file]',
		'options': """
-h, --help       Print this help message
-a, --all        Test all coins supported by specified external tool
-k, --use-internal-keccak-module Force use of the internal keccak module
--, --longhelp   Print help message for long options (common options)
-q, --quiet      Produce quieter output
-t, --type=t     Specify address type (e.g. 'compressed','segwit','zcash_z','bech32')
-v, --verbose    Produce more verbose output
""",
	'notes': """
TEST TYPES:

   A/B:     {prog} A:B [rounds]  (compare key generators A and B)
   Speed:   {prog} A [rounds]    (test speed of key generator A)
   Compare: {prog} A <dump file> (compare generator A to wallet dump)

     where A and B are one of:
       '1' - native Python ECDSA library (slow), or
       '2' - bitcoincore.org's libsecp256k1 library (default);
     or:
       B is name of an external tool (see below) or 'ext'.
       If B is 'ext', the external tool will be chosen automatically.

EXAMPLES:

  Compare addresses generated by native Python ECDSA library and libsecp256k1,
  100 rounds:
  $ {prog} 1:2 100

  Compare mmgen-secp256k1 Segwit address generation to pycoin library for all
  supported coins, 100 rounds:
  $ {prog} --all --type=segwit 2:pycoin 100

  Compare mmgen-secp256k1 address generation to keyconv tool for all
  supported coins, 100 rounds:
  $ {prog} --all --type=compressed 2:keyconv 100

  Compare mmgen-secp256k1 XMR address generation to configured external tool,
  10 rounds:
  $ {prog} --coin=xmr 2:ext 10

  Test speed of mmgen-secp256k1 address generation, 10,000 rounds:
  $ {prog} 2 10000

  Compare mmgen-secp256k1-generated bech32 addrs to coin daemon wallet dump:
  $ {prog} --type=bech32 2 bech32wallet.dump

Supported external tools:

  + ethkey (for ETH,ETC)
	https://github.com/openethereum/openethereum
    (build with 'cargo build -p ethkey-cli --release')

  + zcash-mini (for Zcash Z-addresses)
    https://github.com/FiloSottile/zcash-mini

  + moneropy (for Monero addresses)
    https://github.com/bigreddmachine/MoneroPy

  + pycoin (for supported coins)
    https://github.com/richardkiss/pycoin

  + keyconv (for supported coins)
    https://github.com/exploitagency/vanitygen-plus
    ('keyconv' does not generate Segwit addresses)
"""
	},
	'code': {
		'notes': lambda s: s.format(
			prog='test/gentest.py',
			pnm=g.proj_name,
			snum=rounds )
	}
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cmd_args = opts.init(opts_data,add_opts=['exact_output','use_old_ed25519'])

if not 1 <= len(cmd_args) <= 2:
	opts.usage()

from mmgen.protocol import init_proto_from_opts
proto = init_proto_from_opts()

from subprocess import run,PIPE,DEVNULL
def get_cmd_output(cmd,input=None):
	return run(cmd,input=input,stdout=PIPE,stderr=DEVNULL).stdout.decode().splitlines()

from collections import namedtuple
gtr = namedtuple('gen_tool_result',['wif','addr','vk'])

class GenTool(object):

	def run_tool(self,sec):
		vcoin = 'BTC' if proto.coin == 'BCH' else proto.coin
		return self.run(sec,vcoin)

class GenToolEthkey(GenTool):
	desc = 'ethkey'
	def __init__(self):
		proto = init_proto('eth')
		global addr_type
		addr_type = MMGenAddrType(proto,'E')

	def run(self,sec,vcoin):
		o = get_cmd_output(['ethkey','info',sec])
		return gtr(o[0].split()[1],o[-1].split()[1],None)

class GenToolKeyconv(GenTool):
	desc = 'keyconv'
	def run(self,sec,vcoin):
		o = get_cmd_output(['keyconv','-C',vcoin,sec.wif])
		return gtr(o[1].split()[1],o[0].split()[1],None)

class GenToolZcash_mini(GenTool):
	desc = 'zcash-mini'
	def __init__(self):
		proto = init_proto('zec')
		global addr_type
		addr_type = MMGenAddrType(proto,'Z')

	def run(self,sec,vcoin):
		o = get_cmd_output(['zcash-mini','-key','-simple'],input=(sec.wif+'\n').encode())
		return gtr(o[1],o[0],o[-1])

class GenToolPycoin(GenTool):
	"""
	pycoin/networks/all.py pycoin/networks/legacy_networks.py
	"""
	desc = 'pycoin'
	def __init__(self):
		m = "Unable to import pycoin.networks.registry.  Is pycoin installed on your system?"
		try:
			from pycoin.networks.registry import network_for_netcode
		except:
			raise ImportError(m)
		self.nfnc = network_for_netcode

	def run(self,sec,vcoin):
		if proto.testnet:
			vcoin = ci.external_tests['testnet']['pycoin'][vcoin]
		network = self.nfnc(vcoin)
		key = network.keys.private(secret_exponent=int(sec,16),is_compressed=addr_type.name != 'legacy')
		if key is None:
			die(1,"can't parse {}".format(sec))
		if addr_type.name in ('segwit','bech32'):
			hash160_c = key.hash160(is_compressed=True)
			if addr_type.name == 'segwit':
				p2sh_script = network.contract.for_p2pkh_wit(hash160_c)
				addr = network.address.for_p2s(p2sh_script)
			else:
				addr = network.address.for_p2pkh_wit(hash160_c)
		else:
			addr = key.address()
		return gtr(key.wif(),addr,None)

class GenToolMoneropy(GenTool):
	desc = 'moneropy'
	def __init__(self):

		m = "Unable to import moneropy.  Is moneropy installed on your system?"
		try:
			import moneropy.account
		except:
			raise ImportError(m)

		self.mpa = moneropy.account
		proto = init_proto('xmr')

		global addr_type
		addr_type = MMGenAddrType(proto,'M')

	def run(self,sec,vcoin):
		sk_t,vk_t,addr_t = self.mpa.account_from_spend_key(sec) # VERY slow!
		return gtr(sk_t,addr_t,vk_t)

def get_tool(arg):

	if arg not in ext_progs + ['ext']:
		die(1,'{!r}: unsupported tool for network {}'.format(arg,proto.network))

	if opt.all:
		if arg == 'ext':
			die(1,"'--all' must be combined with a specific external testing tool")
		return arg
	else:
		tool = ci.get_test_support(
			proto.coin,
			addr_type.name,
			proto.network,
			verbose = not opt.quiet,
			tool = arg if arg in ext_progs else None )
		if not tool:
			sys.exit(2)
		if arg in ext_progs and arg != tool:
			sys.exit(3)
		return tool

def test_equal(desc,a_val,b_val,in_bytes,sec,wif,a_desc,b_desc):
	if a_val != b_val:
		fs = """
  {i:{w}}: {}
  {s:{w}}: {}
  {W:{w}}: {}
  {a:{w}}: {}
  {b:{w}}: {}
			"""
		die(3,
			red('\nERROR: {} do not match!').format(desc)
			+ fs.format(
				in_bytes.hex(), sec, wif, a_val, b_val,
				i='input', s='sec key', W='WIF key', a=a_desc, b=b_desc,
				w=max(len(e) for e in (a_desc,b_desc)) + 1
		).rstrip())

def gentool_test(kg_a,kg_b,ag,rounds):

	m = "Comparing address generators '{A}' and '{B}' for {N} {c} ({n}), addrtype {a!r}"
	e = ci.get_entry(proto.coin,proto.network)
	qmsg(green(m.format(
		A = kg_a.desc,
		B = kg_b.desc,
		N = proto.network,
		c = proto.coin,
		n = e.name if e else '---',
		a = addr_type.name )))

	global last_t
	last_t = time.time()

	def do_compare_test(n,trounds,in_bytes):
		global last_t
		if opt.verbose or time.time() - last_t >= 0.1:
			qmsg_r('\rRound {}/{} '.format(i+1,trounds))
			last_t = time.time()
		sec = PrivKey(proto,in_bytes,compressed=addr_type.compressed,pubkey_type=addr_type.pubkey_type)
		a_ph = kg_a.to_pubhex(sec)
		a_addr = ag.to_addr(a_ph)
		a_vk = None
		tinfo = (in_bytes,sec,sec.wif,kg_a.desc,kg_b.desc)
		if isinstance(kg_b,GenTool):
			b = kg_b.run_tool(sec)
			test_equal('WIF keys',sec.wif,b.wif,*tinfo)
			test_equal('addresses',a_addr,b.addr,*tinfo)
			if b.vk:
				a_vk = ag.to_viewkey(a_ph)
				test_equal('view keys',a_vk,b.vk,*tinfo)
		else:
			b_addr = ag.to_addr(kg_b.to_pubhex(sec))
			test_equal('addresses',a_addr,b_addr,*tinfo)
		vmsg(fs.format(b=in_bytes.hex(),k=sec.wif,v=a_vk,a=a_addr))
		qmsg_r('\rRound {}/{} '.format(n+1,trounds))

	fs  = ( '\ninput:    {b}\n%-9s {k}\naddr:     {a}\n',
			'\ninput:    {b}\n%-9s {k}\nviewkey:  {v}\naddr:     {a}\n')[
				'viewkey' in addr_type.extra_attrs] % (addr_type.wif_label + ':')

	# test some important private key edge cases:
	edgecase_sks = (
		bytes([0x00]*31 + [0x01]), # min
		bytes([0xff]*32),          # max
		bytes([0x0f] + [0xff]*31), # same key as above for zcash-z
		bytes([0x00]*31 + [0xff]), # monero will reduce
		bytes([0xff]*31 + [0x0f]), # monero will not reduce
	)

	qmsg(purple('edge cases:'))
	for i,in_bytes in enumerate(edgecase_sks):
		do_compare_test(i,len(edgecase_sks),in_bytes)
	qmsg(green('\rOK            ' if opt.verbose else 'OK'))

	qmsg(purple('random input:'))
	for i in range(rounds):
		do_compare_test(i,rounds,os.urandom(32))
	qmsg(green('\rOK            ' if opt.verbose else 'OK'))

def speed_test(kg,ag,rounds):
	m = "Testing speed of address generator '{}' for coin {}"
	qmsg(green(m.format(kg.desc,proto.coin)))
	from struct import pack,unpack
	seed = os.urandom(28)
	qmsg('Incrementing key with each round')
	qmsg('Starting key: {}'.format((seed + pack('I',0)).hex()))
	import time
	start = last_t = time.time()

	for i in range(rounds):
		if time.time() - last_t >= 0.1:
			qmsg_r('\rRound {}/{} '.format(i+1,rounds))
			last_t = time.time()
		sec = PrivKey(proto,seed+pack('I',i),compressed=addr_type.compressed,pubkey_type=addr_type.pubkey_type)
		addr = ag.to_addr(kg.to_pubhex(sec))
		vmsg('\nkey:  {}\naddr: {}\n'.format(sec.wif,addr))
	qmsg_r('\rRound {}/{} '.format(i+1,rounds))
	qmsg('\n{} addresses generated in {:.2f} seconds'.format(rounds,time.time()-start))

def dump_test(kg,ag,fh):

	dump = [[*(e.split()[0] for e in line.split('addr='))] for line in fh.readlines() if 'addr=' in line]
	if not dump:
		die(1,'File {!r} appears not to be a wallet dump'.format(fh.name))

	m = 'Comparing output of address generator {!r} against wallet dump {!r}'
	qmsg(green(m.format(kg.desc,fh.name)))

	for count,(b_wif,b_addr) in enumerate(dump,1):
		qmsg_r('\rKey {}/{} '.format(count,len(dump)))
		try:
			b_sec = PrivKey(proto,wif=b_wif)
		except:
			die(2,'\nInvalid {} WIF address in dump file: {}'.format(proto.network,b_wif))
		a_addr = ag.to_addr(kg.to_pubhex(b_sec))
		vmsg('\nwif: {}\naddr: {}\n'.format(b_wif,b_addr))
		tinfo = (bytes.fromhex(b_sec),b_sec,b_wif,kg.desc,fh.name)
		test_equal('addresses',a_addr,b_addr,*tinfo)
	qmsg(green(('\n','')[bool(opt.verbose)] + 'OK'))

def init_tool(tname):
	return globals()['GenTool'+capfirst(tname.replace('-','_'))]()

def parse_arg1(arg,arg_id):

	m1 = 'First argument must be a numeric generator ID or two colon-separated generator IDs'
	m2 = 'Second part of first argument must be a numeric generator ID or one of {}'

	def check_gen_num(n):
		if not (1 <= int(n) <= len(g.key_generators)):
			die(1,'{}: invalid generator ID'.format(n))
		return int(n)

	if arg_id == 'a':
		if is_int(arg):
			a_num = check_gen_num(arg)
			return (KeyGenerator(proto,addr_type,a_num),a_num)
		else:
			die(1,m1)
	elif arg_id == 'b':
		if is_int(arg):
			return KeyGenerator(proto,addr_type,check_gen_num(arg))
		elif arg in ext_progs + ['ext']:
			return init_tool(get_tool(arg))
		else:
			die(1,m2.format(ext_progs))

def parse_arg2():
	m = 'Second argument must be dump filename or integer rounds specification'
	if len(cmd_args) == 1:
		return None
	arg = cmd_args[1]
	if is_int(arg) and int(arg) > 0:
		return int(arg)
	try:
		return open(arg)
	except:
		die(1,m)

# begin execution
from mmgen.protocol import init_proto
from mmgen.altcoin import CoinInfo as ci
from mmgen.obj import MMGenAddrType,PrivKey
from mmgen.addr import KeyGenerator,AddrGenerator

addr_type = MMGenAddrType(
	proto = proto,
	id_str = opt.type or proto.dfl_mmtype )
ext_progs = list(ci.external_tests[proto.network])

arg1 = cmd_args[0].split(':')
if len(arg1) == 1:
	a,a_num = parse_arg1(arg1[0],'a')
	b = None
elif len(arg1) == 2:
	a,a_num = parse_arg1(arg1[0],'a')
	b = parse_arg1(arg1[1],'b')
else:
	opts.usage()

if type(a) == type(b):
	die(1,'Address generators are the same!')

arg2 = parse_arg2()

if not opt.all:
	ag = AddrGenerator(proto,addr_type)

if not b and type(arg2) == int:
	speed_test(a,ag,arg2)
elif not b and hasattr(arg2,'read'):
	dump_test(a,ag,arg2)
elif a and b and type(arg2) == int:
	if opt.all:
		from mmgen.protocol import CoinProtocol,init_genonly_altcoins
		init_genonly_altcoins(testnet=proto.testnet)
		for coin in ci.external_tests[proto.network][b.desc]:
			if coin.lower() not in CoinProtocol.coins:
#				ymsg('Coin {} not configured'.format(coin))
				continue
			proto = init_proto(coin)
			if addr_type not in proto.mmtypes:
				continue
			# proto has changed, so reinit kg and ag
			a = KeyGenerator(proto,addr_type,a_num)
			ag = AddrGenerator(proto,addr_type)
			b_chk = ci.get_test_support(proto.coin,addr_type.name,proto.network,tool=b.desc,verbose=not opt.quiet)
			if b_chk == b.desc:
				gentool_test(a,b,ag,arg2)
	else:
		gentool_test(a,b,ag,arg2)
else:
	opts.usage()
