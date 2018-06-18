import os
import tempfile
import time
import unittest

from unittest.mock import Mock
from Xlib.error import DisplayError

import termtosvg.__main__ as __main__
import termtosvg.term as term

SHELL_COMMANDS = [
    'echo $SHELL && sleep 0.1;\r\n',
    'tree && 0.1;\r\n',
    'ls && sleep 0.1;\r\n',
    'w',
    'h',
    'o',
    'a',
    'm',
    'i\r\n',
    'exit;\r\n'
]


# TODO: Replace os.pipe + fork by Popen ?
class TestMain(unittest.TestCase):
    def test_parse(self):
        test_cases = [
            [],
            ['--theme', 'solarized-light'],
            ['--verbose'],
            ['--theme', 'solarized-light', '--verbose'],
            ['--theme', 'solarized-light'],
            ['record'],
            ['record', 'output_filename'],
            ['record', 'output_filename', '--verbose'],
            ['record', '--verbose'],
            ['render', 'input_filename'],
            ['render', 'input_filename', '--verbose'],
            ['render', 'input_filename', '--verbose', '--theme', 'solarized-light'],
            ['render', 'input_filename', '--theme', 'solarized-light'],
            ['render', 'input_filename', 'output_filename'],
            ['render', 'input_filename', 'output_filename', '--verbose'],
            ['render', 'input_filename', 'output_filename', '--verbose', '--theme', 'solarized-light'],
            ['render', 'input_filename', 'output_filename', '--theme', 'solarized-light'],
        ]

        for args in test_cases:
            with self.subTest(case=args):
                __main__.parse(args)

    @staticmethod
    def run_main(shell_commands, args):
        # Use pipes in lieu of stdin and stdout
        fd_in_read, fd_in_write = os.pipe()
        fd_out_read, fd_out_write = os.pipe()

        pid = os.fork()
        if pid == 0:
            # Child process
            for line in shell_commands:
                os.write(fd_in_write, line.encode('utf-8'))
                time.sleep(0.060)
            os._exit(0)

        __main__.main(args, fd_in_read, fd_out_write)

        os.waitpid(pid, 0)
        for fd in fd_in_read, fd_in_write, fd_out_read, fd_out_write:
            os.close(fd)

    def test_main(self):
        _, cast_filename = tempfile.mkstemp(prefix='termtosvg_', suffix='.cast')
        svg_filename = cast_filename[:-5] + '.svg'

        with self.subTest(case='record (no filename)'):
            # Force use of fallback theme by mocking _get_x_resources
            get_x_mock = Mock(side_effect=DisplayError(None))
            with unittest.mock.patch('termtosvg.term._get_xresources', get_x_mock):
                args = ['termtosvg', 'record']
                TestMain.run_main(SHELL_COMMANDS, args)

        with self.subTest(case='record (with filename)'):
            # Force use of fallback theme by mocking _get_x_resources
            get_x_mock = Mock(side_effect=DisplayError(None))
            with unittest.mock.patch('termtosvg.term._get_xresources', get_x_mock):
                args = ['termtosvg', 'record', cast_filename]
                TestMain.run_main(SHELL_COMMANDS, args)

        with self.subTest(case='render (no filename)'):
            args = ['termtosvg', 'render', cast_filename]
            TestMain.run_main([], args)

        with self.subTest(case='render (with filename)'):
            args = ['termtosvg', 'render', cast_filename, svg_filename]
            TestMain.run_main([], args)

        with self.subTest(case='render (with theme)'):
            args = ['termtosvg', 'render', cast_filename, '--theme', 'circus']
            TestMain.run_main([], args)

        with self.subTest(case='record and render on the fly (fallback theme)'):
            # Force use of fallback theme by mocking _get_x_resources]
            get_x_mock = Mock(side_effect=DisplayError(None))
            with unittest.mock.patch('termtosvg.term._get_xresources', get_x_mock):
                args = ['termtosvg', '--verbose']
                TestMain.run_main(SHELL_COMMANDS, args)

        with self.subTest(case='record and render on the fly (system theme)'):
            # Mock color info gathering
            xresources_dracula = term.default_themes()['dracula']
            get_x_mock = Mock(return_value=xresources_dracula)
            with unittest.mock.patch('termtosvg.term._get_xresources', get_x_mock):
                args = ['termtosvg', '--verbose', svg_filename]
                TestMain.run_main(SHELL_COMMANDS, args)

        with self.subTest(case='record and render on the fly (system theme)'):
            # Mock color info gathering
            xresources_dracula = term.default_themes()['dracula']
            get_x_mock = Mock(return_value=xresources_dracula)
            with unittest.mock.patch('termtosvg.term._get_xresources', get_x_mock):
                args = ['termtosvg', svg_filename, '--theme', 'circus', '--verbose']
                TestMain.run_main(SHELL_COMMANDS, args)