from os import path

def absolute_path(file_name, context=__file__):
    return path.join(path.dirname(context), file_name)
