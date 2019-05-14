import torch.utils.data as data
import os
import os.path
import open3d
import numpy as np
import time
from tqdm import tqdm
import json
from input_preparation import get_local_patches_on_the_fly


class SunDataset(data.Dataset):
    def __init__(self,
                 root,
                 split='train',
                 num_patches=32,  # num of patches per point cloud. which is also the batch size of the input.
                 num_points_per_patch=1024,
                 data_augmentation=True,
                 on_the_fly=True):
        self.root = root
        self.split = split
        self.data_augmentation = data_augmentation
        self.num_patches = num_patches
        self.num_points_per_patch = num_points_per_patch
        self.on_the_fly = on_the_fly

        # Support the whole 3Dmatch dataset
        with open(os.path.join(root, f'scene_list_{split}.txt')) as f:
            scene_list = f.readlines()

        self.ids_list = []
        self.scene_list = []
        for scene in scene_list:
            if not scene.__contains__('sun3d'):
                continue
            scene = scene.replace("\n","")
            ids = [scene + "/seq-01/" + str(filename.split(".")[0]) for filename in os.listdir(os.path.join(self.root, scene + '/seq-01/'))]
            self.ids_list += sorted(list(set(ids)))
            self.scene_list.append(scene)
        #if split == 'test':
        #    self.ids_list = self.ids_list[0:10000]
        #if split == 'train':
        #    self.ids_list = self.ids_list[0:50000]

    def __getitem__(self, index):
        id = self.ids_list[index]
        if self.on_the_fly:
            try:
                return get_local_patches_on_the_fly(self.root, id, self.num_patches, self.num_points_per_patch), id
            except:
                print(id, "cannot open")
                return self.__getitem__(0)

        ind = np.random.choice(range(2048), self.num_patches, replace=False)
        patches = np.load(os.path.join(self.root, self.ids_list[index] + ".npy"))
        return patches[ind], self.ids_list[index]

        # if self.split == 'train':
        #     patches = np.load(os.path.join(self.root, self.ids_list[index] + ".npy"))
        #     return patches
        # else:
        #     patches = np.load(os.path.join(self.root, self.ids_list[index] + ".npy"))
        #     pcd = open3d.read_point_cloud(os.path.join(self.root, self.ids_list[index] + ".pcd"))
        #     return patches, [pcd]

    def __len__(self):
        return len(self.ids_list)


if __name__ == '__main__':
    datapath = "/data/3DMatch/whole"
    d = SunDataset(root=datapath, split='test', on_the_fly=True)
    print(len(d.ids_list))
    # print(d.scene_list)
    start_time = time.time()
    for i in range(len(d.ids_list)):
        patches, id = d[i]
        if i % 100 == 0:
            print(f"{i} : {time.time() - start_time} s")
    print(f"Test set On the fly: {time.time() - start_time}")

    datapath = "/data/3DMatch/whole"
    d = SunDataset(root=datapath, split='train', on_the_fly=True)
    print(len(d.ids_list))
    #print(d.scene_list)
    start_time = time.time()
    for i in range(len(d.ids_list)):
        patches, id = d[i]
        if i % 100 == 0:
            print(f"{i}: {time.time() - start_time} s")
    print(f"Training set On the fly: {time.time() - start_time}")

    # datapath = "/data/3DMatch/whole/"
    # d = SunDataset(root=datapath, split='train', on_the_fly=True)
    # print("Training set size:", len(d.ids_list))
    # for i in range(13900, 140900):
    #     p, ind = d[i]
    #     print(ind)
    #
    # d = SunDataset(root=datapath, split='test', on_the_fly=True)
    # print("Test set size:", len(d.ids_list))
    # patches, id = d[0]
    # print(patches.shape)
    # print(id)
