# Fine-tuning Awareness

## Full Fine-tuning
**What:** Update all model weights using a dataset.

**When it makes sense:**
- Task is stable and won’t change often
- Large, high-quality dataset exists
- Prompting alone fails to give consistency

**Problems:**
- Very expensive
- Slow to iterate
- Risk of overfitting

## LoRA (Low-Rank Adaptation)
**What:** Train small adapter layers while keeping base model frozen.

**Why it is cost-efficient:**
- Very few parameters trained
- Faster training
- Easy rollback
- Multiple adapters possible

**When to use:**
- Need customization without full cost
- Rapid experimentation

## QLoRA
**What:** Quantize base model + apply LoRA.

**Why cheaper:**
- Much lower memory usage
- Works on smaller GPUs

**Tradeoff:**
- Slight quality drop possible

## Project decision
This project uses **retrieval + prompting first**.
Fine-tuning is only considered if repeated failures occur.

