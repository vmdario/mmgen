#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

all_tests="dep dev lint obj color unit hash ref altref altgen xmr eth autosign btc btc_tn btc_rt bch bch_tn bch_rt ltc ltc_tn ltc_rt tool tool2 gen alt"

groups_desc="
	default  - All tests minus the extra tests
	extra    - All tests minus the default tests
	noalt    - BTC-only tests
	quick    - Default tests minus btc_tn, bch, bch_rt, ltc and ltc_rt
	qskip    - The tests skipped in the 'quick' test group
"

init_groups() {
	dfl_tests='dep alt obj color unit hash ref tool tool2 gen autosign btc btc_tn btc_rt altref altgen bch bch_rt ltc ltc_rt eth xmr'
	extra_tests='dep dev lint autosign_btc autosign_live ltc_tn bch_tn'
	noalt_tests='dep alt obj color unit hash ref tool tool2 gen autosign_btc btc btc_tn btc_rt'
	quick_tests='dep alt obj color unit hash ref tool tool2 gen autosign btc btc_rt altref altgen eth xmr'
	qskip_tests='lint btc_tn bch bch_rt ltc ltc_rt'

	[ "$MSYS2" ] && SKIP_LIST='autosign autosign_btc autosign_live'
	true
}

init_tests() {
	REFDIR='test/ref'

	d_alt="altcoin module"
	t_alt="
		- python3 -m test.altcointest $altcoin_mod_opts
	"

	d_obj="data objects"
	t_obj="
		- $objtest_py --coin=btc
		- $objtest_py --getobj --coin=btc
		- $objtest_py --coin=btc --testnet=1
		a $objtest_py --coin=ltc
		a $objtest_py --coin=ltc --testnet=1
		a $objtest_py --coin=eth
		- $objattrtest_py
	"
	[ "$SKIP_ALT_DEP" ] && t_obj_skip='a'

	[ "$PYTHONOPTIMIZE" ] && {
		echo -e "${YELLOW}PYTHONOPTIMIZE set, skipping object tests$RESET"
		t_obj_skip='-'
	}

	d_color="color handling"
	t_color='- test/colortest.py'

	d_dep="system and testing dependencies"
	t_dep="- $unit_tests_py testdep dep daemon.exec"

	d_dev="developer scripts ${YELLOW}(additional dependencies required)$RESET"
	t_dev="
		- $cmdtest_py dev
	"

	d_lint="code errors with static code analyzer"
	t_lint="
		- $pylint --errors-only mmgen
		- $pylint --errors-only test
		- $pylint --errors-only --disable=relative-beyond-top-level test/cmdtest_py_d
	"

	d_unit="low-level subsystems"
	t_unit="- $unit_tests_py --exclude testdep,dep,daemon"

	d_hash="internal hash function implementations"
	t_hash="
		256    $python test/hashfunc.py sha256 $rounds5x
		512    $python test/hashfunc.py sha512 $rounds5x # native SHA512 - not used by the MMGen wallet
		keccak $python test/hashfunc.py keccak $rounds5x
		ripemd160 $python mmgen/contrib/ripemd160.py $VERBOSE $fast_opt
	"

	[ "$ARM32" ] && t_hash_skip='512' # gmpy produces invalid init constants
	[ "$MSYS2" ] && t_hash_skip='512' # 2:py_long_long issues
	[ "$SKIP_ALT_DEP" ] && t_hash_skip+=' keccak'

	d_ref="generated values against reference data"
	t_ref="
		- $scrambletest_py
	"

	d_altref="altcoin reference file checks"
	t_altref="
		- $cmdtest_py ref_altcoin # generated addrfiles verified against checksums
	"

	d_altgen="altcoin address generation"
	t_altgen="
		- # speed tests, no verification:
		- $gentest_py --coin=etc 1 $rounds10x
		- $gentest_py --coin=etc --use-internal-keccak-module 1 $rounds10x
		- $gentest_py --coin=eth 1 $rounds10x
		- $gentest_py --coin=eth --use-internal-keccak-module 1 $rounds10x
		- $gentest_py --coin=xmr 1 $rounds10x
		- $gentest_py --coin=xmr --use-internal-keccak-module 1 $rounds10x
		- $gentest_py --coin=zec 1 $rounds10x
		- $gentest_py --coin=zec --type=zcash_z 1 $rounds10x
		- # verification against external libraries and tools:
		- #   pycoin
		- $gentest_py --all-coins --type=legacy 1:pycoin $rounds
		- $gentest_py --all-coins --type=compressed 1:pycoin $rounds
		- $gentest_py --all-coins --type=segwit 1:pycoin $rounds
		- $gentest_py --all-coins --type=bech32 1:pycoin $rounds

		- $gentest_py --all-coins --type=legacy --testnet=1 1:pycoin $rounds
		- $gentest_py --all-coins --type=compressed --testnet=1 1:pycoin $rounds
		- $gentest_py --all-coins --type=segwit --testnet=1 1:pycoin $rounds
		- $gentest_py --all-coins --type=bech32 --testnet=1 1:pycoin $rounds
		- #   keyconv
		- $gentest_py --all-coins --type=legacy 1:keyconv $rounds_min
		- $gentest_py --all-coins --type=compressed 1:keyconv $rounds_min
		e #   ethkey
		e $gentest_py --coin=eth 1:ethkey $rounds10x
		e $gentest_py --coin=eth --use-internal-keccak-module 2:ethkey $rounds5x
		m #   monero-python
		m $gentest_py --coin=xmr 1:monero-python $rounds100x
		M $gentest_py --coin=xmr all:monero-python $rounds_min # very slow, please be patient!
		z #   zcash-mini
		z $gentest_py --coin=zec --type=zcash_z all:zcash-mini $rounds50x
	"

	[ "$MSYS2" ] && t_altgen_skip='z'    # no zcash-mini (golang)
	[ "$ARM32" ] && t_altgen_skip='z e'
	[ "$FAST" ]  && t_altgen_skip+=' M'
	# ARM ethkey available only on Arch Linux:
	[ \( "$ARM32" -o "$ARM64" \) -a "$DISTRO" != 'archarm' ] && t_altgen_skip+=' e'


	d_xmr="Monero xmrwallet operations"
	t_xmr="
		- $cmdtest_py --coin=xmr
	"

	d_eth="operations for Ethereum and Ethereum Classic using devnet"
	t_eth="
		geth   $cmdtest_py --coin=eth ethdev
		parity $cmdtest_py --coin=etc ethdev
	"
	[ "$ARM32" -o "$ARM64" ] && t_eth_skip+=' parity'

	d_autosign="transaction and message autosigning"
	t_autosign="- $cmdtest_py autosign"

	d_autosign_btc="transaction and message autosigning (Bitcoin only)"
	t_autosign_btc="- $cmdtest_py autosign_btc"

	d_autosign_btc="transaction and message autosigning (interactive)"
	t_autosign_live="- $cmdtest_py autosign_live"

	d_btc="overall operations with emulated RPC data (Bitcoin)"
	t_btc="
		- $cmdtest_py --exclude regtest,autosign,ref_altcoin
		- $cmdtest_py --segwit
		- $cmdtest_py --segwit-random
		- $cmdtest_py --bech32
	"

	d_btc_tn="overall operations with emulated RPC data (Bitcoin testnet)"
	t_btc_tn="
		- $cmdtest_py --testnet=1
		- $cmdtest_py --testnet=1 --segwit
		- $cmdtest_py --testnet=1 --segwit-random
		- $cmdtest_py --testnet=1 --bech32
	"

	d_btc_rt="overall operations using the regtest network (Bitcoin)"
	t_btc_rt="- $cmdtest_py regtest"

	d_bch="overall operations with emulated RPC data (Bitcoin Cash Node)"
	t_bch="- $cmdtest_py --coin=bch --exclude regtest"

	d_bch_tn="overall operations with emulated RPC data (Bitcoin Cash Node testnet)"
	t_bch_tn="- $cmdtest_py --coin=bch --testnet=1 --exclude regtest"

	d_bch_rt="overall operations using the regtest network (Bitcoin Cash Node)"
	t_bch_rt="- $cmdtest_py --coin=bch regtest"

	d_ltc="overall operations with emulated RPC data (Litecoin)"
	t_ltc="
		- $cmdtest_py --coin=ltc --exclude regtest
		- $cmdtest_py --coin=ltc --segwit
		- $cmdtest_py --coin=ltc --segwit-random
		- $cmdtest_py --coin=ltc --bech32
	"

	d_ltc_tn="overall operations with emulated RPC data (Litecoin testnet)"
	t_ltc_tn="
		- $cmdtest_py --coin=ltc --testnet=1 --exclude regtest
		- $cmdtest_py --coin=ltc --testnet=1 --segwit
		- $cmdtest_py --coin=ltc --testnet=1 --segwit-random
		- $cmdtest_py --coin=ltc --testnet=1 --bech32
	"

	d_ltc_rt="overall operations using the regtest network (Litecoin)"
	t_ltc_rt="- $cmdtest_py --coin=ltc regtest"

	d_tool2="'mmgen-tool' utility with data check"
	t_tool2="
		- $tooltest2_py --tool-api # test the tool_api subsystem
		- $tooltest2_py --tool-api --testnet=1
		e $tooltest2_py --tool-api --coin=eth
		a $tooltest2_py --tool-api --coin=xmr
		a $tooltest2_py --tool-api --coin=zec
		- $tooltest2_py
		- $tooltest2_py --testnet=1
		a $tooltest2_py --coin=ltc
		a $tooltest2_py --coin=ltc --testnet=1
		a $tooltest2_py --coin=bch
		a $tooltest2_py --coin=bch --testnet=1
		a $tooltest2_py --coin=zec
		a $tooltest2_py --coin=xmr
		a $tooltest2_py --coin=dash
		e $tooltest2_py --coin=eth
		e $tooltest2_py --coin=eth --testnet=1
		e $tooltest2_py --coin=eth --token=mm1
		e $tooltest2_py --coin=eth --token=mm1 --testnet=1
		e $tooltest2_py --coin=etc
		- $tooltest2_py --fork # run once with --fork so commands are actually executed
	"
	[ "$SKIP_ALT_DEP" ] && t_tool2_skip='a e' # skip ETH,ETC: txview requires py_ecc

	d_tool="'mmgen-tool' utility (all supported coins)"
	t_tool="
		- $tooltest_py --coin=btc cryptocoin
		- $tooltest_py --coin=btc mnemonic
		a $tooltest_py --coin=ltc cryptocoin
		a $tooltest_py --coin=eth cryptocoin
		a $tooltest_py --coin=etc cryptocoin
		a $tooltest_py --coin=dash cryptocoin
		a $tooltest_py --coin=doge cryptocoin
		a $tooltest_py --coin=emc cryptocoin
		a $tooltest_py --coin=xmr cryptocoin
		a $tooltest_py --coin=zec cryptocoin
		z $tooltest_py --coin=zec --type=zcash_z cryptocoin
	"
	[ "$MSYS2" -o "$ARM32" ] && t_tool_skip='z'
	[ "$SKIP_ALT_DEP" ] && t_tool_skip='a z'

	d_gen="Bitcoin and Litecoin address generation"
	t_gen="
		- # speed tests, no verification:
		- $gentest_py --coin=btc 1 $rounds10x
		- $gentest_py --coin=btc --type=compressed 1 $rounds10x
		- $gentest_py --coin=btc --type=segwit 1 $rounds10x
		- $gentest_py --coin=btc --type=bech32 1 $rounds10x
		a $gentest_py --coin=ltc 1 $rounds10x
		a $gentest_py --coin=ltc --type=compressed 1 $rounds10x
		a $gentest_py --coin=ltc --type=segwit 1 $rounds10x
		a $gentest_py --coin=ltc --type=bech32 1 $rounds10x
		- # wallet dumps:
		- $gentest_py --type=compressed 1 $REFDIR/btcwallet.dump
		- $gentest_py --type=segwit 1 $REFDIR/btcwallet-segwit.dump
		- $gentest_py --type=bech32 1 $REFDIR/btcwallet-bech32.dump
		- $gentest_py --type=compressed --testnet=1 1 $REFDIR/btcwallet-testnet.dump
		a $gentest_py --coin=ltc --type=compressed 1 $REFDIR/litecoin/ltcwallet.dump
		a $gentest_py --coin=ltc --type=segwit 1 $REFDIR/litecoin/ltcwallet-segwit.dump
		a $gentest_py --coin=ltc --type=bech32 1 $REFDIR/litecoin/ltcwallet-bech32.dump
		a $gentest_py --coin=ltc --type=compressed --testnet=1 1 $REFDIR/litecoin/ltcwallet-testnet.dump
		- # libsecp256k1 vs python-ecdsa:
		- $gentest_py --type=legacy 1:2 $rounds100x
		- $gentest_py --type=compressed 1:2 $rounds100x
		- $gentest_py --type=segwit 1:2 $rounds100x
		- $gentest_py --type=bech32 1:2 $rounds100x
		- $gentest_py --testnet=1 1:2 $rounds100x
		- $gentest_py --testnet=1 --type=segwit 1:2 $rounds100x
		a $gentest_py --coin=ltc 1:2 $rounds100x
		a $gentest_py --coin=ltc --type=segwit 1:2 $rounds100x
		a $gentest_py --coin=ltc --testnet=1 1:2 $rounds100x
		a $gentest_py --coin=ltc --testnet=1 --type=segwit 1:2 $rounds100x
		- # all backends vs pycoin:
		- $gentest_py all:pycoin $rounds100x
	"

	[ "$SKIP_ALT_DEP" ] && t_gen_skip='a'

	true
}
