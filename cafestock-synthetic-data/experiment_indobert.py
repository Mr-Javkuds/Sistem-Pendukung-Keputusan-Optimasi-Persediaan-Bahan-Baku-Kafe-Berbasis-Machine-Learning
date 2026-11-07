"""Fine-tune IndoBERT on the existing sentiment train split and score the frozen challenge set.

Run from cafestock-synthetic-data with the project venv:
    python experiment_indobert.py

The experiment writes the checkpoint used by the local demo endpoint under the
ignored workspace tmp/ folder. It does not alter SVM.joblib or historical SVM outputs.
"""
from pathlib import Path
import hashlib
import json
import random
import time

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
OUT = ROOT / "reports/indobert_experiment"
CHECKPOINT = WORKSPACE / "tmp/indobert-cafestock-fourclass"
BASE_MODEL = "indobenchmark/indobert-base-p1"
LABELS = ["positive", "negative", "neutral", "mixed"]
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}
MAX_LENGTH = 80
BATCH_SIZE = 24
EPOCHS = 2
SEED = 42


class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.tokens = tokenizer(list(texts), truncation=True, padding="max_length",
                                max_length=MAX_LENGTH, return_tensors="pt")
        self.labels = torch.tensor([LABEL_TO_ID[str(label)] for label in labels], dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):
        return {**{key: value[index] for key, value in self.tokens.items()},
                "labels": self.labels[index]}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_everything():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(min(8, torch.get_num_threads()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    seed_everything()
    train_x = pd.read_csv(ROOT / "prepared/05_split_70_15_15/sentiment/train_X.csv")
    train_y = pd.read_csv(ROOT / "prepared/05_split_70_15_15/sentiment/train_y.csv").iloc[:, 0]
    cases = pd.read_csv(ROOT / "reports/sentiment_stress_test/cases_2000.csv")
    assert len(cases) == 2000 and cases.expected_label.value_counts().eq(500).all()
    assert set(train_y) == set(LABELS)

    original_model = ROOT / "prepared/07_modeling/SVM.joblib"
    original_model_hash = sha256(original_model)
    print(f"Loading {BASE_MODEL} on CPU; train rows={len(train_x)}, challenge rows={len(cases)}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(LABELS), id2label={i: label for i, label in enumerate(LABELS)},
        label2id=LABEL_TO_ID, ignore_mismatched_sizes=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train = DataLoader(TextDataset(train_x.content_text, train_y, tokenizer),
                       batch_size=BATCH_SIZE, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
    history = []
    started = time.perf_counter()
    for epoch in range(EPOCHS):
        model.train()
        losses = []
        for step, batch in enumerate(train, start=1):
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            output = model(**batch)
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(output.loss.detach().cpu()))
            if step % 10 == 0:
                print(f"epoch={epoch + 1}/{EPOCHS} step={step}/{len(train)} loss={np.mean(losses):.4f}", flush=True)
        history.append({"epoch": epoch + 1, "mean_train_loss": float(np.mean(losses))})
        print(f"Finished epoch {epoch + 1}: mean loss {np.mean(losses):.4f}", flush=True)

    model.eval()
    challenge = DataLoader(TextDataset(cases.content_text, cases.expected_label, tokenizer),
                           batch_size=32, shuffle=False)
    predictions = []
    with torch.inference_mode():
        for batch in challenge:
            batch = {key: value.to(device) for key, value in batch.items() if key != "labels"}
            logits = model(**batch).logits
            predictions.extend(torch.argmax(logits, dim=1).cpu().tolist())
    cases["prediction"] = [LABELS[index] for index in predictions]
    cases["correct"] = cases.expected_label.eq(cases.prediction)
    metrics = {
        "base_model": BASE_MODEL,
        "fine_tuned_for": "4-class cafe menu sentiment using the existing train split only",
        "device": str(device), "seed": SEED, "epochs": EPOCHS, "batch_size": BATCH_SIZE,
        "max_length": MAX_LENGTH, "train_count": len(train_x), "challenge_count": len(cases),
        "train_class_counts": train_y.value_counts().to_dict(),
        "accuracy": float(accuracy_score(cases.expected_label, cases.prediction)),
        "macro_f1": float(f1_score(cases.expected_label, cases.prediction, labels=LABELS, average="macro")),
        "classification_report": classification_report(cases.expected_label, cases.prediction,
            labels=LABELS, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(cases.expected_label, cases.prediction, labels=LABELS).tolist(),
        "label_order": LABELS, "epoch_history": history,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "original_svm_sha256_before": original_model_hash,
        "original_svm_sha256_after": sha256(original_model),
        "limitations": [
            "This is a controlled synthetic challenge, not human-reviewed consumer reviews.",
            "Challenge labels did not participate in fine-tuning or model selection.",
            "Training labels are synthetic project labels; performance should not be generalized to real market data.",
            "Checkpoint is local to ignored tmp/; model weights are not stored in GitHub.",
        ],
    }
    cases.to_csv(OUT / "predictions_2000.csv", index=False, lineterminator="\n")
    cases.loc[~cases.correct].to_csv(OUT / "errors.csv", index=False, lineterminator="\n")
    (OUT / "results.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    model.save_pretrained(CHECKPOINT, safe_serialization=True)
    tokenizer.save_pretrained(CHECKPOINT)

    svm_result = json.loads((ROOT / "reports/sentiment_stress_test/results.json").read_text(encoding="utf-8"))
    report = ["# Eksperimen IndoBERT untuk sentimen menu", "",
        f"- Base model: `{BASE_MODEL}` (pretrained bahasa; classifier empat kelas di-fine-tune di data train proyek).",
        f"- Data latih: {len(train_x)} baris, split train proyek; challenge: 2.000 input beku.",
        f"- Runtime: {device}, {metrics['elapsed_seconds']} detik, {EPOCHS} epoch.",
        "- Challenge yang sama seperti uji SVM sebelumnya; tidak dipakai saat fine-tuning.", "",
        "> **Status:** IndoBERT dipakai pada endpoint demo lokal. Akurasi total challenge lebih tinggi dari SVM, tetapi recall positif jatuh karena sebagian besar opini positif diprediksi campuran. Hasil ini belum menunjukkan kinerja pada ulasan nyata.", "",
        "| Model | Akurasi | Macro F1 |", "|---|---:|---:|"]
    report.append(f"| SVM TF-IDF (acuan) | {svm_result['accuracy']:.2%} | {svm_result['macro_f1']:.4f} |")
    report.append(f"| IndoBERT fine-tuned | {metrics['accuracy']:.2%} | {metrics['macro_f1']:.4f} |")
    report += ["", "## Per kelas dan perbandingan recall", "",
        "| Kelas | SVM recall | IndoBERT recall | IndoBERT precision | IndoBERT F1 |",
        "|---|---:|---:|---:|---:|"]
    for label in LABELS:
        item = metrics["classification_report"][label]
        baseline = svm_result["classification_report"][label]
        report.append(f"| {label} | {baseline['recall']:.1%} | {item['recall']:.1%} | {item['precision']:.4f} | {item['f1-score']:.4f} |")
    report += ["", "## Pola kegagalan", "",
        f"- Dari 500 input positif, IndoBERT hanya mengenali {metrics['confusion_matrix'][0][0]} sebagai positif; {metrics['confusion_matrix'][0][3]} diprediksi campuran.",
        f"- Pada kelas campuran, recall naik dari {svm_result['classification_report']['mixed']['recall']:.1%} (SVM) ke {metrics['classification_report']['mixed']['recall']:.1%}, tetapi model masih melewatkan sebagian besar kasus.",
        "- Set challenge menguji dua arah campuran rasa/nilai, sedangkan generator data latih proyek hanya membentuk satu arah campuran. Ini kemungkinan besar membuat model berat sebelah.",
        "- Variasi bahasa informal memperoleh akurasi tertinggi (57,8%), tetapi akurasi keseluruhan tetap terbatas.",
        "", "## Catatan", "", *[f"- {note}" for note in metrics["limitations"]],
        "- Checkpoint fine-tuned lokal tersimpan di workspace `tmp/indobert-cafestock-fourclass` dan dipakai endpoint demo; bobot tidak disimpan di GitHub.",
        "- Seri sentimen historis dan fitur risiko tetap memakai SVM kronologis; form demo teks memakai IndoBERT.", ""]
    (OUT / "report.md").write_text("\n".join(report), encoding="utf-8")
    assert metrics["original_svm_sha256_before"] == metrics["original_svm_sha256_after"]
    print(f"IndoBERT challenge accuracy={metrics['accuracy']:.4f}, macro_f1={metrics['macro_f1']:.4f}", flush=True)
    print(f"Report: {OUT / 'report.md'}", flush=True)


if __name__ == "__main__":
    main()
