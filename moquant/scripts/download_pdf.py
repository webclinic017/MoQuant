import os
from urllib import request

from lxml import etree

from moquant.log import get_logger
from moquant.utils import env_utils

log = get_logger(__name__)


def full_file_path_name(dt, file_name):
    parent_dir = os.path.join(env_utils.forecast_saved_path(), dt)
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)
    file_path = os.path.join(parent_dir, file_name)
    return file_path

def split_name_code(name_code: str):
    name_code_arr = name_code.split('(')
    return name_code_arr[0], name_code_arr[1][:-1]

def format_file_name(name: str, code: str, col_val: str):
    short_name = col_val[col_val.index(name) + len(name):]
    if short_name.startswith(':'):
        short_name = short_name[1:]
    return '%s-%s-%s.pdf' % (code, name, short_name)


def forecast():
    html_path = env_utils.forecast_html_path()
    if os.path.exists(html_path):
        log.warn('File not found: %s' % html_path)
    html_file = open(html_path, 'r', encoding='utf-8')
    html_str = html_file.read()
    html = etree.HTML(html_str)
    rows = html.xpath('//body//table[@id="FavoriteTable"]/tbody/tr')
    for row in rows:
        columns = row.xpath('td')
        dt = columns[1].text
        corp_name, code = split_name_code(columns[2].attrib['title'])
        file_name = format_file_name(corp_name, code, columns[3].attrib['title'])
        full = full_file_path_name(dt, file_name)
        download_url = columns[4].xpath('img')[0].attrib['url']
        if os.path.exists(full):
            log.info('file already exists. skip. %s' % file_name)
        else:
            download_stream = request.urlopen(download_url)
            download_data = download_stream.read()
            with open(full, "wb") as file_writer:
                file_writer.write(download_data)
            log.info('Downloaded. %s' % file_name)


if __name__ == '__main__':
    forecast()
