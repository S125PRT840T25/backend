from transformers import BertTokenizer, BertForSequenceClassification
import torch
import pickle

class SentimentModel:
    def __init__(self, model_path, label_path):
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()
        with open(label_path, 'rb') as f:
            self.label_encoder = pickle.load(f)

    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=-1).item()
        return self.label_encoder.inverse_transform([predicted_class])[0]
