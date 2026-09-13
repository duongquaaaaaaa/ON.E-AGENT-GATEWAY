import json
scores = json.load(open('data/scores.json'))
for s in sorted(scores, key=lambda x: -x['overall_score']):
    print(f"{s['product_name'][:42]:42s}  {s['overall_score']:5.1f}  {s['tier']}")
