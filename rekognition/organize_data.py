"""
Helper script for re-organizing Meta Hateful Memes Challenge dataset into train/ and test/ directories stratified as hateful/ or non-hateful/ so that Rekognition can auto-detect labels from directory hierarchy when formulating dataset. 
"""

import os
import json
import shutil

def create_directories(base_path):
    for subdir in ['train', 'test']:
        for label_dir in ['hateful', 'non-hateful']:
            dir_path = os.path.join(base_path, subdir, label_dir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)


def move_images(jsonl_file, base_dir, subdir):
    with open(jsonl_file, 'r') as file:
        for line in file:
            data = json.loads(line)
            img_path = os.path.join(base_dir, data['img'])
            label_dir = 'hateful' if data['label'] == 1 else 'non-hateful'
            target_dir = os.path.join(base_dir, 'img', subdir, label_dir, os.path.basename(data['img']))
            
            try:
                shutil.move(img_path, target_dir)
            except FileNotFoundError:
                print(f"File not found: {img_path}, skipping.")
                continue


def main():
    base_dir = 'hateful_memes' 
    create_directories(os.path.join(base_dir, 'img'))

    # Move images from training, testing, and development data
    move_images('hateful_memes/train.jsonl', base_dir, 'train')
    move_images('hateful_memes/test_seen.jsonl', base_dir, 'test')
    move_images('hateful_memes/test_unseen.jsonl', base_dir, 'test')
    move_images('hateful_memes/dev_seen.jsonl', base_dir, 'train')  
    move_images('hateful_memes/dev_unseen.jsonl', base_dir, 'train')


if __name__ == '__main__':
    main()

