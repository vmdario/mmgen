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
mmgen-autosign: Auto-sign MMGen transactions
"""

import sys,os,time,signal,shutil
from subprocess import run,PIPE,DEVNULL
from stat import *

mountpoint   = '/mnt/tx'
tx_dir       = '/mnt/tx/tx'
part_label   = 'MMGEN_TX'
wallet_dir   = '/dev/shm/autosign'
key_fn       = 'autosign.key'

from .common import *
prog_name = os.path.basename(sys.argv[0])
opts_data = {
	'sets': [('stealth_led', True, 'led', True)],
	'text': {
		'desc': 'Auto-sign MMGen transactions',
		'usage':'[opts] [command]',
		'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-c, --coins=c       Coins to sign for (comma-separated list)
-I, --no-insert-check Don't check for device insertion
-l, --led           Use status LED to signal standby, busy and error
-m, --mountpoint=m  Specify an alternate mountpoint (default: '{mp}')
-n, --no-summary    Don't print a transaction summary
-s, --stealth-led   Stealth LED mode - signal busy and error only, and only
                    after successful authorization.
-S, --full-summary  Print a full summary of each signed transaction after
                    each autosign run. The default list of non-MMGen outputs
                    will not be printed.
-q, --quiet         Produce quieter output
-v, --verbose       Produce more verbose output
""".format(mp=mountpoint),
	'notes': """

                              COMMANDS

gen_key - generate the wallet encryption key and copy it to '{td}'
setup   - generate the wallet encryption key and wallet
wait    - start in loop mode: wait-mount-sign-unmount-wait


                             USAGE NOTES

If invoked with no command, the program mounts a removable device containing
MMGen transactions, signs any unsigned transactions, unmounts the removable
device and exits.

If invoked with 'wait', the program waits in a loop, mounting, signing and
unmounting every time the removable device is inserted.

On supported platforms (currently Orange Pi and Raspberry Pi boards), the
status LED indicates whether the program is busy or in standby mode, i.e.
ready for device insertion or removal.

The removable device must have a partition labeled MMGEN_TX and a user-
writable directory '/tx', where unsigned MMGen transactions are placed.

On the signing machine the mount point '{mp}' must exist and /etc/fstab
must contain the following entry:

    LABEL='MMGEN_TX' /mnt/tx auto noauto,user 0 0

Transactions are signed with a wallet on the signing machine (in the directory
'{wd}') encrypted with a 64-character hexadecimal password on the
removable device.

The password and wallet can be created in one operation by invoking the
command with 'setup' with the removable device inserted.  The user will be
prompted for a seed mnemonic.

Alternatively, the password and wallet can be created separately by first
invoking the command with 'gen_key' and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -r0 -q -iwords -d{wd} -p1 -P{td}/{kf} -Llabel

Note that the hash preset must be '1'.  Multiple wallets are permissible.

For good security, it's advisable to re-generate a new wallet and key for
each signing session.

This command is currently available only on Linux-based platforms.
""".format(pnm=prog_name,wd=wallet_dir,td=tx_dir,kf=key_fn,mp=mountpoint)
	}
}

cmd_args = opts.init(opts_data,add_opts=['mmgen_keys_from_file','in_fmt'])

exit_if_mswin('autosigning')

import mmgen.tx
from .txsign import txsign
from .protocol import init_proto,init_coin
from .rpc import rpc_init

if g.test_suite:
	from .daemon import CoinDaemon

if opt.mountpoint:
	mountpoint = opt.mountpoint

opt.outdir = tx_dir = os.path.join(mountpoint,'tx')

async def check_daemons_running():
	if opt.coin:
		die(1,'--coin option not supported with this command.  Use --coins instead')
	if opt.coins:
		coins = opt.coins.upper().split(',')
	else:
		ymsg('Warning: no coins specified, so defaulting to BTC only')
		coins = ['BTC']

	for coin in coins:
		g.proto = init_proto(coin,g.proto.testnet)
		if g.proto.sign_mode == 'daemon':
			if g.test_suite:
				g.proto.daemon_data_dir = 'test/daemons/' + coin.lower()
				g.rpc_port = CoinDaemon(get_network_id(coin,g.proto.testnet),test_suite=True).rpc_port
			vmsg(f'Checking {coin} daemon')
			try:
				await rpc_init()
			except SystemExit as e:
				if e.code != 0:
					ydie(1,f'{coin} daemon not running or not listening on port {g.proto.rpc_port}')

def get_wallet_files():
	try:
		dlist = os.listdir(wallet_dir)
	except:
		die(1,f"Cannot open wallet directory {wallet_dir!r}. Did you run 'mmgen-autosign setup'?")

	fns = [x for x in dlist if x.endswith('.mmdat')]
	if fns:
		return [os.path.join(wallet_dir,w) for w in fns]
	else:
		die(1,'No wallet files present!')

