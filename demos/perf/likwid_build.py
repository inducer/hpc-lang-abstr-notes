from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
    void init();
    void init_thread();
    void init_openmp_threads();
    void register_region(const char *);
    void start_region(const char *);
    void stop_region(const char *);
    void finalize();
""")

ffibuilder.set_source("_likwid", """
    #include <likwid.h>

    void init()
    {
        LIKWID_MARKER_INIT;
    }

    void init_thread()
    {
        LIKWID_MARKER_THREADINIT;
    }

    void init_openmp_threads()
    {
        #pragma omp parallel
        {
            LIKWID_MARKER_THREADINIT;
        }
    }

    void register_region(const char *name)
    {
        LIKWID_MARKER_REGISTER(name);
    }

    void start_region(const char *name)
    {
        LIKWID_MARKER_START(name);
    }

    void stop_region(const char *name)
    {
        LIKWID_MARKER_STOP(name);
    }

    void finalize()
    {
        LIKWID_MARKER_CLOSE;
    }
""", libraries=['likwid'],
    define_macros=[("LIKWID_PERFMON", 1)],
    extra_compile_args=["-fopenmp"],
    extra_link_args=["-fopenmp"],
    )

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
