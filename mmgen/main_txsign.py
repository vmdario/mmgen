#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
mmgen-txsign: Sign a transaction generated by 'mmgen-txcreate'
"""

import mmgen.opts as opts
from .globalvars import gc
from .util import msg,ymsg,die,async_run
from .subseed import SubSeedIdxRange
from .wallet import Wallet
from .color import orange

# -w, --use-wallet-dat (keys from running coin daemon) removed: use walletdump rpc instead
opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc':    f'Sign cryptocoin transactions generated by {gc.proj_name.lower()}-txcreate',
		'usage':   '[opts] <transaction file>... [seed source]...',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
                      brainwallet input
-d, --outdir=      d  Specify an alternate directory 'd' for output
-D, --tx-id           Display transaction ID and exit
-e, --echo-passphrase Print passphrase to screen when typing it
-E, --use-internal-keccak-module Force use of the internal keccak module
-i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-O, --old-incog-fmt   Specify old-format incognito input
-l, --seed-len=    l  Specify wallet seed length of 'l' bits. This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {dsl}-bit) seed lengths.
-p, --hash-preset=p   Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{gc.dfl_hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
-K, --keygen-backend=n Use backend 'n' for public key generation.  Options
                      for {coin_id}: {kgs}
-M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
                      address file (output of '{pnl}-keygen'). Permits
                      online signing without an {pnm} seed source. The
                      key-address file is also used to verify {pnm}-to-{cu}
                      mappings, so the user should record its checksum.
-P, --passwd-file= f  Get {pnm} wallet passphrase from file 'f'
-q, --quiet           Suppress warnings; overwrite files without prompting
-I, --info            Display information about the transaction and exit
-t, --terse-info      Like '--info', but produce more concise output
-u, --subseeds=     n The number of subseed pairs to scan for (default: {ss},
                      maximum: {ss_max}). Only the default or first supplied
                      wallet is scanned for subseeds.
-v, --verbose         Produce more verbose output
-V, --vsize-adj=   f  Adjust transaction's estimated vsize by factor 'f'
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
""",
	'notes': """
{}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

FMT CODES:

  {f}
"""
	},
	'code': {
		'options': lambda cfg,proto,help_notes,s: s.format(
			cfg=cfg,
			gc=gc,
			pnm=gc.proj_name,
			pnl=gc.proj_name.lower(),
			kgs=help_notes('keygen_backends'),
			coin_id=help_notes('coin_id'),
			dsl=help_notes('dfl_seed_len'),
			ss=help_notes('dfl_subseeds'),
			ss_max=SubSeedIdxRange.max_idx,
			cu=proto.coin),
		'notes': lambda help_notes,s: s.format(
			help_notes('txsign'),
			f=help_notes('fmt_codes')),
	}
}

cfg = opts.init(opts_data)

infiles = cfg._args

if not infiles:
	opts.usage()

from .fileutil import check_infile
for i in infiles:
	check_infile(i)

if not cfg.info and not cfg.terse_info:
	from .ui import do_license_msg
	do_license_msg(cfg,immed=True)

from .tx.sign import *

tx_files   = get_tx_files(cfg,infiles)
seed_files = get_seed_files(cfg,infiles)

async def main():

	bad_tx_count = 0
	tx_num_disp = ''

	for tx_num,tx_file in enumerate(tx_files,1):

		if len(tx_files) > 1:
			tx_num_disp = f' #{tx_num}'
			msg(orange(f'\nTransaction{tx_num_disp} of {len(tx_files)}:'))

		from .tx import UnsignedTX
		tx1 = UnsignedTX(cfg=cfg,filename=tx_file)

		cfg._util.vmsg(f'Successfully opened transaction file {tx_file!r}')

		if tx1.proto.sign_mode == 'daemon':
			from .rpc import rpc_init
			tx1.rpc = await rpc_init(cfg,tx1.proto)

		if cfg.tx_id:
			msg(tx1.txid)
			continue

		if cfg.info or cfg.terse_info:
			tx1.view(pause=False,terse=cfg.terse_info)
			continue

		if not cfg.yes:
			tx1.info.view_with_prompt(f'View data for transaction{tx_num_disp}?')

		kal = get_keyaddrlist(cfg,tx1.proto)
		kl = get_keylist(cfg,tx1.proto)

		tx2 = await txsign(cfg,tx1,seed_files,kl,kal,tx_num_disp)
		if tx2:
			if not cfg.yes:
				tx2.add_comment() # edits an existing comment
			tx2.file.write(ask_write=not cfg.yes,ask_write_default_yes=True,add_desc=tx_num_disp)
		else:
			ymsg('Transaction could not be signed')
			bad_tx_count += 1

	if bad_tx_count:
		die(2,f'{bad_tx_count} transaction{suf(bad_tx_count)} could not be signed')

async_run(main())
