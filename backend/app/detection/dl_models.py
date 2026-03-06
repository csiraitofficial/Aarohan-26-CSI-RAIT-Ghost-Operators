from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)

# SAFE MODE / Hardware Check
TORCH_AVAILABLE = False
if os.getenv('NIDS_SAFE_MODE', 'false').lower() != 'true':
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        TORCH_AVAILABLE = True
    except ImportError:
        logger.warning("PyTorch not found. Deep Learning models will be disabled.")
    except Exception as e:
        logger.error(f"Hardware error during Torch load: {e}. Disabling DL.")

if not TORCH_AVAILABLE:
    # Minimal stubs to prevent ImportErrors in other modules
    class nn:
        class Module: pass
    class F: pass
    
    class Attention(nn.Module):
        def __init__(self, *args, **kwargs): pass
        def forward(self, x): return x, None

    class CNN1DDetector(nn.Module):
        def __init__(self, *args, **kwargs): pass
        def forward(self, x): return x

    class LSTMDetector(nn.Module):
        def __init__(self, *args, **kwargs): pass
        def forward(self, x): return x

    class AutoencoderAnomaly(nn.Module):
        def __init__(self, *args, **kwargs): pass
        def forward(self, x): return x
        def get_anomaly_score(self, x): return 0.0

    class EliteHybridDetector(nn.Module):
        def __init__(self, *args, **kwargs): pass
        def forward(self, x): return x
else:
    # Full Implementation
    class Attention(nn.Module):
        """Simple Self-Attention mechanism to focus on key features."""
        def __init__(self, hidden_dim: int):
            super(Attention, self).__init__()
            self.attention = nn.Linear(hidden_dim, 1)

        def forward(self, x):
            weights = torch.softmax(self.attention(x), dim=1)
            context = torch.sum(weights * x, dim=1)
            return context, weights

    class CNN1DDetector(nn.Module):
        def __init__(self, input_dim: int, num_classes: int = 2):
            super(CNN1DDetector, self).__init__()
            self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
            self.bn1 = nn.BatchNorm1d(32)
            self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
            self.bn2 = nn.BatchNorm1d(64)
            self.pool = nn.MaxPool1d(kernel_size=2)
            self.flatten_dim = 64 * (input_dim // 2)
            self.fc1 = nn.Linear(self.flatten_dim, 128)
            self.dropout = nn.Dropout(0.3)
            self.fc2 = nn.Linear(128, num_classes)

        def forward(self, x):
            x = x.unsqueeze(1)
            x = F.relu(self.bn1(self.conv1(x)))
            x = self.pool(F.relu(self.bn2(self.conv2(x))))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            x = self.dropout(x)
            x = self.fc2(x)
            return x

    class LSTMDetector(nn.Module):
        def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, num_classes: int = 2):
            super(LSTMDetector, self).__init__()
            self.hidden_dim = hidden_dim
            self.num_layers = num_layers
            self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
            self.fc = nn.Linear(hidden_dim, num_classes)

        def forward(self, x):
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
            out, _ = self.lstm(x, (h0, c0))
            out = self.fc(out[:, -1, :])
            return out

    class AutoencoderAnomaly(nn.Module):
        def __init__(self, input_dim: int):
            super(AutoencoderAnomaly, self).__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 32), nn.ReLU(),
                nn.Linear(32, 16), nn.ReLU(),
                nn.Linear(16, 8)
            )
            self.decoder = nn.Sequential(
                nn.Linear(8, 16), nn.ReLU(),
                nn.Linear(16, 32), nn.ReLU(),
                nn.Linear(32, input_dim)
            )

        def forward(self, x):
            latent = self.encoder(x)
            return self.decoder(latent)

        def get_anomaly_score(self, x):
            reconstructed = self.forward(x)
            return F.mse_loss(x, reconstructed, reduction='none').mean(dim=1)

    class EliteHybridDetector(nn.Module):
        def __init__(self, input_dim: int, hidden_dim: int = 128, num_classes: int = 2):
            super(EliteHybridDetector, self).__init__()
            self.conv1 = nn.Conv1d(in_channels=1, out_channels=64, kernel_size=3, padding=1)
            self.bn1 = nn.BatchNorm1d(64)
            self.pool = nn.MaxPool1d(kernel_size=2)
            self.lstm = nn.LSTM(input_size=64, hidden_size=hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
            self.attention = Attention(hidden_dim * 2)
            self.fc1 = nn.Linear(hidden_dim * 2, 64)
            self.dropout = nn.Dropout(0.4)
            self.fc2 = nn.Linear(64, num_classes)

        def forward(self, x):
            x = x.unsqueeze(1)
            x = F.relu(self.bn1(self.conv1(x)))
            x = self.pool(x)
            x = x.transpose(1, 2)
            out, _ = self.lstm(x)
            context, _ = self.attention(out)
            x = F.relu(self.fc1(context))
            x = self.dropout(x)
            x = self.fc2(x)
            return x
