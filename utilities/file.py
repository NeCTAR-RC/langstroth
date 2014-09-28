from os import path

def absolute_path(file_name):
    return path.join(path.dirname(__file__), file_name)
