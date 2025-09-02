<a href="https://ds500.paiml.com/rankings/llms" title="LLM Rankings" style="text-decoration: none;">
  <img src="./.github/header.svg" alt="LLM Rankings">
</a>

<h1 align="center"><a href="https://ds500.paiml.com/rankings/llms">Sonnet 4</a></h1>
<h5 align="center">Model Evaluation</h5>


This repository holds the code output of Sonnet 4, used for evaluation with [PMAT](https://github.com/paiml/paiml-mcp-agent-toolkit).

Evaluations are posted at [Pragmatic AI Labs](https://ds500.paiml.com/rankings/llms).

For details on the prompt used, check the [test.yaml](./test.yaml) file.


> [!NOTE]
> This repository does not accept Pull Requests

## How the Overall Score is Calculated

The overall score is calculated on a scale of 0-100 points using three key complexity metrics, each with a maximum penalty of 25 points:

### Scoring Components

| Component | Max Penalty | Calculation Method |
|-----------|-------------|-------------------|
| **Cognitive Complexity** | 25 points | Percentage of functions exceeding cognitive complexity thresholds |
| **Cyclomatic Complexity** | 25 points | Percentage of functions exceeding cyclomatic complexity thresholds |
| **Big-O Complexity** | 25 points | Percentage of functions with high algorithmic complexity (O(n²) or worse) |

### Final Score Formula

```
Final Score = 100 - Cognitive Penalty - Cyclomatic Penalty - Big-O Penalty
```

- **Minimum possible score**: 25/100 (when all three categories reach maximum penalty)
- **Maximum possible score**: 100/100 (when no penalties are applied)

### Penalty Calculation Details

Each penalty is calculated as:
```
Penalty = min(25, (affected_functions / total_functions) × 100)
```

- **Cognitive Complexity**: Functions with high nesting, branching, and logical complexity
- **Cyclomatic Complexity**: Functions with excessive conditional paths and decision points
- **Big-O Complexity**: Functions with O(n²), O(n³), or worse algorithmic complexity

### Evaluation Details

- Repository: This codebase
- Model: Check the ./test.yaml file for model details
- Prompt: See ./test.yaml for the original prompt used
- Results: Available at [LLM Rankings](https://ds500.paiml.com/rankings/llms)

### About the Evaluation System

The Real-World Code Score system evaluates AI-generated code across multiple dimensions to provide a comprehensive quality assessment. Unlike simple correctness checks, it analyzes real-world code quality factors that matter in
production environments.
