from datetime import datetime
import json
import sys


REPEAT = 5
BATCH_SIZE = 128

assert len(sys.argv) >= 2, "Usage: python {sys.argv[0]} [-g] model_name1 [model_name2 [...]]"
if sys.argv[1] == "-g":
    require_gpu = True
    device = "GPU"
    model_names = sys.argv[2:]
else:
    require_gpu = False
    device = "CPU"
    model_names = sys.argv[1:]

sents = [_.rstrip("\n") for _ in sys.stdin]

results = {}


print("timestamp                 ", "[msec]", "device", 'procedure description', sep="\t", file=sys.stderr)
start = datetime.now()
prev = start
print(start, 0, f"benchmark started with {len(sents)} sentences", sep="\t", file=sys.stderr)

import spacy
if require_gpu:
    spacy.require_gpu()
lap = datetime.now()
dur = int((lap - prev).total_seconds() * 1000)
print(lap, dur, device, 'import spacy', sep="\t", file=sys.stderr)
prev = lap

for model_name in model_names:
    results = {}
    nlp = spacy.load(model_name)
    lap = datetime.now()
    dur = int((lap - prev).total_seconds() * 1000)
    results[f"spacy.load()"] = [dur]
    print(lap, dur, device, f"spacy.load({model_name})", sep="\t", file=sys.stderr)
    prev = lap

    results[f"nlp.pipe(batch={BATCH_SIZE})"] = []
    for repeat in range(1, REPEAT + 1):
        for _ in range((len(sents) - 1) // BATCH_SIZE + 1):
            docs = nlp.pipe(sents[_ * BATCH_SIZE:(_ + 1) * BATCH_SIZE])
            for doc in docs:
                len(doc)
        lap = datetime.now()
        dur = int((lap - prev).total_seconds() * 1000)
        results[f"nlp.pipe(batch={BATCH_SIZE})"].append(dur / len(sents))
        print(
            lap,
            dur,
            device,
            f"#{repeat} {model_name}->nlp.pipe(batch={BATCH_SIZE}): {dur / len(sents):.03f}[msec/sent]",
            sep="\t", file=sys.stderr,
        )
        prev = lap

    results[f"nlp(batch=1)"] = []
    for repeat in range(1, REPEAT + 1):
        for sent in sents:
            doc = nlp(sent)
            len(doc)
        lap = datetime.now()
        dur = int((lap - prev).total_seconds() * 1000)
        results[f"nlp(batch=1)"].append(dur / len(sents))
        print(
            lap,
            dur,
            device,
            f"#{repeat} {model_name}->nlp(batch=1):   {dur / len(sents):.03f}[msec/sent]",
            sep="\t", file=sys.stderr,
        )
        prev = lap

    dur = int((lap - start).total_seconds() * 1000)
    print(lap, dur, device, model_name, 'finished', sep="\t", file=sys.stderr)

    for k, v in results.items():
        l = sorted(v)
        results[k] = l[len(l) // 2]

    json.dump(
        {"model": model_name, "device": device, "results": results},
        sys.stdout,
        ensure_ascii=False,
    )
    print()
