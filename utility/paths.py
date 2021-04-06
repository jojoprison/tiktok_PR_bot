import pathlib
from sys import platform

PROJECT_NAME = 'SubVPbot'


# путь к проекту
def get_project_root_path():
    current_path = pathlib.Path().cwd()

    project_path = None

    if current_path.name == PROJECT_NAME:
        project_path = current_path
    else:
        for parent_path in current_path.parents:
            parent_path_parts = parent_path.parts
            if parent_path_parts[len(parent_path_parts) - 1] == PROJECT_NAME:
                project_path = parent_path
                break

    return project_path


def get_chromedriver_path():
    # проверяем ось, с которой запускается бот
    if platform.startswith('linux'):
        driver_path = get_project_root_path().joinpath('chromedriver_linux')
    # win32
    else :
        driver_path = get_project_root_path().joinpath('chromedriver.exe')

    print(driver_path)
    print(type(driver_path))

    return driver_path
