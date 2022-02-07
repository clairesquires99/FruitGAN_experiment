Steps for setup
1. ganspace/models/wrappers.py, register model (fruits already registered)
2. in ganspace folder
    python visualize.py --model 'StyleGAN2' --class 'fruits' --use-w --layer style -c 10 (# don't think 10 works here)
3. components stored in npz file in ganspace/cache/components

