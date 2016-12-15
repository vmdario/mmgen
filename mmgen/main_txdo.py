#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
mmgen-txdo: Create, sign and broadcast an online MMGen transaction
"""

from mmgen.txcreate import *
from mmgen.txsign import *

opts_data = {
	'desc': 'Create, sign and send an {g.proj_name} transaction'.format(g=g),
	'usage':   '[opts]  <addr,amt> ... [change addr] [addr file] ... [seed source] ...',
	'options': """
-h, --help             Print this help message
--, --longhelp         Print help message for long options (common options)
-a, --tx-fee-adj=    f Adjust transaction fee by factor 'f' (see below)
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for brainwallet
                       input
-B, --no-blank         Don't blank screen before displaying unspent outputs
-c, --comment-file=  f Source the transaction's comment from file 'f'
-C, --tx-confs=      c Desired number of confirmations (default: {g.tx_confs})
-d, --outdir=        d Specify an alternate directory 'd' for output
-e, --echo-passphrase  Print passphrase to screen when typing it
-f, --tx-fee=f         Transaction fee (default: {g.tx_fee} BTC (but see below))
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-i, --in-fmt=        f Input is from wallet format 'f' (see FMT CODES below)
-l, --seed-len=      l Specify wallet seed length of 'l' bits. This option
                       is required only for brainwallet and incognito inputs
                       with non-standard (< {g.seed_len}-bit) seed lengths.
-k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
-K, --key-generator= m Use method 'm' for public key generation
                       Options: {kgs} (default: {kg})
-m, --minconf=n        Minimum number of confirmations required to spend outputs (default: 1)
-M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
                       address file (output of '{pnl}-keygen'). Permits
                       online signing without an {pnm} seed source. The
                       key-address file is also used to verify {pnm}-to-BTC
                       mappings, so the user should record its checksum.
-O, --old-incog-fmt    Specify old-format incognito input
-p, --hash-preset=   p Use the scrypt hash parameters defined by preset 'p'
                       for password hashing (default: '{g.hash_preset}')
-P, --passwd-file=   f Get {pnm} wallet or bitcoind passphrase from file 'f'
-q, --quiet            Suppress warnings; overwrite files without prompting
-v, --verbose          Produce more verbose output
-z, --show-hash-presets Show information on available hash presets
""".format(g=g,pnm=pnm,pnl=pnm.lower(),
		kgs=' '.join(['{}:{}'.format(n,k) for n,k in enumerate(g.key_generators,1)]),
		kg=g.key_generator),
	'notes': '\n' + txcreate_notes + txsign_notes
}

cmd_args = opts.init(opts_data)
seed_files = get_seed_files(opt,cmd_args)
c = bitcoin_connection()
do_license_msg()

kal = get_keyaddrlist(opt)
kl = get_keylist(opt)
if kl and kal: kl.remove_dups(kal,key='wif')

tx = txcreate(opt,cmd_args,caller='txdo')
txsign(opt,c,tx,seed_files,kl,kal)
tx.write_to_file(ask_write=False)

if tx.send(opt,c):
	tx.write_to_file(ask_write=False)