#!/usr/bin/env python3

import sys
from mmgen.bip39 import bip39

words = bip39().get_wordlist()
print('Reading file ', sys.argv[1])
with open(sys.argv[1], 'r') as file:
  mn = file.readline().split()
  for m in mn:
    print(hex(words.index(m)))

