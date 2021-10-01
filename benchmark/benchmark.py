from datetime import datetime
import json
import sys


REPEAT = 5
BATCH_SIZE = 128

assert len(sys.argv) == 1 or len(sys.argv) == 2 and sys.argv[1] == "-g", "Usage: python {sys.argv[0]} {sys.argv[1]} [-g]"
require_gpu = len(sys.argv) == 2 and sys.argv[1] == "-g"
if require_gpu:
    device = "GPU"
else:
    device = "CPU"

sents = [_.rstrip("\n") for _ in sys.stdin]

results = {}


print("timestamp                 ", "[msec]", "device", 'procedure description', sep="\t", file=sys.stderr)
start = datetime.now()
prev = start
print(start, 0, f'benchmark started with {len(sents)} sentences', sep="\t", file=sys.stderr)

import spacy
if require_gpu:
    spacy.require_gpu()
lap = datetime.now()
dur = int((lap - prev).total_seconds() * 1000)
results[f"import spacy"] = [dur]
print(lap, dur, device, 'import spacy', sep="\t", file=sys.stderr)
prev = lap

nlp = spacy.load("ja_ginza")
lap = datetime.now()
dur = int((lap - prev).total_seconds() * 1000)
results[f"spacy.load('ja_ginza')"] = [dur]
print(lap, dur, device, f'spacy.load("ja_ginza")', sep="\t", file=sys.stderr)
prev = lap

results[f"ja_ginza->nlp(batch={BATCH_SIZE})"] = []
for repeat in range(1, REPEAT + 1):
    for _ in range((len(sents) - 1) // BATCH_SIZE + 1):
        doc = nlp("\n".join(sents[_ * BATCH_SIZE:(_ + 1) * BATCH_SIZE]))
    lap = datetime.now()
    dur = int((lap - prev).total_seconds() * 1000)
    results[f"ja_ginza->nlp(batch={BATCH_SIZE})"].append(dur / len(sents))
    print(
        lap,
        dur,
        device,
        f'#{repeat} ja_ginza->nlp(batch={BATCH_SIZE}): {dur / len(sents):.03f}[msec/sent]',
        sep="\t", file=sys.stderr,
    )
    prev = lap

results[f"ja_ginza->nlp(batch=1)"] = []
for repeat in range(1, REPEAT + 1):
    for sent in sents:
        doc = nlp(sent)
    lap = datetime.now()
    dur = int((lap - prev).total_seconds() * 1000)
    results[f"ja_ginza->nlp(batch=1)"].append(dur / len(sents))
    print(
        lap,
        dur,
        device,
        f'#{repeat} ja_ginza->nlp(batch=1):   {dur / len(sents):.03f}[msec/sent]',
        sep="\t", file=sys.stderr,
    )
    prev = lap

nlp = spacy.load("ja_ginza_electra")
lap = datetime.now()
dur = int((lap - prev).total_seconds() * 1000)
results[f"spacy.load('ja_ginza_electra')"] = [dur]
print(lap, dur, device, f'spacy.load("ja_ginza_electra")', sep="\t", file=sys.stderr)
prev = lap

results[f"ja_ginza_electra->nlp(batch={BATCH_SIZE})"] = []
for repeat in range(1, REPEAT + 1):
    for _ in range((len(sents) - 1) // BATCH_SIZE + 1):
        doc = nlp("\n".join(sents[_ * BATCH_SIZE:(_ + 1) * BATCH_SIZE]))
    lap = datetime.now()
    dur = int((lap - prev).total_seconds() * 1000)
    results[f"ja_ginza_electra->nlp(batch={BATCH_SIZE})"].append(dur / len(sents))
    print(
        lap,
        dur,
        device,
        f'#{repeat} ja_ginza_electra->nlp(batch={BATCH_SIZE}): {dur / len(sents):.03f}[msec/sent]',
        sep="\t", file=sys.stderr,
    )
    prev = lap

results[f"ja_ginza_electra->nlp(batch=1)"] = []
for repeat in range(1, REPEAT + 1):
    for sent in sents:
        doc = nlp(sent)
    lap = datetime.now()
    dur = int((lap - prev).total_seconds() * 1000)
    results[f"ja_ginza_electra->nlp(batch=1)"].append(dur / len(sents))
    print(
        lap,
        dur,
        device,
        f'#{repeat} ja_ginza_electra->nlp(batch=1):   {dur / len(sents):.03f}[msec/sent]',
        sep="\t", file=sys.stderr,
    )
    prev = lap

dur = int((lap - start).total_seconds() * 1000)
print(lap, dur, device, 'total', sep="\t", file=sys.stderr)

for k, v in results.items():
    l = sorted(v)
    results[k] = l[len(l) // 2]

json.dump(
    {"device": device, "results": results},
    sys.stdout,
    ensure_ascii=False,
)
print()
