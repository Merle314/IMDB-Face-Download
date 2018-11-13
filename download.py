import zipfile
import os
import requests
import argparse
from collections import namedtuple
import csv
from tqdm import tqdm
import urllib

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


def save_img(img_url, file_name, file_path):
    # save image to file_path
    try:
        if not os.path.exists(file_path):
            print('directory', file_path, 'not exist, make it!!!')
            os.mkdir(file_path)
        # get the save path
        filename = '{}{}{}'.format(file_path,os.sep,file_name)
       #下载图片，并保存到文件夹中
        # urllib.request.urlretrieve(img_url,filename=filename)

        u = urllib.request.urlopen(img_url)
        data = u.read()
        with open(filename, 'wb+') as f:
            f.write(data)

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
        for row in f_csv:
            id_dir = os.path.join(data_path, row['index'])
            save_img(row['url'], row['image'], id_dir)