def do_mount():
	if not os.path.ismount(mountpoint):
		if run(['mount',mountpoint],stderr=DEVNULL,stdout=DEVNULL).returncode == 0:
			msg(f'Mounting {mountpoint}')
	try:
		ds = os.stat(tx_dir)
		assert S_ISDIR(ds.st_mode), f'{tx_dir!r} is not a directory!'
		assert ds.st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR,f'{tx_dir!r} is not read/write for this user!'
	except:
		die(1,'{tx_dir!r} missing, or not read/writable by user!')

def do_umount():
	if os.path.ismount(mountpoint):
		run(['sync'],check=True)
		msg(f'Unmounting {mountpoint}')
		run(['umount',mountpoint],check=True)

async def sign_tx_file(txfile,signed_txs):
	try:
		init_coin('BTC',testnet=False)
		tmp_tx = mmgen.tx.MMGenTX(txfile,metadata_only=True)
		init_coin(tmp_tx.coin)

		if tmp_tx.chain != 'mainnet':
			if tmp_tx.chain == 'testnet' or (
				hasattr(g.proto,'chain_name') and tmp_tx.chain != g.proto.chain_name):
				init_coin(tmp_tx.coin,testnet=True)

		if hasattr(g.proto,'chain_name'):
			if tmp_tx.chain != g.proto.chain_name:
				die(2, f'Chains do not match! tx file: {tmp_tx.chain}, proto: {g.proto.chain_name}')

		g.chain = tmp_tx.chain
		g.token = tmp_tx.dcoin
		g.proto.dcoin = tmp_tx.dcoin or g.proto.coin

		tx = mmgen.tx.MMGenTxForSigning(txfile)

		if g.proto.sign_mode == 'daemon':
			if g.test_suite:
				g.proto.daemon_data_dir = 'test/daemons/' + g.coin.lower()
				g.rpc_port = CoinDaemon(get_network_id(g.coin,g.proto.testnet),test_suite=True).rpc_port
			await rpc_init()

		if await txsign(tx,wfs,None,None):
			tx.write_to_file(ask_write=False)
			signed_txs.append(tx)
			return True
		else:
			return False
	except Exception as e:
		msg(f'An error occurred: {e.args[0]}')
		if g.debug or g.traceback:
			print_stack_trace(f'AUTOSIGN {txfile}')
		return False
	except:
		return False

async def sign():
	dirlist  = os.listdir(tx_dir)
	raw,signed = [set(f[:-6] for f in dirlist if f.endswith(ext)) for ext in ('.rawtx','.sigtx')]
	unsigned = [os.path.join(tx_dir,f+'.rawtx') for f in raw - signed]

	if unsigned:
		signed_txs,fails = [],[]
		for txfile in unsigned:
			ret = await sign_tx_file(txfile,signed_txs)
			if not ret:
				fails.append(txfile)
			qmsg('')
		time.sleep(0.3)
		msg('{} transaction{} signed'.format(len(signed_txs),suf(signed_txs)))
		if fails:
			rmsg('{} transaction{} failed to sign'.format(len(fails),suf(fails)))
		if signed_txs and not opt.no_summary:
			print_summary(signed_txs)
		if fails:
			rmsg('\nFailed transactions:')
			rmsg('  ' + '\n  '.join(sorted(fails)) + '\n')
		return False if fails else True
	else:
		msg('No unsigned transactions')
		time.sleep(1)
		return True

def decrypt_wallets():
	opt.hash_preset = '1'
	opt.set_by_user = ['hash_preset']
	opt.passwd_file = os.path.join(tx_dir,key_fn)
	from .wallet import Wallet
	msg("Unlocking wallet{} with key from '{}'".format(suf(wfs),opt.passwd_file))
	fails = 0
	for wf in wfs:
		try:
			Wallet(wf)
		except SystemExit as e:
			if e.code != 0:
				fails += 1

	return False if fails else True

def print_summary(signed_txs):

	if opt.full_summary:
		bmsg('\nAutosign summary:\n')
		def gen():
			for tx in signed_txs:
				init_coin(tx.coin,tx.chain == 'testnet')
				yield tx.format_view(terse=True)
		msg_r(''.join(gen()))
		return

	def gen():
		for tx in signed_txs:
			non_mmgen = [o for o in tx.outputs if not o.mmid]
			if non_mmgen:
				yield (tx,non_mmgen)

	body = list(gen())

	if body:
		bmsg('\nAutosign summary:')
		fs = '{}  {} {}'
		t_wid,a_wid = 6,44

		def gen():
			yield fs.format('TX ID ','Non-MMGen outputs'+' '*(a_wid-17),'Amount')
			yield fs.format('-'*t_wid, '-'*a_wid, '-'*7)
			for tx,non_mmgen in body:
				for nm in non_mmgen:
					yield fs.format(
						tx.txid.fmt(width=t_wid,color=True) if nm is non_mmgen[0] else ' '*t_wid,
						nm.addr.fmt(width=a_wid,color=True),
						nm.amt.hl() + ' ' + yellow(tx.coin))

		msg('\n'.join(gen()))
	else:
		msg('No non-MMGen outputs')

