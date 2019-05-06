# PyTorch PPF-FoldNet
This repo is implementation for PPF-FoldNet(https://arxiv.org/abs/1808.10322v1) in pytorch. 

## Project Structure

- `models/`: dictionary that saves the model of PPF-FoldNet. PPF-FoldNet is an Auto-Encoder for point pair feature of a local patch. The input is a batch of point cloud fragments `[bs(num_patches), num_points_per_patch, 4]`, output of the Encoder is the descriptor for each local patch in these point cloud, `[bs(num_patches), 1, 512]`, where 512 is the default codeword length.
    1. `models_conv1d.py`: PPF-FoldNet model using conv1d layers.
    2. `models_linear.py`: PPF-FoldNet model using linear layers. Theoretically, nn.Conv1d and nn.Linear should be same when `(kernel_size=1, stride=1, padding=0, dilation=1)`. You can try `misc/linear_conv1d.py` for the experiment.
- `input_preparation.py`: used before training, including: 
    1. reconstruct point cloud from  rgbd image and depth image.
    2. choose reference point(or interest point) from the point cloud.
    3. collect neighboring points near each reference point.
    4. build local patch for each reference point and their neighbor.
    5. save the local patch as numpy array for later use.
    6. I also write a function for preparing the ppf input on the fly.
- `dataset.py`: define the Dataset, read from the files generated from input prepration stage.
- `dataloader.py`: define the dataloader, nothing specical.
- `loss.py`: define the Chamfer Loss. (Earth Move Distance Loss is worth trying.)
- `trainer.py`: the trainer class, handle the training process including snapshot.
- `train.py`: the entrance file, every time I start training, this file will be copied to the snapshot dictionary.
- `geometric_registration/`: dictionary for evaluating the model through the task of geometric registration
    1. `gt_result/`: the ground truth information provided by 3DMatch benchmark.
    2. `intermediate-files-real/`: dictionary that saves the keypoints coordinates for each scene.
    3. `fragments/`: dictionary that save the point cloud fragments for each scene.
    4. `preparation.py`: calculate the descriptor for each interest point provided by 3DMatch Benchmark. (need to calculate the ppf representation for each interest point first)
    5. `evaluate_ppfnet.py`: using the evaluation metric proposed in PPF-FoldNet paper to evaluate the performance of the descriptor.
        1. get point cloud from `.ply` file and get the interest point coordinate from `.keypts.bin` file.
        2. use the descriptor generated by `preparation.py` to register each pair of point clouds fragment and save the result in `pred_result/`
        3. after register each pair of fragment, we can get the final `recall` of the descriptors.
    6. `utils.py`
 - `misc/`

## Prepara the data

Use `script/download.sh` to download all the training set from [3DMatch](http://3dmatch.cs.princeton.edu/)


## Milestone
- 3.25: Initial Version
    - Realize the network architecture of PPF-FoldNet(but actually is very similar with FoldingNet and I have partially achieve the result of FoldingNet, the reconstruction and interpolation looks good.)
    - The input is still the point coordinates for now. And the dataset used is ShapeNet. This is the main aim of next step implementation.
    
- 4.8:
    - Change dataset to Sun3D (downloaded from 3DMatch webpage). And it is easy to extend to the whole 3DMatch dataset.
    - Input preparation is done, the input is the point pair feature. Currently I do this process before I start to train the network. For each point cloud (reconstructed by a RGB image and a depth image and a camera pose), I select 2048 interest point, and collect 1024 neighbor point for each interest point, then calculate the ppf for each pair. So the preprocessing output for one point cloud is a [2048, 1024, 4] array, I save it in a `.npy` file. 
    - But here comes a questions: for input to the network, how many interest point should I choice for one point cloud? (Or for one batch input, how many point cloud should I choose? and for each point cloud how many local patches should I choose? In the origin paper, the author claimed that they use a batch size 32, so obviously they cannot select all the 2048 local patches for a single point cloud otherwise the input to the network will be [32, 2048, 1024, 4] which is so large.) Currently I just random pick all the 2048 local patches from one point cloud and use a small batch size. Maybe choose a small number of local patches per point cloud is also OK.
        - here my origin understanding is wrong, the batch size refers to how many local patches we choose for one input, if batch size = 32, then the input shape is [32, 1024, 4]. So I will change the code, every time we select `batch_size` number of local patches from one point cloud fragment.
    - It seems there is no good way to visualize the result and evaluate the performance except the 3DMatch geometry benchmark. The visualization of ppf in the PPF-FoldNet paper does not make sense to me.


## TODO List
- [x] dataset & dataloader for 3DMatch Dataset.
- [x] Input Preparation. (Point coordinates -> point pair feature)
- [x] Evaluation. (Recall on 3DMatch Dataset).
- [x] Scale to the whole 3DMatch Dataset.
- [x] Add initialization using Xaviar.
- [ ] why my descriptor have many zero dimentions?
