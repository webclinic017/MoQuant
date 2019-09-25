import json
import os


def from_file(file_name: str) -> object:
    module_path = os.path.dirname(os.path.dirname(__file__))
    file_path_name = module_path + file_name
    info_file = open(file_path_name, encoding='utf-8')
    return json.load(info_file)