async def do_sign():
	if not opt.stealth_led:
		led.set('busy')
	do_mount()
	key_ok = decrypt_wallets()
	if key_ok:
		if opt.stealth_led:
			led.set('busy')
		ret = await sign()
		do_umount()
		led.set(('standby','off','error')[(not ret)*2 or bool(opt.stealth_led)])
		return ret
	else:
		msg('Password is incorrect!')
		do_umount()
		if not opt.stealth_led:
			led.set('error')
		return False

def wipe_existing_key():
	fn = os.path.join(tx_dir,key_fn)
	try: os.stat(fn)
	except: pass
	else:
		msg('\nWiping existing key {}'.format(fn))
		run(['wipe','-cf',fn],check=True)

def create_key():
	kdata = os.urandom(32).hex()
	fn = os.path.join(tx_dir,key_fn)
	desc = 'key file {}'.format(fn)
	msg('Creating ' + desc)
	try:
		open(fn,'w').write(kdata+'\n')
		os.chmod(fn,0o400)
		msg('Wrote ' + desc)
	except:
		die(2,'Unable to write ' + desc)

def gen_key(no_unmount=False):
	create_wallet_dir()
	if not get_insert_status():
		die(1,'Removable device not present!')
	do_mount()
	wipe_existing_key()
	create_key()
	if not no_unmount:
		do_umount()

def remove_wallet_dir():
	msg("Deleting '{}'".format(wallet_dir))
	try: shutil.rmtree(wallet_dir)
	except: pass

def create_wallet_dir():
	try: os.mkdir(wallet_dir)
	except: pass
	try: os.stat(wallet_dir)
	except: die(2,"Unable to create wallet directory '{}'".format(wallet_dir))

def setup():
	remove_wallet_dir()
	gen_key(no_unmount=True)
	from .wallet import Wallet
	opt.hidden_incog_input_params = None
	opt.quiet = True
	opt.in_fmt = 'words'
	ss_in = Wallet()
	opt.out_fmt = 'wallet'
	opt.usr_randchars = 0
	opt.hash_preset = '1'
	opt.set_by_user = ['hash_preset']
	opt.passwd_file = os.path.join(tx_dir,key_fn)
	from .obj import MMGenWalletLabel
	opt.label = MMGenWalletLabel('Autosign Wallet')
	ss_out = Wallet(ss=ss_in)
	ss_out.write_to_file(desc='autosign wallet',outdir=wallet_dir)

def get_insert_status():
	if opt.no_insert_check:
		return True
	try: os.stat(os.path.join('/dev/disk/by-label',part_label))
	except: return False
	else: return True

def check_wipe_present():
	try:
		run(['wipe','-v'],stdout=DEVNULL,stderr=DEVNULL,check=True)
	except:
		die(2,"The 'wipe' utility must be installed before running this program")

async def do_loop():
	n,prev_status = 0,False
	if not opt.stealth_led:
		led.set('standby')
	while True:
		status = get_insert_status()
		if status and not prev_status:
			msg('Device insertion detected')
			await do_sign()
		prev_status = status
		if not n % 10:
			msg_r('\r{}\rWaiting'.format(' '*17))
			sys.stderr.flush()
		time.sleep(1)
		msg_r('.')
		n += 1

if len(cmd_args) not in (0,1):
	opts.usage()

if len(cmd_args) == 1:
	cmd = cmd_args[0]
	if cmd in ('gen_key','setup'):
		globals()[cmd]()
		sys.exit(0)
	elif cmd != 'wait':
		die(1,f'{cmd!r}: unrecognized command')

check_wipe_present()
wfs = get_wallet_files()

def at_exit(exit_val,message='\nCleaning up...'):
	if message:
		msg(message)
	led.stop()
	sys.exit(exit_val)

def handler(a,b):
	at_exit(1)

signal.signal(signal.SIGTERM,handler)
signal.signal(signal.SIGINT,handler)

from .led import LEDControl
led = LEDControl(enabled=opt.led,simulate=g.test_suite and not os.getenv('MMGEN_TEST_SUITE_AUTOSIGN_LIVE'))
led.set('off')

async def main():
	await check_daemons_running()

	if len(cmd_args) == 0:
		ret = await do_sign()
		at_exit(int(not ret),message='')
	elif cmd_args[0] == 'wait':
		await do_loop()

run_session(main(),do_rpc_init=False)
