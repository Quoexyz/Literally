import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torch_xla.core.xla_model as xm
import torch_xla.distributed.xla_multiprocessing as xmp
import torch_xla.distributed.parallel_loader as pl

from transformers import AutoTokenizer, AutoModelForCausalLM, get_linear_schedule_with_warmup
MODEL_ID = "/kaggle/input/models/google/gemma-3/transformers/gemma-3-270m-it/1"     
DATA_PATH = "/kaggle/input/datasets/timwang123/gemma3-distill-train/gemma3_distill_train.jsonl"     
SAVE_DIR = "./gemma3_translation_tpu_checkpoints"
MAX_LENGTH = 256                                   
BATCH_SIZE = 16                                   
EPOCHS = 3                                        
LEARNING_RATE = 2e-5
class DistillDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_length=256):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.data.append(json.loads(line))
    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        english_text = item["en"]
        chinese_text = item["zh"]
        
        prompt = f"<start_of_turn>user\nTranslate the following English text into Chinese.\nInput: {english_text}<end_of_turn>\n<start_of_turn>model\n"
        full_text = prompt + chinese_text + self.tokenizer.eos_token
        
        encodings = self.tokenizer(full_text, max_length=self.max_length, padding="max_length", truncation=True, return_tensors="pt")
        
        input_ids = encodings["input_ids"].squeeze(0)
        attention_mask = encodings["attention_mask"].squeeze(0)
        
        prompt_encodings = self.tokenizer(prompt, add_special_tokens=True, return_tensors="pt")
        prompt_len = prompt_encodings["input_ids"].size(1)
        
        labels = input_ids.clone()
        labels[:min(prompt_len, self.max_length)] = -100
        labels[attention_mask == 0] = -100
        
        return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}
def train_single_tpu_core(index):
    device = xm.xla_device()
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, 
    torch_dtype=torch.bfloat16, 
    local_files_only=True,
    use_cache=False
)
    model.to(device)
    dataset = DistillDataset(DATA_PATH, tokenizer, MAX_LENGTH)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    total_steps = len(dataloader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(optimizer, int(total_steps * 0.03), total_steps)

    for epoch in range(EPOCHS):
        model.train()
        tpu_loader = pl.ParallelLoader(dataloader, [device]).per_device_loader(device)
        
        for step, batch in enumerate(tpu_loader):
            optimizer.zero_grad()
            outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
            loss = outputs.loss
            loss.backward()
            
            xm.optimizer_step(optimizer)
            scheduler.step()
            
            if step % 50 == 0:
                print(f"Epoch [{epoch+1}/{EPOCHS}] | Step {step}/{len(dataloader)} | Loss: {loss.item():.4f}")
        
        epoch_save_dir = os.path.join(SAVE_DIR, f"epoch_{epoch+1}")
        os.makedirs(epoch_save_dir, exist_ok=True)
        tokenizer.save_pretrained(epoch_save_dir)
        xm.save(model.state_dict(), os.path.join(epoch_save_dir, "pytorch_model.bin"))

    print(f"\n🎉 Done。")

if __name__ == "__main__":
    os.makedirs(SAVE_DIR, exist_ok=True)
    xmp.spawn(train_single_tpu_core, args=(), nprocs=1, start_method='fork')
