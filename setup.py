#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

# MSYS2 Note (2023-10-26):
#   mingw-w64-ucrt-x86_64-python package is missing static lib, so we must build dynamic extmod
#   linked to installed libsecp256k1

import os,platform
from pathlib import Path
from subprocess import run,PIPE
from setuptools import setup,Extension
from setuptools.command.build_ext import build_ext

have_arm   = platform.uname().machine in ('aarch64','armv7l') # x86_64 (linux), AMD64 (win), aarch64, armv7l
have_msys2 = platform.system() == 'Windows'

home = Path(os.environ['HOME'])

cache_path = home.joinpath('.cache','mmgen')
src_path   = home.joinpath('.cache','mmgen','secp256k1')

if have_msys2:
	root = Path().resolve().anchor
	installed_lib_file = Path(root, 'msys64', 'ucrt64', 'lib', 'libsecp256k1.dll.a')
	lib_file = src_path.joinpath('.libs', 'libsecp256k1.dll.a')
else:
	installed_lib_file = None
	lib_file = src_path.joinpath('.libs', 'libsecp256k1.a')

def build_libsecp256k1():

	if installed_lib_file and installed_lib_file.exists(): # see ‘MSYS2 Note’ above
		return

	def fix_broken_aclocal_path():
		os.environ['ACLOCAL_PATH'] = '/C/msys64/ucrt64/share/aclocal:/C/msys64/usr/share/aclocal'

	if have_msys2:
		fix_broken_aclocal_path()

	if not cache_path.exists():
		cache_path.mkdir(parents=True)

	if not src_path.exists():
		print('\nCloning libsecp256k1')
		run(['git','clone','https://github.com/bitcoin-core/secp256k1.git'],check=True,cwd=cache_path)

	if not lib_file.exists():
		print(f'\nBuilding libsecp256k1 (cwd={str(src_path)})')
		cmds = {
			'Windows': (
				['sh','./autogen.sh'],
				['sh','./configure','CFLAGS=-g -O2 -fPIC','--disable-dependency-tracking'],
				['mingw32-make','MAKE=mingw32-make']
			),
			'Linux': (
				['./autogen.sh'],
				['./configure','CFLAGS=-g -O2 -fPIC'],
				['make'] + ([] if have_arm else ['-j4']),
			),
		}[platform.system()]
		for cmd in cmds:
			print('Executing {}'.format(' '.join(cmd)))
			run(cmd,check=True,cwd=src_path)

	if installed_lib_file and not installed_lib_file.exists(): # see ‘MSYS2 Note’ above
		run(['mingw32-make','install','MAKE=mingw32-make'],check=True,cwd=src_path)

class my_build_ext(build_ext):
	def build_extension(self,ext):
		build_libsecp256k1()
		build_ext.build_extension(self,ext)

setup(
	cmdclass = { 'build_ext': my_build_ext },
	ext_modules = [Extension(
		name               = 'mmgen.proto.secp256k1.secp256k1',
		sources            = ['extmod/secp256k1mod.c'],
		libraries          = ['gmp'] if have_msys2 else [],
		include_dirs       = [str(src_path.joinpath('include'))],
		extra_objects      = [str(lib_file)],
		extra_compile_args = ['-shared'] if have_msys2 else [],
		extra_link_args    = ['-shared'] if have_msys2 else [],
	)]
)
