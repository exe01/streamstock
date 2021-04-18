import tempfile
import os


def delete_file(path):
    os.remove(path)


def create_file(data=None, name=None, suffix=None, dir=None):
    if dir is None:
        dir = tempfile.mkdtemp()

    if name is None:
        file = tempfile.NamedTemporaryFile(dir=dir, suffix=suffix, delete=False)
    else:
        if dir.endswith('/'):
            file_path = '{}{}'.format(dir, name)
        else:
            file_path = '{}/{}'.format(dir, name)
        file = open(file_path, mode='wb')

    if data:
        if type(data) == str:
            data = data.encode('utf-8')

        file.write(data)
        file.flush()

    file.close()
    return file.name


def create_folder():
    return tempfile.mkdtemp()
