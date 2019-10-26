#!/usr/bin/env python3
"""
test/unit_tests_d/ut_baseconv.py: Base conversion unit test for the MMGen suite
"""

from mmgen.common import *
from mmgen.exception import *

class unit_test(object):

	vectors = {
		'b58': (
			(('00',None),'1'),
			(('00',1),'1'),
			(('00',2),'11'),
			(('01',None),'2'),
			(('01',1),'2'),
			(('01',2),'12'),
			(('0f',None),'G'),
			(('0f',1),'G'),
			(('0f',2),'1G'),
			(('deadbeef',None),'6h8cQN'),
			(('deadbeef',20),'111111111111116h8cQN'),
			(('00000000',None),'1'),
			(('00000000',20),'11111111111111111111'),
			(('ffffffff',None),'7YXq9G'),
			(('ffffffff',20),'111111111111117YXq9G'),
			(('ff'*16,'seed'),'YcVfxkQb6JRzqk5kF2tNLv'),
			(('ff'*24,'seed'),'QLbz7JHiBTspS962RLKV8GndWFwiEaqKL'),
			(('ff'*32,'seed'),'JEKNVnkbo3jma5nREBBJCDoXFVeKkD56V3xKrvRmWxFG'),
			(('00'*16,'seed'),'1111111111111111111111'),
			(('00'*24,'seed'),'111111111111111111111111111111111'),
			(('00'*32,'seed'),'11111111111111111111111111111111111111111111'),
		),
		# MMGen-flavored base32 using simple base conversion
		'b32': (
			(('00',None),'A'),
			(('00',1),'A'),
			(('00',2),'AA'),
			(('01',None),'B'),
			(('01',1),'B'),
			(('01',2),'AB'),
			(('0f',None),'P'),
			(('0f',1),'P'),
			(('0f',2),'AP'),
			(('deadbeef',None),'DPK3PXP'),
			(('deadbeef',20),'AAAAAAAAAAAAADPK3PXP'),
			(('00000000',None),'A'),
			(('00000000',20),'AAAAAAAAAAAAAAAAAAAA'),
			(('ffffffff',None),'D777777'),
			(('ffffffff',20),'AAAAAAAAAAAAAD777777'),
		),
		'b16': (
			(('00',None),'0'),
			(('00',1),'0'),
			(('00',2),'00'),
			(('01',None),'1'),
			(('01',1),'1'),
			(('01',2),'01'),
			(('0f',None),'f'),
			(('0f',1),'f'),
			(('0f',2),'0f'),
			(('deadbeef',None),'deadbeef'),
			(('deadbeef',20),'000000000000deadbeef'),
			(('00000000',None),'0'),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'ffffffff'),
			(('ffffffff',20),'000000000000ffffffff'),
		),
		'b10': (
			(('00',None),'0'),
			(('00',1),'0'),
			(('00',2),'00'),
			(('01',None),'1'),
			(('01',1),'1'),
			(('01',2),'01'),
			(('0f',None),'15'),
			(('0f',1),'15'),
			(('0f',2),'15'),
			(('deadbeef',None),'3735928559'),
			(('deadbeef',20),'00000000003735928559'),
			(('00000000',None),'0'),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'4294967295'),
			(('ffffffff',20),'00000000004294967295'),
		),
		'b8': (
			(('00',None),'0'),
			(('00',1),'0'),
			(('00',2),'00'),
			(('01',None),'1'),
			(('01',1),'1'),
			(('01',2),'01'),
			(('0f',None),'17'),
			(('0f',1),'17'),
			(('0f',2),'17'),
			(('deadbeef',None),'33653337357'),
			(('deadbeef',20),'00000000033653337357'),
			(('00000000',None),'0'),
			(('00000000',20),'00000000000000000000'),
			(('ffffffff',None),'37777777777'),
			(('ffffffff',20),'00000000037777777777'),
		),
	}

	def run_test(self,name,ut):

		msg_r('Testing base conversion routines...')

		from mmgen.util import baseconv
		perr = "length of {!r} less than pad length ({})"
		rerr = "return value ({!r}) does not match reference value ({!r})"

		qmsg_r('\nChecking hex-to-base conversion:')
		for base,data in self.vectors.items():
			fs = "  {h:%s}  {p:<6} {r}" % max(len(d[0][0]) for d in data)
			if not opt.verbose: qmsg_r(' {}'.format(base))
			vmsg('\nBase: {}'.format(base))
			vmsg(fs.format(h='Input',p='Pad',r='Output'))
			for (hexstr,pad),ret_chk in data:
				ret = baseconv.fromhex(hexstr,wl_id=base,pad=pad,tostr=True)
				if pad != 'seed':
					assert len(ret) >= (pad or 0), perr.format(ret,pad or 0)
				assert ret == ret_chk, rerr.format(ret,ret_chk)
				vmsg(fs.format(h=hexstr,r=ret,p=str(pad)))
