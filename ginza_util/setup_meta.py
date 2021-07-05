import json
import sys


with open(sys.argv[1], "r") as fin:
  master = json.load(fin)

with open(sys.argv[2], "r") as fin:
  target = json.load(fin)

target.update(master)

json.dump(target, sys.stdout, indent=1, ensure_ascii=False)

