"""
Assums that you've already using clevr-dataset-gen repo to run something like:

/persist/soft/blender-2.79b-linux-glibc219-x86_64/blender --background --python generate_cube_color_examples.py -- \
    --out_dir ../output/cube_colors --min_objects 2 --max_objects 2 --num_examples 1024 --width 64 --height 64 \
    --sizes small:0.7,large:1.4 --min_pixels_per_object 40 --render_num_samples 256
(this will generate images and scene files)

What we want to do in this script is:
- reduce the images to an h5py file, and
- reduce the scenes_reduced.json to a csv file


This script is a fork of cube_is_color_dataprep.py, for the case where each example has multiple scenes.
"""
import os, sys, time, datetime, csv, json, argparse, glob
from os import path
from os.path import join, expanduser as expand
from scipy.misc import imread, imresize
import numpy as np
import h5py

def run(ds_ref, out_dir, in_scenes_reduced, in_images, out_labels, out_images):
    print('creating', out_labels)
    M = len(glob.glob(join(expand(out_dir), 'scenes', 'CLEVR_new_000000_*.json')))
    print('M', M)
    scene_files = sorted(glob.glob(join(expand(out_dir), 'scenes', f'CLEVR_new_*_{M-1}.json')))
    image_files = sorted(glob.glob(join(expand(out_dir), 'images', f'*_{M-1}.png')))
    N_scenes = len(scene_files)
    N_images = len(image_files)
    N = min(N_scenes, N_images)
    print('N_scenes', N_scenes, 'N_images', N_images, 'N', N, 'M', M)
    scene_files = scene_files[:N]
    image_files = image_files[:N]

    scene_filepath = join(expand(out_dir), 'scenes', f'CLEVR_new_%06d_%d.json' % (0, 0))
    shapes = []
    with open(expand(scene_filepath), 'r') as f:
        scene = json.load(f)
        color = None
        for o in scene['objects']:
            shapes.append(o['shape'])
    shapes = sorted(shapes)
    print('shapes', shapes)
    shape_id_by_name = {shape: i for i, shape in enumerate(shapes)}

    with open(expand(out_labels), 'w') as f:
        dict_writer = csv.DictWriter(f, fieldnames=['n'] + shapes)
        dict_writer.writeheader()
        # for n, scene_filepath in enumerate(scene_files):
        # we want to collect the underlying example metadata, so we can calculate rho
        for n in range(N):
            # color_idxes = torch.LongTensor
            row = {'n': n}
            # for m in range(M):
            m = 0
            scene_filepath = join(expand(out_dir), 'scenes', f'CLEVR_new_%06d_%d.json' % (n, m))
            with open(expand(scene_filepath), 'r') as f:
                scene = json.load(f)
                for o in scene['objects']:
                    row[o['shape']] = o['color']
            dict_writer.writerow(row)
            n += 1
    print('done writing', out_labels)

    print('creating', out_images)
    last_print = time.time()
    with h5py.File(expand(out_images), 'w') as f:
        images_dset = None
        files = sorted(os.listdir(expand(in_images)))
        for n in range(N):
            for m in range(M):
                img_path = join(expand(out_dir), 'images', f'CLEVR_new_%06d_%d.png' % (n, m))
        # for n, img_path in enumerate(image_files):
                img = imread(expand(img_path), mode='RGB')
                img = img.transpose(2, 0, 1)[None] / 255
                if images_dset is None:
                    _, C, H, W = img.shape
                    images_dset = f.create_dataset('images', (N, M, C, H, W), dtype=np.float32)
                    print('created images dataset')
                images_dset[n, m] = img
                # n += 1
                if time.time() - last_print >= 5:
                    print('n', n)
                    last_print = time.time()
    print('created', out_images)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ds-ref', type=str, required=True)
    parser.add_argument('--out-dir', type=str, default='~/data/clevr/{ds_ref}', help='path to directory that contains images, scenes, scenes_reduced.json')
    parser.add_argument('--in-scenes-reduced', type=str, default='{out_dir}/scenes_reduced.json')
    parser.add_argument('--in-images', type=str, default='{out_dir}/images')
    parser.add_argument('--out-labels', type=str, default='{out_dir}/labels.csv')
    parser.add_argument('--out-images', type=str, default='{out_dir}/imagesb.h5')
    args = parser.parse_args()
    args.out_dir = args.out_dir.format(**args.__dict__)
    for k, v in args.__dict__.items():
        if '{' in v:
            args.__dict__[k] = v.format(**args.__dict__)
    run(**args.__dict__)
