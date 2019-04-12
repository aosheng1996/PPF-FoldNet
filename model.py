import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import itertools
from loss import ChamferLoss
import inspect
from gpu_mem_track import MemTracker

class Encoder(nn.Module):
    def __init__(self, num_points=1024):
        super(Encoder, self).__init__()
        self.num_points = num_points
        self.conv1 = nn.Conv1d(4, 64, 1)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()

        self.conv2 = nn.Conv1d(64, 128, 1)
        self.bn2 = nn.BatchNorm1d(128)
        self.relu2 = nn.ReLU()

        self.conv3 = nn.Conv1d(128, 1024, 1)
        self.bn3 = nn.BatchNorm1d(1024)
        self.relu3 = nn.ReLU()

        self.fc1 = nn.Linear(1024 + 64, 1024)
        self.fc2 = nn.Linear(1024, 512)  # codeword dimension = 512
        # self.bn4 = nn.BatchNorm1d(1024)
        # self.bn5 = nn.BatchNorm1d(512)

    def forward(self, input):
        # origin shape from dataloader [bs*32, 1024(num_points), 4]
        input = input.transpose(2, 1).float()
        x = self.relu1(self.bn1(self.conv1(input)))
        local_feature = x  # save the  low level features to concatenate this global feature.
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = torch.max(x, 2, keepdim=True)[0]
        global_feature = x.view(-1, 1024, 1).repeat(1, 1, 1024)
        feature = torch.cat([local_feature, global_feature], 1)  # [bs, 1088, 1024]

        # TODO: add batch_norm or not?
        x = F.relu(self.fc1(feature.transpose(1, 2)))
        x = F.relu(self.fc2(x))

        # TODO: the actual output should be [bs, 1, 512] by max pooling ??
        return torch.max(x, 1, keepdim=True)[0]  # [bs, 1, 512]


class Decoder(nn.Module):
    def __init__(self, num_points=1024, m=1024):
        super(Decoder, self).__init__()
        self.n = num_points  # input point cloud size.
        self.m = m  # 32 * 32
        self.meshgrid = [[-0.3, 0.3, 32], [-0.3, 0.3, 32]]
        self.mlp1 = nn.Sequential(
            nn.Conv1d(514, 256, 1),
            nn.ReLU(),
            nn.Conv1d(256, 64, 1),
            nn.ReLU(),
            nn.Conv1d(64, 4, 1),
            # nn.ReLU(),
        )

        self.mlp2 = nn.Sequential(
            nn.Conv1d(516, 256, 1),
            nn.ReLU(),
            nn.Conv1d(256, 64, 1),
            nn.ReLU(),
            nn.Conv1d(64, 4, 1),
            # nn.ReLU(),
        )

    def build_grid(self, batch_size):
        # ret = np.meshgrid(*[np.linspace(it[0], it[1], num=it[2]) for it in self.meshgrid])
        # ndim = len(self.meshgrid)
        # grid = np.zeros((np.prod([it[2] for it in self.meshgrid]), ndim), dtype=np.float32)  # MxD
        # for d in range(ndim):
        #     grid[:, d] = np.reshape(ret[d], -1)
        x = np.linspace(*self.meshgrid[0])
        y = np.linspace(*self.meshgrid[1])
        grid = np.array(list(itertools.product(x, y)))
        grid = np.repeat(grid[np.newaxis, ...], repeats=batch_size, axis=0)
        grid = torch.tensor(grid)
        return grid.float()

    def forward(self, input):
        input = input.transpose(1, 2).repeat(1, 1, self.m)  # [bs, 512, m]
        grid = self.build_grid(input.shape[0]).transpose(1, 2)  # [bs, 2, m]
        if torch.cuda.is_available():
            grid = grid.cuda()
        concate1 = torch.cat((input, grid), dim=1)  # [bs, 514, m]
        after_folding1 = self.mlp1(concate1)  # [bs, 4, m]
        concate2 = torch.cat((input, after_folding1), dim=1)  # [bs, 516, m]
        after_folding2 = self.mlp2(concate2)  # [bs, 4, m]
        return after_folding2.transpose(1, 2)  # [bs, m ,4]


class PPFFoldNet(nn.Module):
    def __init__(self, num_points):
        super(PPFFoldNet, self).__init__()

        self.encoder = Encoder(num_points=num_points)
        self.decoder = Decoder(num_points=num_points, m=num_points)
        self.loss = ChamferLoss()

    def forward(self, input):
        frame = inspect.currentframe()
        gpu_tracker = MemTracker(frame)
        gpu_tracker.track()

        codeword = self.encoder(input)
        gpu_tracker.track()
        output = self.decoder(codeword)
        gpu_tracker.track()
        return output

    def get_parameter(self):
        return list(self.encoder.parameters()) + list(self.decoder.parameters())

    def get_loss(self, input, output):
        # input shape  [bs, 2048, 3]
        # output shape [bs, 2025, 3]
        return self.loss(input, output)
