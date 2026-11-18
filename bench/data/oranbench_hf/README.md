---
license: mit
task_categories:
- question-answering
language:
- en
tags:
- benchmark
- telecommunications
- o-ran
- llm-evaluation
size_categories:
- 1K<n<10K
---

# ORANBench: A Streamlined Benchmark for Assessing LLMs in O-RAN

## Overview

**ORANBench** is a streamlined evaluation dataset derived from **ORAN-Bench-13K**, designed to efficiently assess Large Language Models (LLMs) in the context of Open Radio Access Networks (O-RAN). This benchmark consists of **1,500** multiple-choice questions, with 500 questions randomly sampled from each of three difficulty levels: easy, intermediate, and difficult.

This dataset is part of the **ORANSight-2.0** work, which introduces foundational LLMs for O-RAN. ORANBench retains the diversity and rigor of the original ORAN-Bench-13K benchmark while reducing computational overhead, enabling efficient evaluation of LLMs on O-RAN-specific tasks.

**Note:** The full ORAN-Bench-13K benchmark, containing 13,952 questions across all difficulty levels, is available on GitHub: [https://github.com/prnshv/ORAN-Bench-13K](https://github.com/prnshv/ORAN-Bench-13K)

## Dataset Format

Each question is represented in JSON format, comprising the following fields:

* **question**: A string presenting the question about O-RAN concepts, specifications, or implementations.
* **choices**: An array of four strings representing the answer options.
* **answer**: An integer (0-based index) indicating the correct answer from the choices array.
* **difficulty**: A string indicating the difficulty level: "easy", "medium", or "hard".

## Dataset Instance

An example from the dataset:

```json
{
  "question": "Which O-RAN Working Group focuses on the architecture description of Open Radio Access Networks?",
  "choices": [
    "1. O-RAN.WG3",
    "2. O-RAN.WG4",
    "3. O-RAN.WG1",
    "4. O-RAN.WG5"
  ],
  "answer": 2,
  "difficulty": "easy"
}
```

## Difficulty Levels

* **Easy**: Questions focus on basic concepts and known facts about O-RAN.
* **Medium**: Questions require comprehension and application of concepts or involve moderate calculations or reasoning.
* **Hard**: Questions demand a deep understanding of O-RAN standards or the ability to synthesize multiple pieces of information.

## Motivation

The rapid advancement of O-RAN technology necessitates the development of sophisticated and intelligent systems capable of managing complex tasks within these networks. Large Language Models have shown significant promise in various domains but require thorough evaluation within the specific context of O-RAN. ORANBench provides an efficient and balanced benchmark to evaluate LLMs' capabilities in this critical domain.

## Usage

### Loading the Dataset

You can load the dataset using the Hugging Face `datasets` library:

```python
from datasets import load_dataset

dataset = load_dataset("prnshv/ORANBench")
```

Or load directly from the JSON file:

```python
import json

with open('ORANBench_NextGlab.json', 'r') as f:
    data = json.load(f)
```

### Evaluation Example

```python
from datasets import load_dataset

dataset = load_dataset("prnshv/ORANBench")
questions = dataset['train']  # or appropriate split

# Example: Evaluate a model's answer
for item in questions:
    question = item['question']
    choices = item['choices']
    correct_answer_idx = item['answer']
    difficulty = item['difficulty']
    
    # Your model evaluation logic here
    model_answer_idx = your_model.predict(question, choices)
    is_correct = (model_answer_idx == correct_answer_idx)
```

### Filtering by Difficulty

```python
from datasets import load_dataset

dataset = load_dataset("prnshv/ORANBench")
questions = dataset['train']

# Filter by difficulty
easy_questions = [q for q in questions if q['difficulty'] == 'easy']
medium_questions = [q for q in questions if q['difficulty'] == 'medium']
hard_questions = [q for q in questions if q['difficulty'] == 'hard']
```

## Citation

If you use this dataset in your research, please cite both works:

### ORANSight-2.0 (Primary Citation)

```bibtex
@ARTICLE{11096935,
  author={Gajjar, Pranshav and Shah, Vijay K.},
  journal={IEEE Transactions on Machine Learning in Communications and Networking}, 
  title={ORANSight-2.0: Foundational LLMs for O-RAN}, 
  year={2025},
  volume={3},
  number={},
  pages={903-920},
  doi={10.1109/TMLCN.2025.3592658}
}
```

### ORAN-Bench-13K (Framework Foundation)

```bibtex
@misc{gajjar2024oranbench13kopensourcebenchmark,
  title={ORAN-Bench-13K: An Open Source Benchmark for Assessing LLMs in Open Radio Access Networks}, 
  author={Pranshav Gajjar and Vijay K. Shah},
  year={2024},
  eprint={2407.06245},
  archivePrefix={arXiv},
  primaryClass={cs.NI},
  url={https://arxiv.org/abs/2407.06245}
}
```

## Full Benchmark

For the complete benchmark with all 13,952 questions, please refer to:
- **GitHub Repository**: [https://github.com/prnshv/ORAN-Bench-13K](https://github.com/prnshv/ORAN-Bench-13K)

## License

This dataset is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.

## Repository

- **Hugging Face**: [https://huggingface.co/datasets/prnshv/ORANBench](https://huggingface.co/datasets/prnshv/ORANBench)
- **Full Benchmark (GitHub)**: [https://github.com/prnshv/ORAN-Bench-13K](https://github.com/prnshv/ORAN-Bench-13K)

## Contact

For questions, suggestions, or contributions, please reach out through the GitHub repository.
