# coding=utf-8
import zipfile
import os
import requests
import argparse
import csv
from tqdm import tqdm
import urllib
import threading, queue, time
from skimage import io, transform

parser = argparse.ArgumentParser(description='Download IMDB-Face helper')
parser.add_argument('path', type=str, help="IMDB-Face Dataset Save Path")

def download_file_from_google_drive(id, destination):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def save_response_content(response, destination, chunk_size=32 * 1024):
    total_size = int(response.headers.get('content-length', 0))
    with open(destination, "wb") as f:
        for chunk in tqdm(
                response.iter_content(chunk_size),
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=destination):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def save_img(data_path, urlQueue):
    # save image to file_path
    while True:
        try:
            row = urlQueue.get_nowait()
            i = urlQueue.qsize()
        except Exception as e:
            break
        print ('Thread:%s, Url: %s ' % (threading.currentThread().name, row['url']))
        try:
            id_dir = os.path.join(data_path, row['index'])
            if not os.path.exists(id_dir):
                os.mkdir(id_dir)
            # get the save path
            filename = '{}{}{}'.format(id_dir, os.sep, row['image'])
            img = io.imread(row['url'])
            img_shape = [int(i) for i in row['height width'].split(' ')]
            rect = [int(i) for i in row['rect'].split(' ')]
            download_shape = img.shape
            if ((img_shape[0]!=download_shape[0]) or (img_shape[1]!=download_shape[1])):
                # ratio_height = download_shape[0]/img_shape[0]
                # ratio_width = download_shape[1]/img_shape[1]
                # rect = [int(rect[0]*ratio_width), int(rect[1]*ratio_height), int(rect[2]*ratio_width), int(rect[3]*ratio_height)]
                img = transform.resize(img, (img_shape[0], img_shape[1]))
            face_shape = [int((rect[3]-rect[1])/2), int((rect[2]-rect[0])/2)]
            rect = [max(0, rect[0]-face_shape[1]), max(0, rect[1]-face_shape[0]), min(img_shape[1], rect[2]+face_shape[1]), min(img_shape[0], rect[3]+face_shape[0])]
            img = img[rect[1]:rect[3], rect[0]:rect[2], :]
            io.imsave(filename, img)

        except IOError as e:
            print('IOError', e)
        except Exception as e:
            print('Error ：', e)


if __name__ == '__main__':
    args = parser.parse_args()
    dirpath = args.path
    data_name = 'IMDb-Face'
    data_path = os.path.join(dirpath, data_name)
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    csvname = 'IMDb-Face.csv '
    drive_id = '134kOnRcJgHZ2eREu8QRi99qj996Ap_ML'
    print('Deal with file: ' + csvname, ',may take a little while!!!')
    if os.path.exists(csvname):
        print('[*] {} already exists'.format(csvname))
    else:
        download_file_from_google_drive(drive_id, csvname)

    print('Deal with IMDb-Face Images!!!')
    with open(csvname) as f:
        f_csv = csv.DictReader(f)
        urlQueue = queue.Queue()
        for row in f_csv:
            urlQueue.put(row)

    threads = []
    # 可以调节线程数， 进而控制抓取速度
    threadNum = 8
    for i in range(0, threadNum):
        t = threading.Thread(target=save_img, args=(data_path, urlQueue,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        #多线程多join的情况下，依次执行各线程的join方法, 这样可以确保主线程最后退出， 且各个线程间没有阻塞
        t.join()
