import threading
import tkinter as tk
from tkinter import filedialog
from queue import Queue, Empty
import os

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
)
import customtkinter as ctk

device = torch.device("cpu")
model = None
tokenizer = None
model_loading = False

def load_model(model_path):
    global model, tokenizer, model_loading
    if model_loading:
        return
    model_loading = True
    disable_ui(True)
    status_var.set("Loading model...")

    def _load():
        global model, tokenizer, model_loading
        try:
            print(f"Loading tokenizer from {model_path}...")
            tok = AutoTokenizer.from_pretrained(model_path)
            print(f"Loading model from {model_path}...")
            m = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
            )
            m.to(device)
            m.eval()
            tokenizer = tok
            model = m
            root.after(0, _on_model_loaded, model_path)
        except Exception as e:
            root.after(0, _on_model_load_error, str(e))
        finally:
            model_loading = False
            root.after(0, disable_ui, False)

    threading.Thread(target=_load, daemon=True).start()

def _on_model_loaded(path):
    model_path_var.set(path)
    model_name_label.configure(text=f"✓ {os.path.basename(path)}")
    status_var.set("Ready")

def _on_model_load_error(err):
    model_name_label.configure(text="✗ Load failed")
    status_var.set(f"Error: {err[:60]}")

def disable_ui(disabled):
    state = "disabled" if disabled else "normal"
    translate_btn.configure(state=state)
    stop_btn.configure(state="disabled")
    clear_btn.configure(state=state)
    browse_btn.configure(state=state)
    input_box.configure(state="normal" if not disabled else "disabled")
def browse_model():
    path = filedialog.askdirectory(title="Select Model Directory")
    if path:
        threading.Thread(target=load_model, args=(path,), daemon=True).start()

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Literally")
root.geometry("900x750")
root.minsize(750, 600)
root.configure(fg_color="#F5F5F7")

main_card = ctk.CTkFrame(root, corner_radius=20, fg_color="white", border_width=0)
main_card.pack(fill="both", expand=True, padx=25, pady=25)

title = ctk.CTkLabel(
    main_card, text="Literally  ·  English → Chinese",
    font=ctk.CTkFont(size=22, weight="bold"), text_color="#1E1E2E",
)
title.pack(anchor="w", padx=25, pady=(20, 10))

model_frame = ctk.CTkFrame(main_card, fg_color="transparent")
model_frame.pack(fill="x", padx=25, pady=(0, 10))

model_path_var = tk.StringVar(value="No model loaded")

model_label = ctk.CTkLabel(
    model_frame, text="Model:",
    font=ctk.CTkFont(size=12, weight="bold"), text_color="#4A4A5A",
)
model_label.pack(side="left", padx=(0, 8))

model_entry = ctk.CTkEntry(
    model_frame, textvariable=model_path_var, font=ctk.CTkFont(size=12),
    state="readonly", fg_color="#F0F2F5", border_color="#D1D5DB",
    corner_radius=8, width=400,
)
model_entry.pack(side="left", padx=(0, 8))

browse_btn = ctk.CTkButton(
    model_frame, text="Browse...", width=80, height=32,
    corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"),
    fg_color="#2563EB", hover_color="#1D4ED8", command=browse_model,
)
browse_btn.pack(side="left", padx=(0, 10))

model_name_label = ctk.CTkLabel(
    model_frame, text="", font=ctk.CTkFont(size=11), text_color="#6B7280",
)
model_name_label.pack(side="left")

# 分割线
separator = ctk.CTkFrame(main_card, height=1, fg_color="#E5E7EB")
separator.pack(fill="x", padx=25, pady=(0, 15))

input_label = ctk.CTkLabel(
    main_card, text="ENGLISH",
    font=ctk.CTkFont(size=11, weight="bold"), text_color="#6B7280",
)
input_label.pack(anchor="w", padx=25, pady=(0, 5))

input_box = ctk.CTkTextbox(
    main_card, height=120, corner_radius=10, border_width=1.5,
    border_color="#D1D5DB", fg_color="#F9FAFB",
    font=ctk.CTkFont(family="Cascadia Code", size=12), text_color="#111827", wrap="word",
)
input_box.pack(fill="x", padx=25, pady=(0, 8))

def focus_in(event):
    input_box.configure(border_color="#3B82F6")
