import _likwid
import atexit

_likwid.lib.init()
init_thread = _likwid.lib.init_thread
init_openmp_threads = _likwid.lib.init_openmp_threads

atexit.register(_likwid.lib.finalize)


class Region(object):
    def __init__(self, name):
        self.name = name.encode()
        _likwid.lib.register_region(self.name)

    def __enter__(self):
        _likwid.lib.start_region(self.name)

    def __exit__(self, *args):
        _likwid.lib.stop_region(self.name)
