import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence

class ConjunctionLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, num_layers=2, num_classes=3, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x, lengths):
        packed = pack_padded_sequence(
            x, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        out, (hidden, _) = self.lstm(packed)
        last_hidden = hidden[-1]
        out = self.dropout(last_hidden)
        return self.fc(out)