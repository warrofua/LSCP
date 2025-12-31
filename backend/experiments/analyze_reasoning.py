"""Analyze reasoning traces from ablation study"""
import json
import sys

with open('/Users/joshuafarrow/Projects/LSCP/data/experiments/prompt_ablation_20251228_171611.json') as f:
    data = json.load(f)

print("=" * 80)
print("REASONING TRACE ANALYSIS")
print("=" * 80)

# Show one example in detail
pair = data['concept_pairs'][0]  # love ↔ addiction
print(f"\n### EXAMPLE: {pair['concept_a'].upper()} ↔ {pair['concept_b'].upper()} ###\n")

for variant in ['neutral', 'current']:
    reasoning = pair['responses'][variant]['reasoning']
    print(f"\n{variant.upper()} PROMPT - First 400 chars:")
    print("-" * 60)
    print(reasoning[:400] + "...")

print("\n\n" + "=" * 80)
print("COMPUTATIONAL LANGUAGE DENSITY ANALYSIS")
print("=" * 80)

# Extended keyword list
comp_keywords = [
    'computational', 'algorithm', 'function', 'processing', 'mechanism',
    'system', 'state', 'model', 'pattern', 'optimization', 'reinforcement',
    'signal', 'feedback', 'entropy', 'information', 'vector', 'latent',
    'neural', 'dopamine', 'reward', 'prediction', 'policy', 'valuation',
    'learning', 'training', 'embedding', 'representation', 'activation'
]

results = {}
for variant in ['neutral', 'current', 'hybrid']:
    all_reasoning = ' '.join([
        pair['responses'][variant]['reasoning']
        for pair in data['concept_pairs']
    ]).lower()

    words = all_reasoning.split()
    comp_count = sum(1 for word in words if any(kw in word for kw in comp_keywords))

    results[variant] = {
        'total_words': len(words),
        'comp_words': comp_count,
        'pct': (comp_count / len(words) * 100) if words else 0
    }

for variant in ['neutral', 'current', 'hybrid']:
    r = results[variant]
    print(f"\n{variant.upper()}:")
    print(f"  Total words: {r['total_words']}")
    print(f"  Computational words: {r['comp_words']}")
    print(f"  Density: {r['pct']:.2f}%")

print("\n" + "=" * 80)
print("VERDICT")
print("=" * 80)

neutral_pct = results['neutral']['pct']
current_pct = results['current']['pct']
increase = current_pct - neutral_pct

print(f"\nNeutral prompt: {neutral_pct:.2f}% computational language")
print(f"Current prompt: {current_pct:.2f}% computational language")
print(f"Increase: +{increase:.2f}%")

if neutral_pct > 5:
    print("\n✓ COMPUTATIONAL BIAS IS INNATE")
    print(f"  Even without prompting, {neutral_pct:.1f}% of reasoning uses")
    print("  computational/neuroscience terminology, suggesting this is")
    print("  the model's natural conceptual framework.")
else:
    print("\n✗ COMPUTATIONAL BIAS IS INDUCED")
    print(f"  Only {neutral_pct:.1f}% computational language with neutral prompt.")
    print("  The bias is primarily driven by prompt engineering.")

print("\n" + "=" * 80)
