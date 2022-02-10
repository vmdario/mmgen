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
wallet.incog_base: incognito wallet base class
"""

from ..globalvars import g
from ..opts import opt
from ..seed import Seed
from ..util import msg,vmsg,qmsg,make_chksum_8,keypress_confirm
from .enc import wallet
import mmgen.crypto as crypto

class wallet(wallet):

	_msg = {
		'check_incog_id': """
  Check the generated Incog ID above against your records.  If it doesn't
  match, then your incognito data is incorrect or corrupted.
	""",
		'record_incog_id': """
  Make a record of the Incog ID but keep it secret.  You will use it to
  identify your incog wallet data in the future.
	""",
		'decrypt_params': " {} hash preset"
	}

	def _make_iv_chksum(self,s):
		from hashlib import sha256
		return sha256(s).hexdigest()[:8].upper()

	def _get_incog_data_len(self,seed_len):
		return (
			crypto.aesctr_iv_len
			+ crypto.salt_len
			+ (0 if opt.old_incog_fmt else crypto.hincog_chk_len)
			+ seed_len//8 )

	def _incog_data_size_chk(self):
		# valid sizes: 56, 64, 72
		dlen = len(self.fmt_data)
		seed_len = opt.seed_len or Seed.dfl_len
		valid_dlen = self._get_incog_data_len(seed_len)
		if dlen == valid_dlen:
			return True
		else:
			if opt.old_incog_fmt:
				msg('WARNING: old-style incognito format requested.  Are you sure this is correct?')
			msg(f'Invalid incognito data size ({dlen} bytes) for this seed length ({seed_len} bits)')
			msg(f'Valid data size for this seed length: {valid_dlen} bytes')
			for sl in Seed.lens:
				if dlen == self._get_incog_data_len(sl):
					die(1,f'Valid seed length for this data size: {sl} bits')
			msg(f'This data size ({dlen} bytes) is invalid for all available seed lengths')
			return False

	def _encrypt (self):
		self._get_first_pw_and_hp_and_encrypt_seed()
		if opt.old_incog_fmt:
			die(1,'Writing old-format incog wallets is unsupported')
		d = self.ssdata
		# IV is used BOTH to initialize counter and to salt password!
		d.iv = crypto.get_random( crypto.aesctr_iv_len )
		d.iv_id = self._make_iv_chksum(d.iv)
		msg(f'New Incog Wallet ID: {d.iv_id}')
		qmsg('Make a record of this value')
		vmsg('\n  ' + self.msg['record_incog_id'].strip()+'\n')

		d.salt = crypto.get_random( crypto.salt_len )
		key = crypto.make_key( d.passwd, d.salt, d.hash_preset, 'incog wallet key' )
		from hashlib import sha256
		chk = sha256(self.seed.data).digest()[:8]
		d.enc_seed = crypto.encrypt_data(
			chk + self.seed.data,
			key,
			crypto.aesctr_dfl_iv,
			'seed' )

		d.wrapper_key = crypto.make_key( d.passwd, d.iv, d.hash_preset, 'incog wrapper key' )
		d.key_id = make_chksum_8(d.wrapper_key)
		vmsg(f'Key ID: {d.key_id}')
		d.target_data_len = self._get_incog_data_len(self.seed.bitlen)

	def _format(self):
		d = self.ssdata
		self.fmt_data = d.iv + crypto.encrypt_data(
			d.salt + d.enc_seed,
			d.wrapper_key,
			d.iv,
			self.desc )

	def _filename(self):
		s = self.seed
		d = self.ssdata
		return '{}-{}-{}[{},{}]{x}.{}'.format(
				s.fn_stem,
				d.key_id,
				d.iv_id,
				s.bitlen,
				d.hash_preset,
				self.ext,
				x='-α' if g.debug_utf8 else '')

	def _deformat(self):

		if not self._incog_data_size_chk():
			return False

		d = self.ssdata
		d.iv             = self.fmt_data[0:crypto.aesctr_iv_len]
		d.incog_id       = self._make_iv_chksum(d.iv)
		d.enc_incog_data = self.fmt_data[crypto.aesctr_iv_len:]
		msg(f'Incog Wallet ID: {d.incog_id}')
		qmsg('Check this value against your records')
		vmsg('\n  ' + self.msg['check_incog_id'].strip()+'\n')

		return True

	def _verify_seed_newfmt(self,data):
		chk,seed = data[:8],data[8:]
		from hashlib import sha256
		if sha256(seed).digest()[:8] == chk:
			qmsg('Passphrase{} are correct'.format( self.msg['decrypt_params'].format('and') ))
			return seed
		else:
			msg('Incorrect passphrase{}'.format( self.msg['decrypt_params'].format('or') ))
			return False

	def _verify_seed_oldfmt(self,seed):
		m = f'Seed ID: {make_chksum_8(seed)}.  Is the Seed ID correct?'
		if keypress_confirm(m, True):
			return seed
		else:
			return False

	def _decrypt(self):
		d = self.ssdata
		self._get_hash_preset(add_desc=d.incog_id)
		d.passwd = self._get_passphrase(add_desc=d.incog_id)

		# IV is used BOTH to initialize counter and to salt password!
		key = crypto.make_key( d.passwd, d.iv, d.hash_preset, 'wrapper key' )
		dd = crypto.decrypt_data( d.enc_incog_data, key, d.iv, 'incog data' )

		d.salt     = dd[0:crypto.salt_len]
		d.enc_seed = dd[crypto.salt_len:]

		key = crypto.make_key( d.passwd, d.salt, d.hash_preset, 'main key' )
		qmsg(f'Key ID: {make_chksum_8(key)}')

		verify_seed = getattr(self,'_verify_seed_'+
						('newfmt','oldfmt')[bool(opt.old_incog_fmt)])

		seed = verify_seed( crypto.decrypt_seed(d.enc_seed, key, '', '') )

		if seed:
			self.seed = Seed(seed)
			msg(f'Seed ID: {self.seed.sid}')
			return True
		else:
			return False