def focus_out(event):
    input_box.configure(border_color="#D1D5DB")
input_box.bind("<FocusIn>", focus_in)
input_box.bind("<FocusOut>", focus_out)

btn_frame = ctk.CTkFrame(main_card, fg_color="transparent")
btn_frame.pack(pady=(0, 8))

translate_btn = ctk.CTkButton(
    btn_frame, text="Translate", width=130, height=36,
    corner_radius=10, font=ctk.CTkFont(size=13, weight="bold"),
    fg_color="#2563EB", hover_color="#1D4ED8", command=None,
)
translate_btn.pack(side="left", padx=6)

stop_btn = ctk.CTkButton(
    btn_frame, text="Stop", width=100, height=36,
    corner_radius=10, font=ctk.CTkFont(size=13, weight="bold"),
    fg_color="#EF4444", hover_color="#DC2626",
    state="disabled", command=None,
)
stop_btn.pack(side="left", padx=6)

clear_btn = ctk.CTkButton(
    btn_frame, text="Clear", width=100, height=36,
    corner_radius=10, font=ctk.CTkFont(size=13),
    fg_color="#9CA3AF", hover_color="#6B7280", command=None,
)
clear_btn.pack(side="left", padx=6)

status_var = tk.StringVar(value="Ready")
status_label = ctk.CTkLabel(
    main_card, textvariable=status_var,
    font=ctk.CTkFont(size=12), text_color="#6B7280",
)
status_label.pack(pady=(2, 8))

output_label = ctk.CTkLabel(
    main_card, text="CHINESE",
    font=ctk.CTkFont(size=11, weight="bold"), text_color="#6B7280",
)
output_label.pack(anchor="w", padx=25, pady=(0, 5))

output_box = ctk.CTkTextbox(
    main_card, height=140, corner_radius=10, border_width=1.5,
    border_color="#D1D5DB", fg_color="#F9FAFB",
    font=ctk.CTkFont(family="Microsoft YaHei", size=12), text_color="#111827",
    wrap="word", state="disabled",
)
output_box.pack(fill="both", expand=True, padx=25, pady=(0, 20))

stop_event = threading.Event()
token_queue = Queue()

def translate():
    global model, tokenizer
    if model is None or tokenizer is None:
        status_var.set("No model loaded")
        return
    text = input_box.get("1.0", "end-1c").strip()
    if not text:
        return

    translate_btn.configure(state="disabled")
    stop_btn.configure(state="normal")
    status_var.set("Translating...")
    stop_event.clear()

    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.configure(state="disabled")

    prompt = (
        "<start_of_turn>user\n"
        "Translate the following English text into Chinese.\n"
        f"Input: {text}"
        "<end_of_turn>\n"
        "<start_of_turn>model\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt")
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    generation_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=256,
        do_sample=False,
        temperature=0.0,
        repetition_penalty=1.05,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    def generate():
        with torch.inference_mode():
            model.generate(**generation_kwargs)

    threading.Thread(target=generate, daemon=True).start()

    def read_stream():
        for token in streamer:
            if stop_event.is_set():
                break
            token_queue.put(token)
        token_queue.put(None)

    threading.Thread(target=read_stream, daemon=True).start()

    def update_gui():
        try:
            while True:
                token = token_queue.get_nowait()
                if token is None or stop_event.is_set():
                    translate_btn.configure(state="normal")
                    stop_btn.configure(state="disabled")
                    status_var.set("Ready" if not stop_event.is_set() else "Stopped")
                    stop_event.clear()
                    return
                output_box.configure(state="normal")
                output_box.insert("end", token)
                output_box.see("end")
                output_box.configure(state="disabled")
        except Empty:
            pass
        root.after(30, update_gui)

    update_gui()

def stop_translation():
    stop_event.set()
    translate_btn.configure(state="normal")
    stop_btn.configure(state="disabled")
    status_var.set("Stopped")

def clear():
    input_box.delete("1.0", "end")
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.configure(state="disabled")
    status_var.set("Ready")

translate_btn.configure(command=lambda: threading.Thread(target=translate, daemon=True).start())
stop_btn.configure(command=stop_translation)
clear_btn.configure(command=clear)

def ctrl_enter(event):
    threading.Thread(target=translate, daemon=True).start()
input_box.bind("<Control-Return>", ctrl_enter)

root.mainloop()
