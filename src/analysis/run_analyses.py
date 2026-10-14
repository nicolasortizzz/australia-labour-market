"""Run all analysis modules in order."""

from __future__ import annotations

from src.analysis import affordability, conclusions, cost_of_living, earnings, occupations


def main() -> None:
    occupations.run()
    earnings.run()
    cost_of_living.run()
    affordability.run()
    findings = conclusions.run()
    print("Analysis complete. Key findings:")
    for k, v in findings.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
