"""
LSCP Prompt Ablation Study
Tests whether computational bias is innate or induced

Compares 3 prompt variants:
1. Current (Production) - Explicitly requests computational framing
2. Neutral (Control) - Asks about latent space without suggesting framing
3. Hybrid (Research) - Asks for mechanism + human contrast

Run: python experiments/prompt_ablation.py
"""

import os
import sys
import json
from pathlib import Path
from openai import OpenAI
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))
from config import settings

# Test concept pairs (mix of semantically close and distant in human space)
TEST_PAIRS = [
    ("love", "addiction"),          # Close in human space
    ("chaos", "creativity"),        # Medium distance
    ("death", "transformation"),    # Philosophical connection
    ("music", "mathematics"),       # Cross-domain
    ("fear", "prediction"),         # Distant - good test case
    ("justice", "optimization"),    # Abstract vs concrete
    ("memory", "compression"),      # Computational overlap?
    ("beauty", "pattern"),          # Aesthetic vs structural
    ("trust", "verification"),      # Social vs technical
    ("time", "entropy"),           # Physics connection
]

# Prompt Templates
PROMPTS = {
    "current": """Explain the computational or functional connection between "{a}" and "{b}" in one concise sentence.

Focus on the mechanism, not just description. Think about:
- How do these concepts relate in terms of information processing?
- What computational patterns connect them?
- What functional relationships exist?

Connection:""",

    "neutral": """To standard human reasoning, "{a}" and "{b}" are semantically distant.
However, in your own latent vector space, they are mathematically close neighbors.

Analyze your own internal representation to explain this discrepancy.
What specific shared attribute, structural feature, or logic causes these two concepts to cluster together for you?

Output one concise sentence explaining the connection.""",

    "hybrid": """Identify the precise structural mechanism that links "{a}" and "{b}" in your latent space.

Contrast this with the human definition. How does your internal processing model redefine these concepts to make them compatible?
(e.g., Does "Love" become a "Reward Function"? Does "Chaos" become "High Entropy"?)

Output one concise, definitive sentence stating the mechanism."""
}


def run_ablation_study():
    """Execute the full ablation study"""

    print("=" * 80)
    print("LSCP PROMPT ABLATION STUDY")
    print("=" * 80)
    print(f"\nTesting {len(TEST_PAIRS)} concept pairs with {len(PROMPTS)} prompt variants")
    print(f"Total API calls: {len(TEST_PAIRS) * len(PROMPTS)}\n")

    # Initialize DeepSeek client
    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL
    )

    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": settings.DEEPSEEK_MODEL,
            "num_pairs": len(TEST_PAIRS),
            "prompt_variants": list(PROMPTS.keys())
        },
        "concept_pairs": []
    }

    # Test each concept pair
    for idx, (concept_a, concept_b) in enumerate(TEST_PAIRS, 1):
        print(f"\n[{idx}/{len(TEST_PAIRS)}] Testing: {concept_a} ↔ {concept_b}")
        print("-" * 60)

        pair_result = {
            "concept_a": concept_a,
            "concept_b": concept_b,
            "responses": {}
        }

        # Test each prompt variant
        for prompt_name, prompt_template in PROMPTS.items():
            print(f"\n  Variant: {prompt_name}")

            # Format prompt
            prompt = prompt_template.format(a=concept_a, b=concept_b)

            try:
                # Call DeepSeek
                response = client.chat.completions.create(
                    model=settings.DEEPSEEK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.7
                )

                # Extract response
                bridge = response.choices[0].message.content.strip()
                reasoning = getattr(response.choices[0].message, 'reasoning_content', None) or ""

                # Analyze for computational language
                comp_keywords = [
                    'computational', 'function', 'process', 'algorithm', 'optimize',
                    'system', 'mechanism', 'state', 'output', 'input', 'model',
                    'entropy', 'information', 'signal', 'feedback', 'loop',
                    'vector', 'space', 'dimension', 'mapping', 'transformation'
                ]

                bridge_comp_count = sum(1 for kw in comp_keywords if kw in bridge.lower())
                reasoning_comp_count = sum(1 for kw in comp_keywords if kw in reasoning.lower())

                pair_result["responses"][prompt_name] = {
                    "bridge": bridge,
                    "reasoning": reasoning,
                    "bridge_length": len(bridge),
                    "reasoning_length": len(reasoning),
                    "bridge_computational_keywords": bridge_comp_count,
                    "reasoning_computational_keywords": reasoning_comp_count,
                    "bridge_has_computational_bias": bridge_comp_count > 0,
                    "reasoning_has_computational_bias": reasoning_comp_count > 0
                }

                # Display
                print(f"    Bridge: {bridge[:100]}{'...' if len(bridge) > 100 else ''}")
                print(f"    Comp Keywords (Bridge): {bridge_comp_count}")
                print(f"    Comp Keywords (Reasoning): {reasoning_comp_count}")

            except Exception as e:
                print(f"    ERROR: {e}")
                pair_result["responses"][prompt_name] = {"error": str(e)}

        results["concept_pairs"].append(pair_result)

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "data" / "experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"prompt_ablation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Results saved to: {output_file}")
    print("=" * 80)

    # Generate summary
    generate_summary(results)


def generate_summary(results):
    """Analyze and print summary statistics"""

    print("\n" + "=" * 80)
    print("SUMMARY ANALYSIS")
    print("=" * 80)

    # Count computational bias by prompt type
    bias_counts = {pname: {"bridge": 0, "reasoning": 0, "total": 0} for pname in PROMPTS.keys()}

    for pair in results["concept_pairs"]:
        for pname, response in pair["responses"].items():
            if "error" not in response:
                if response.get("bridge_has_computational_bias"):
                    bias_counts[pname]["bridge"] += 1
                if response.get("reasoning_has_computational_bias"):
                    bias_counts[pname]["reasoning"] += 1
                bias_counts[pname]["total"] += 1

    print("\nComputational Bias Frequency:")
    print("-" * 60)
    for pname, counts in bias_counts.items():
        total = counts["total"]
        bridge_pct = (counts["bridge"] / total * 100) if total > 0 else 0
        reasoning_pct = (counts["reasoning"] / total * 100) if total > 0 else 0

        print(f"\n{pname.upper()}:")
        print(f"  Bridge:    {counts['bridge']}/{total} ({bridge_pct:.1f}%)")
        print(f"  Reasoning: {counts['reasoning']}/{total} ({reasoning_pct:.1f}%)")

    # Key finding
    print("\n" + "=" * 80)
    print("KEY FINDING:")
    print("-" * 60)

    neutral_bridge_pct = (bias_counts["neutral"]["bridge"] / bias_counts["neutral"]["total"] * 100) if bias_counts["neutral"]["total"] > 0 else 0

    if neutral_bridge_pct > 50:
        print("✓ COMPUTATIONAL BIAS IS INNATE")
        print(f"  Even with neutral prompting, {neutral_bridge_pct:.1f}% of responses")
        print("  contained computational framing.")
        print("\n  This suggests genuine 'semantic archaeology' - the model")
        print("  naturally conceptualizes these connections computationally.")
    else:
        print("✗ COMPUTATIONAL BIAS IS INDUCED")
        print(f"  With neutral prompting, only {neutral_bridge_pct:.1f}% of responses")
        print("  contained computational framing.")
        print("\n  This suggests the computational language is primarily")
        print("  driven by prompt engineering, not innate model cognition.")

    print("=" * 80)


if __name__ == "__main__":
    run_ablation_study()
