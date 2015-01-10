#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
addr.py:  Shared routines for the test suites
"""

import sys,os
from binascii import hexlify
from mmgen.util import msg,write_to_file
import mmgen.opt as opt

_red,_grn,_yel,_cya,_reset = (
	["\033[%sm" % c for c in "31;1","32;1","33;1","36;1","0"]
)
def red(s):    return _red+s+_reset
def green(s):  return _grn+s+_reset
def yellow(s): return _yel+s+_reset
def cyan(s):   return _cya+s+_reset

def cleandir(d):
	try:    files = os.listdir(d)
	except: return

	msg(green("Cleaning directory '%s'" % d))
	for f in files:
		os.unlink(os.path.join(d,f))

def getrandnum(n): return int(hexlify(os.urandom(n)),16)
def getrandhex(n): return hexlify(os.urandom(n))
def getrandstr(num_chars,no_space=False):
	n,m = 95,32
	if no_space: n,m = 94,33
	return "".join([chr(ord(i)%n+m) for i in list(os.urandom(num_chars))])

def mk_tmpdir(cfg):
	try: os.mkdir(cfg['tmpdir'],0755)
	except OSError as e:
		if e.errno != 17: raise
	else: msg("Created directory '%s'" % cfg['tmpdir'])

def get_tmpfile_fn(cfg,fn):
	return os.path.join(cfg['tmpdir'],fn)

def write_to_tmpfile(cfg,fn,data):
	write_to_file(os.path.join(cfg['tmpdir'],fn),data,silent=True)

def read_from_tmpfile(cfg,fn):
	from mmgen.util import get_data_from_file
	return get_data_from_file(os.path.join(cfg['tmpdir'],fn),silent=True)

def read_from_file(fn):
	from mmgen.util import get_data_from_file
	return get_data_from_file(fn,silent=True)

def ok():
	if opt.verbose or opt.exact_output:
		sys.stderr.write(green("OK\n"))
	else: msg(" OK")

def ok_or_die(val,chk_func,s,skip_ok=False):
	try: ret = chk_func(val)
	except: ret = False
	if ret:
	   if not skip_ok: ok()
	else:
		msg(red("Returned value '%s' is not a %s" % (val,s)))
		sys.exit(3)

def cmp_or_die(s,t,skip_ok=False):
	if s == t:
	   if not skip_ok: ok()
	else:
		msg(red("Recoded data:\n%s\ndiffers from original data:\n%s\n" %
					(repr(t),repr(s))))
		sys.exit(3)
