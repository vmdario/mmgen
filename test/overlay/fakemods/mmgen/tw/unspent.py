import os as overlay_fake_os
from .unspent_orig import *

if overlay_fake_os.getenv('MMGEN_BOGUS_UNSPENT_DATA'):

	class overlay_fake_data:

		async def set_dates(_,us):
			for o in us:
				o.date = 1831006505 - int(9.7 * 60 * (o.confs - 1))

	TwUnspentOutputs.set_dates = overlay_fake_data.set_dates
