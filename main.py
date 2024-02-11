import requests
import urllib
import xml.etree.ElementTree as ET

from os import chdir,getcwd,makedirs
from os.path import dirname,abspath,isdir,join
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from PIL import Image
from datetime import datetime
from io import BytesIO
from numpy import array
from  contextlib import ExitStack
from re import findall


def get_work_dir():
    chdir(dirname(abspath(__file__)))
    return getcwd()

def now():
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def check_folder_exist(dir):
    if not isdir(dir):
        makedirs(dir)

def find_dims(url):
    html_page = requests.get(url).text
    soup = BeautifulSoup(html_page, 'html.parser')

    style_att=soup.find('div', id = "clipPlayer")['style']
    
    return [int(findall('width:(.*)px',style_att)[0]),int(findall('height:(.*)px',style_att)[0])]

def url_to_gif(url,base_url,save_dir):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))

    im_asarray = array(img)
    new_im_width = find_dims(base_url)[0]
    new_im_height = find_dims(base_url)[1]

    print(img.width%new_im_width==0)
    print(img.height%new_im_height==0)
    print(img.height/new_im_height)


    ims_asarrays=[Image.fromarray(im_asarray[(y)*new_im_height:(y+1)*new_im_height,(x)*new_im_width:(x+1)*new_im_width]) for y in range(img.height//new_im_height) for x in range(img.width//new_im_width)]


    # use exit stack to automatically close opened images
    with ExitStack() as stack:

        # lazily load images
        imgs = ims_asarrays

        # extract  first image from iterator
        img = next(iter(imgs))

        img.save(fp=save_dir, format='GIF', append_images=imgs,
                    save_all=True, duration=50, loop=0)


if __name__ == "__main__":
    requested_link='http://pie.med.utoronto.ca/tee/TEE_content/assets/applications/standardViewsHTML5/TEE-HTML5-SV/index.html'
    
    save_path=join(get_work_dir(),'gifs/{}'.format(now()))
    check_folder_exist(save_path)
    
    service = Service(executable_path=join(get_work_dir(),'chromedriver/chromedriver'))
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    # Go to the Google home page
    driver.get(requested_link)
    
    # Access requests via the `requests` attribute
    for request in driver.requests:
        if request.response:
            if request.response.headers['Content-Type']=='text/xml':
                xml_url=request.url,
    
    xml_str = urllib.request.urlopen(xml_url[0])
    tree = ET.parse(xml_str)
    
    jpg_base_arr=[]
    
    for x in tree.findall('./row'):
        swf_file=x.attrib['swf_spin'].split('/')[-1].split('.')[0]
        base_str=''
        for x in swf_file.split('-')[1::]:
            base_str+=x+'-'
        base_str=base_str[:-1]
    
        jpg_base_arr.append(base_str)
    
    link_arr=requested_link.split('/')
    base_url=''
    for x in link_arr[:-1]:
        base_url+=x+'/'
    base_url+='images/'
    image_url_arr=[]
    
    for x in jpg_base_arr:
        base_url_x=base_url+x
        base_url_x+='/spriteSheet_vid.jpg'
        image_url_arr.append(base_url_x)
    
    for im,base in zip(image_url_arr,jpg_base_arr):
        save_path_s=join(save_path,'{}.gif'.format(base))
        url_to_gif(im,requested_link,save_path_s)
