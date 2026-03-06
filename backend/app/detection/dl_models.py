"""
Deep Learning Models for NIDS — PyTorch Implementation.

Models:
1. 1D-CNN: For spatial/header feature Extraction and classification.
2. LSTM: For temporal/sequential analysis of packet flows.
3. Autoencoder: For unsupervised anomaly detection.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class Attention(nn.Module):
    """Simple Self-Attention mechanism to focus on key features."""
    def __init__(self, hidden_dim: int):
        super(Attention, self).__init__()
        self.attention = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, hidden_dim)
        weights = torch.softmax(self.attention(x), dim=1)
        # Apply weights: (batch, seq_len, 1) * (batch, seq_len, hidden_dim)
        context = torch.sum(weights * x, dim=1)
        return context, weights

class CNN1DDetector(nn.Module):
    """
    1D Convolutional Neural Network for packet/flow feature extraction.
    Good for capturing local relationships between header fields.
    """
    def __init__(self, input_dim: int, num_classes: int = 2):
        super(CNN1DDetector, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(32)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool = nn.MaxPool1d(kernel_size=2)
        
        # Calculate flatten size based on input_dim
        # After two convs and one pool: input_dim -> input_dim // 2
        self.flatten_dim = 64 * (input_dim // 2)
        
        self.fc1 = nn.Linear(self.flatten_dim, 128)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        # x shape: (batch, input_dim) -> (batch, 1, input_dim)
        x = x.unsqueeze(1)
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class LSTMDetector(nn.Module):
    """
    LSTM (Long Short-Term Memory) for temporal analysis of packet sequences.
    Good for detecting multi-step attacks or slow scans.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, num_classes: int = 2):
        super(LSTMDetector, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        # Take the output of the last time step
        out = self.fc(out[:, -1, :])
        return out

class AutoencoderAnomaly(nn.Module):
    """
    Autoencoder for unsupervised anomaly detection.
    Trained only on 'normal' traffic to reconstruct it. 
    High reconstruction error = Anomaly.
    """
    def __init__(self, input_dim: int):
        super(AutoencoderAnomaly, self).__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8) # Latent representation
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

    def get_anomaly_score(self, x):
        """Returns MSE between input and reconstruction."""
        reconstructed = self.forward(x)
        return F.mse_loss(x, reconstructed, reduction='none').mean(dim=1)

class EliteHybridDetector(nn.Module):
    """
    Elite Hybrid Architecture: 1D-CNN (Spatial) + LSTM (Temporal) + Attention.
    Designed for maximum detection accuracy against sophisticated adversaries.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_classes: int = 2):
        super(EliteHybridDetector, self).__init__()
        
        # 1. Spatial Feature Extraction (CNN)
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        self.pool = nn.MaxPool1d(kernel_size=2)
        
        # 2. Temporal Analysis (LSTM)
        # Reduced dimension after pooling: input_dim // 2
        self.lstm = nn.LSTM(input_size=64, hidden_size=hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
        
        # 3. Attention Component
        self.attention = Attention(hidden_dim * 2) # *2 for bidirectional
        
        # 4. Final Classification
        self.fc1 = nn.Linear(hidden_dim * 2, 64)
        self.dropout = nn.Dropout(0.4)
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x):
        # x: (batch, input_dim) -> (batch, 1, input_dim)
        x = x.unsqueeze(1)
        
        # CNN Phase
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        
        # Prepare for LSTM: (batch, channels, seq) -> (batch, seq, channels)
        x = x.transpose(1, 2)
        
        # LSTM Phase
        out, _ = self.lstm(x)
        
        # Attention Phase
        context, _ = self.attention(out)
        
        # Classification
        x = F.relu(self.fc1(context))
        x = self.dropout(x)
        x = self.fc2(x)
        return x
