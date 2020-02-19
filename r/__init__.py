import argparse
import pathlib
import re
import subprocess
import sys

import toml


def log(message, *args):
    print('r:', message.format(*args), file=sys.stderr, flush=True)


class UserError(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--init',
        action='store_true')

    parser.add_argument(
        'cmdline',
        nargs='...',
        help='The command to execute with the remote shell.')

    args = parser.parse_args()

    if args.init and args.cmdline:
        parser.error('Cannot use --init together with a command line.')

    return args


def bash_escape_string(string):
    # Wrap the string in single quotes and escape each quote in the string
    # (which only works outside of single quotes).
    return "'{}'".format(re.sub("'", "'\\''", string))


class Config:
    def __init__(self, *, root_directory, remote_host, remote_path, name_ignores, path_ignores):
        # Directory containing the config file.
        self.root_directory = root_directory
        self.remote_host = remote_host
        self.remote_path = remote_path
        self.name_ignores = name_ignores
        self.path_ignores = path_ignores


def find_config_file():
    path = pathlib.Path().resolve()

    for i in [path, *path.parents]:
        config_file_path = i / 'r.toml'

        if config_file_path.is_file():
            return config_file_path

    return None


def load_config():
    config_file_path = find_config_file()

    if config_file_path is None:
        raise UserError(
            'No config file r.toml found in the current directory or any of '
            'its parents.')

    config = toml.load(config_file_path)
    remote_host, remote_path = config['remote'].split(':', 1)

    name_ignores = []
    path_ignores = []

    for i in config.get('ignores', []):
        if i.startswith('/'):
            path_ignores.append(i[1:])
        else:
            # Ignores must either be the pattern for a full path relative to
            # the directory containing the r.conf file or a pattern for a
            # file or directory name.
            assert '/' not in i

            name_ignores.append(i)

    return Config(
        root_directory=config_file_path.parent,
        remote_host=remote_host,
        remote_path=pathlib.Path(remote_path),
        name_ignores=name_ignores,
        path_ignores=path_ignores)


def main(init, cmdline):
    if init:
        config_path = pathlib.Path('r.toml')

        if config_path.exists():
            raise UserError(f'Config file {config_path} already exists.')

        print('Please enter the address of the remote directory in the form <hostname>:<path>:')
        remote = input('? ')

        config=dict(remote=remote, ignores=[])

        log(f'Saving configuration to {config_path} ...')

        with config_path.open('w', encoding='utf-8') as file:
            toml.dump(config, file)
    else:
        config = load_config()

        # Path of the current working directory relative to the directory
        # containing the config file.
        relative_path = pathlib.Path().resolve().relative_to(config.root_directory)

        def run_unison():
            def iter_ignore_args():
                ignore_sets = [
                    ('Name', config.name_ignores),
                    ('Path', config.path_ignores)]

                for type, ignores in ignore_sets:
                    for ignore in ignores:
                        yield '-ignore'
                        yield type + ' ' + ignore

            unison_cmd = [
                'unison',
                '-batch',
                '-silent',
                # '-confirmbigdel=false',
                '-logfile=/dev/null',
                '-copyonconflict',
                '-prefer=newer',
                *iter_ignore_args(),
                str(config.root_directory),
                'ssh://{}/{}'.format(config.remote_host, config.remote_path)]

            exit_code = subprocess.call(unison_cmd, stdin=None)

            if exit_code:
                raise UserError('Command failed: {}'.format(' '.join(unison_cmd)))

        def run_ssh():
            remote_dir = config.remote_path / relative_path
            cmdline_str = ' '.join(bash_escape_string(i) for i in cmdline)
            command = 'cd {}; {}'.format(remote_dir, cmdline_str)

            return subprocess.call(['ssh', config.remote_host, command])

        run_unison()
        exit_code = run_ssh()
        run_unison()

        sys.exit(exit_code)


def entry_point():
    try:
        main(**vars(parse_args()))
    except KeyboardInterrupt:
        log('Operation interrupted.')
        sys.exit(1)
    except UserError as e:
        log('error: {}', e)
