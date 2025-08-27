# Sonnet 4 Model Evaluation

This repository holds the code output of GPT 5, used for evaluation with [PMAT](https://github.com/paiml/paiml-mcp-agent-toolkit).

Evaluations are posted at [Pragmatic AI Labs](https://paiml.com/models).

For details on the prompt used, check the [test.yaml](./test.yaml) file.


> [!NOTE] This repository does not accept Pull Requests

## How the Overall Score is Calculated

The overall score (0.0-1.0) is a weighted average of six key metrics:

Scoring Components

| Metric              | Weight | Description                                                                |
|---------------------|--------|----------------------------------------------------------------------------|
| Quality Score       | 25%    | Code quality analysis via https://github.com/paiml/paiml-mcp-agent-toolkit |
| Security Score      | 25%    | Security vulnerability detection (fewer issues = higher score)             |
| Complexity Score    | 20%    | Code complexity analysis (lower complexity = higher score)                 |
| Performance Score   | 15%    | Algorithmic efficiency and performance patterns                            |
| Documentation Score | 10%    | Code documentation quality and completeness                                |
| Test Coverage       | 5%     | Test coverage estimation (if tests are present)                            |

### Grading Scale

The numeric score is converted to a letter grade:

| Grade | Score Range | Percentage |
|-------|-------------|------------|
| A+    | 0.97-1.00   | 97-100%    |
| A     | 0.93-0.96   | 93-96%     |
| A-    | 0.90-0.92   | 90-92%     |
| B+    | 0.87-0.89   | 87-89%     |
| B     | 0.83-0.86   | 83-86%     |
| B-    | 0.80-0.82   | 80-82%     |
| C+    | 0.77-0.79   | 77-79%     |
| C     | 0.73-0.76   | 73-76%     |
| C-    | 0.70-0.72   | 70-72%     |
| D     | 0.60-0.69   | 60-69%     |
| F     | 0.00-0.59   | Below 60%  |

### What Makes a Perfect Score?

To achieve a 1.0 (100%) score, code must excel in all areas:

- ✅ Perfect code quality - Clean, well-structured, maintainable code
- ✅ Zero security issues - No vulnerabilities or security anti-patterns
- ✅ Optimal complexity - Low cyclomatic complexity, minimal nesting, no duplication
- ✅ High performance - Efficient algorithms and optimal time/space complexity
- ✅ Excellent documentation - Comprehensive comments and documentation
- ✅ Good test coverage - Adequate testing if applicable

### Evaluation Details

- Repository: This codebase
- Model: Check the ./test.yaml file for model details
- Prompt: See ./test.yaml for the original prompt used
- Results: Available at https://paiml.com/models

### About the Evaluation System

The Real-World Code Score system evaluates AI-generated code across multiple dimensions to provide a comprehensive quality assessment. Unlike simple correctness checks, it analyzes real-world code quality factors that matter in
production environments.