#				msg("(('{h}',{p}),'{r}'),".format(h=hexstr,r=ret,c=ret_chk,p=pad))
#			msg('')
#		return True
		qmsg_r('\nChecking base-to-hex conversion:')
		for base,data in self.vectors.items():
			fs = "  {h:%s}  {p:<6} {r}" % max(len(d[1]) for d in data)
			if not opt.verbose: qmsg_r(' {}'.format(base))
			vmsg('\nBase: {}'.format(base))
			vmsg(fs.format(h='Input',p='Pad',r='Output'))
			for (hexstr,pad),ret_chk in data:
				if type(pad) == int:
					pad = len(hexstr)
				ret = baseconv.tohex(ret_chk,wl_id=base,pad=pad)
				if pad == None:
					assert int(ret,16) == int(hexstr,16), rerr.format(int(ret,16),int(hexstr,16))
				else:
					assert ret == hexstr, rerr.format(ret,hexstr)
				vmsg(fs.format(h=ret_chk,r=ret,p=str(pad)))
#				msg("(('{h}',{p}),'{r}'),".format(h=hexstr,r=ret_chk,c=ret_chk,p=pad))

		qmsg('')

		vmsg('')
		qmsg('Checking error handling:')

		b = baseconv
		bad_data = (
('bad hexstr',       'HexadecimalStringError','not a hexadecimal str',   lambda:b.fromhex('x','b58')),
('empty hexstr',     'HexadecimalStringError','empty hex strings not',   lambda:b.fromhex('','b58')),
('bad b58 data',     'BaseConversionError',   'not in b58',              lambda:b.tohex('IfFzZ','b58')),
('empty b58 data',   'BaseConversionError',   'empty b58 data',          lambda:b.tohex('','b58')),
('empty b8 data' ,   'BaseConversionError',   'empty b8 data',           lambda:b.tohex('','b8')),
('bad b32 data',     'BaseConversionError',   'not in b32',              lambda:b.tohex('1az','b32')),
('bad pad arg (in)', 'BaseConversionPadError',"illegal value for 'pad'", lambda:b.fromhex('ff','b58',pad='foo')),
('bad pad arg (in)', 'BaseConversionPadError',"illegal value for 'pad'", lambda:b.fromhex('ff','b58',pad=False)),
('bad pad arg (in)', 'BaseConversionPadError',"illegal value for 'pad'", lambda:b.fromhex('ff','b58',pad=True)),
('bad seedlen (in)', 'SeedLengthError',       "invalid seed byte length",lambda:b.fromhex('ff','b58',pad='seed')),
('bad pad arg (out)','BaseConversionPadError',"illegal value for 'pad'", lambda:b.tohex('Z','b58',pad='foo')),
('bad pad arg (out)','BaseConversionPadError',"illegal value for 'pad'", lambda:b.tohex('Z','b58',pad=False)),
('bad pad arg (out)','BaseConversionPadError',"illegal value for 'pad'", lambda:b.tohex('Z','b58',pad=True)),
('bad seedlen (out)','BaseConversionError',   "invalid length for seed", lambda:b.tohex('Z','b58',pad='seed')),
		)

		ut.process_bad_data(bad_data)

		msg('OK')

		return True
