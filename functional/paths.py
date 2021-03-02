import pathlib

PROJECT_NAME = 'SubVPbot'
DB_DIRECTORY = 'db'
DB_NAME = 'ttdb.db'


def get_project_path():
    current_directory_path = pathlib.Path().cwd()
    project_path = ''

    for parent_path in current_directory_path.parents:
        parent_path_parts = parent_path.parts
        if parent_path_parts[len(parent_path_parts) - 1] == PROJECT_NAME:
            project_path = parent_path
            break

    return project_path


def get_tt_db_path():
    project_path = get_project_path()

    db_path = pathlib.Path(project_path, DB_DIRECTORY, DB_NAME)

    return db_path


def get_old_db_path():
    project_path = get_project_path()

    db_path = pathlib.Path(project_path, DB_DIRECTORY, 'data.db')

    return db_path

