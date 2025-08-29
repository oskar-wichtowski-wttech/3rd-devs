# Research Task Solution

This solution helps you complete the research task by fine-tuning a language model to detect anomalies in sensor data.

## Overview

The task involves:
1. Preparing training data from correct and incorrect samples
2. Fine-tuning an OpenAI model
3. Using the fine-tuned model to validate new data
4. Submitting results to the central

## Files

- `main.py` - Main solution script
- `requirements.txt` - Python dependencies
- `lab_data/` - Contains the data files:
  - `correct.txt` - Valid sensor readings
  - `incorect.txt` - Invalid sensor readings  
  - `verify.txt` - Data to validate

## Step-by-Step Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Training Data

```bash
python main.py
```

This creates `training_data.jsonl` with the format required for OpenAI fine-tuning.

### 3. Fine-tune Model

1. Go to [OpenAI Fine-tuning Panel](https://platform.openai.com/finetune/)
2. Click "Create"
3. Select "Supervised" method
4. Choose base model: `gpt-4o-mini-2024-07-18` or `gpt-4.1-mini-2025-04-14`
5. Upload `training_data.jsonl` as training data
6. Set validation data to "None"
7. Choose a suffix for your model name
8. Start training

**Training takes 30 minutes to 2 hours.**

### 4. Validate Data

After training completes, get your model name and run:

```bash
python main.py --validate --api-key YOUR_OPENAI_API_KEY --model YOUR_MODEL_NAME
```

This will classify each sample in `verify.txt` and show which are correct.

### 5. Submit Results

Submit the correct IDs to the central:

```bash
python main.py --submit --api-key YOUR_API_KEY --correct-ids 01,03,08,09
```

Replace the IDs with the actual correct ones from step 4.

## Expected Output Format

The central expects:
```json
{
  "task": "research",
  "apikey": "YOUR_API_KEY",
  "answer": ["01", "03", "08", "09"]
}
```

## Notes

- Fine-tuning may not work perfectly on first try due to LLM non-determinism
- Ensure you use the exact same message format as in training data
- Submit only to `https://c3ntrala.ag3nts.org/report` (with "3" in the URL)
- Only submit the two-digit IDs of correct samples

