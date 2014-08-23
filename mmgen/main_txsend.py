#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
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
mmgen-txsend: Broadcast a transaction signed by 'mmgen-txsign' to the network
"""

import sys

import mmgen.config as g
from mmgen.Opts import *
from mmgen.license import *
from mmgen.tx import *
from mmgen.util import msg,check_infile,get_lines_from_file,confirm_or_exit

help_data = {
	'prog_name': g.prog_name,
	'desc':    "Send a Bitcoin transaction signed by {}-txsign".format(g.proj_name.lower()),
	'usage':   "[opts] <signed transaction file>",
	'options': """
-h, --help      Print this help message
-d, --outdir= d Specify an alternate directory 'd' for output
-q, --quiet     Suppress warnings; overwrite files without prompting
"""
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]; check_infile(infile)
else: usage(help_data)

# Begin execution

do_license_msg()

tx_data = get_lines_from_file(infile,"signed transaction data")

metadata,tx_hex,inputs_data,b2m_map,comment = parse_tx_file(tx_data,infile)

qmsg("Signed transaction file '%s' is valid" % infile)

c = connect_to_bitcoind()

prompt = "View transaction data? (y)es, (N)o, (v)iew in pager"
reply = prompt_and_get_char(prompt,"YyNnVv",enter_ok=True)
if reply and reply in "YyVv":
	view_tx_data(c,inputs_data,tx_hex,b2m_map,comment,metadata,reply in "Vv")

if keypress_confirm("Edit transaction comment?"):
	comment = get_tx_comment_from_user(comment)
	data = make_tx_data("{} {} {}".format(*metadata), tx_hex,
				inputs_data, b2m_map, comment)
	w = "signed transaction with edited comment"
	outfile = infile
	write_to_file(outfile,data,opts,w,False,True,True)

warn   = "Once this transaction is sent, there's no taking it back!"
what   = "broadcast this transaction to the network"
expect =  "YES, I REALLY WANT TO DO THIS"

if g.quiet: warn,expect = "","YES"

confirm_or_exit(warn, what, expect)

msg("Sending transaction")

try:
	tx_id = c.sendrawtransaction(tx_hex)
except:
	msg("Unable to send transaction")
	sys.exit(3)

msg("Transaction sent: %s" % tx_id)

of = "tx_{}[{}].txid".format(*metadata[:2])
write_to_file(of, tx_id+"\n",opts,"transaction ID",True,True)