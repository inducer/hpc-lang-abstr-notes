# http://igoro.com/archive/gallery-of-processor-cache-effects/

import os
from time import time
import matplotlib.pyplot as plt
import numpy as np
from codepy.toolchain import guess_toolchain

toolchain = guess_toolchain()

from codepy.libraries import add_boost_python

add_boost_python(toolchain)


MODULE_CODE = """
#include <boost/scoped_array.hpp>
#include <boost/python.hpp>

%s

BOOST_PYTHON_MODULE(module)
{
  boost::python::def("go", &go);
}
"""


def measure_strides():
    FUNC_CODE = """
    int go(unsigned count, unsigned stride)
    {
      const unsigned array_size = 64 * 1024 * 1024;
      int *ary = (int *) malloc(sizeof(int) * array_size);

      for (unsigned it = 0; it < count; ++it)
      {
        for (unsigned i = 0; i < array_size; i += stride)
          ary[i] *= 17;
      }

      int result = 0;
      for (unsigned i = 0; i < array_size; ++i)
          result += ary[i];

      free(ary);
      return result;
    }
    """
    from codepy.jit import extension_from_string

    cmod = extension_from_string(toolchain, "module", MODULE_CODE % FUNC_CODE)

    strides = []
    times = []

    count = 30
    for stride in [2**i for i in range(0, 11)]:
        start = time()
        cmod.go(count, stride)
        stop = time()

        strides.append(stride)
        times.append((stop - start) / count)

    plt.clf()
    plt.rc("font", size=20)
    plt.semilogx(strides, times, "o-", base=2)
    plt.xlabel("Stride")
    plt.ylabel("Time [s]")
    plt.grid()
    plt.tight_layout()
    plt.savefig("strides.pdf")

    with open("strides.c", "w") as outf:
        outf.write(FUNC_CODE)

    os.system("pdfcrop strides.pdf")


def measure_strides_constant_work():
    # came up during a discussion in s25
    FUNC_CODE = """
    int go(unsigned count, unsigned stride)
    {
      const unsigned array_size = 64 * 1024 * 1024;
      int *ary = (int *) malloc(sizeof(int) * array_size);

      for (unsigned it = 0; it < count * stride; ++it)
      {
        for (unsigned i = 0; i < array_size; i += stride)
          ary[i] *= 17;
      }

      int result = 0;
      for (unsigned i = 0; i < array_size; ++i)
          result += ary[i];

      free(ary);
      return result;
    }
    """
    from codepy.jit import extension_from_string

    cmod = extension_from_string(toolchain, "module", MODULE_CODE % FUNC_CODE)

    strides = []
    times = []

    count = 10
    for stride in [2**i for i in range(0, 11)]:
        start = time()
        cmod.go(count, stride)
        stop = time()

        strides.append(stride)
        times.append((stop - start) / count)

    plt.clf()
    plt.rc("font", size=20)
    plt.semilogx(strides, times, "o-", base=2)
    plt.xlabel("Stride")
    plt.ylabel("Time [s]")
    plt.grid()
    plt.tight_layout()
    plt.show()


def measure_cache_bandwidths():
    FUNC_CODE = """
    int go(unsigned array_size, unsigned steps)
    {
      int *ary = (int *) malloc(sizeof(int) * array_size);
      unsigned asm1 = array_size - 1;

      for (unsigned i = 0; i < 100*steps;)
      {
        #define ONE ary[(i++*16) & asm1] ++;
        #define FIVE ONE ONE ONE ONE ONE
        #define TEN FIVE FIVE
        #define FIFTY TEN TEN TEN TEN TEN
        #define HUNDRED FIFTY FIFTY
        HUNDRED
      }

      int result = 0;
      for (unsigned i = 0; i < array_size; ++i)
          result += ary[i];

      free(ary);
      return result;
    }
    """
    from codepy.jit import extension_from_string

    cmod = extension_from_string(toolchain, "module", MODULE_CODE % FUNC_CODE)

    sizes = []
    bandwidths = []

    steps = 2 ** (26 - 7)
    for array_size in [2**i for i in range(10, 27)]:
        start = time()
        cmod.go(array_size, steps)
        stop = time()

        sizes.append(array_size * 4)
        elapsed = stop - start

        gb_transferred = 2 * 100 * steps * 4 / 1e9  # 2 for rw, 4 for sizeof(int)
        bandwidth = gb_transferred / elapsed

        bandwidths.append(bandwidth)

        print(array_size, bandwidth)

    plt.clf()
    plt.rc("font", size=20)
    plt.plot(sizes, bandwidths, "o-", label="Single-item")
    plt.plot(sizes, 16 * np.array(bandwidths), "--", label="~Cache line")
    plt.xscale("log", base=2)
    plt.yscale("log")
    plt.xlabel("Array Size [Bytes]")
    plt.ylabel("Eff. Bandwidth [GB/s]")
    plt.grid()
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig("bw.pdf")

    with open("bw.c", "w") as outf:
        outf.write(FUNC_CODE)

    os.system("pdfcrop bw.pdf")


def find_associativity():
    FUNC_CODE = """
    int go(unsigned array_size, unsigned stride, unsigned steps)
    {
      char *ary = (char *) malloc(sizeof(int) * array_size);

      unsigned p = 0;
      for (unsigned i = 0; i < steps; ++i)
      {
        ary[p] ++;
        p += stride;
        if (p >= array_size)
          p = 0;
      }

      int result = 0;
      for (unsigned i = 0; i < array_size; ++i)
          result += ary[i];

      free(ary);
      return result;
    }
    """
    from codepy.jit import extension_from_string

    cmod = extension_from_string(toolchain, "module", MODULE_CODE % FUNC_CODE)

    result = {}

    steps = 2**20
    from pytools import ProgressBar

    meg_range = range(1, 25)
    stride_range = range(1, 640)
    pb = ProgressBar("bench", len(meg_range) * len(stride_range))
    for array_megs in meg_range:
        for stride in stride_range:
            start = time()
            cmod.go(array_megs << 20, stride, steps)
            stop = time()

            elapsed = stop - start
            gb_transferred = 2 * steps / 1e9  # 2 for rw, 4 for sizeof(int)
            bandwidth = gb_transferred / elapsed

            result[array_megs, stride] = bandwidth
            pb.progress()

    from pickle import dump

    with open("assoc_result.dat", "wb") as outf:
        dump(result, outf)

    with open("assoc.c", "w") as outf:
        outf.write(FUNC_CODE)


def plot_associativity(infile, outfile):
    from pickle import load

    with open(infile, "rb") as inf:
        results = load(inf)

    megs = sorted(set(k[0] for k in results.keys()))
    strides = sorted(set(k[1] for k in results.keys()))

    ary = np.zeros((len(megs), len(strides)))
    for i_m, meg in enumerate(megs):
        for i_s, stride in enumerate(strides):
            ary[i_m, i_s] = results[meg, stride]

    plt.clf()
    plt.rc("font", size=20)
    plt.imshow(
        np.log(ary),
        origin="lower",
        extent=(min(strides), max(strides), min(megs), max(megs)),
        interpolation="nearest",
        aspect="auto",
    )
    plt.xlabel("Stride [bytes]")
    plt.ylabel("Array Size [MB]")
    plt.tight_layout()
    plt.savefig(outfile)

    os.system(f"pdfcrop {outfile}")


if __name__ == "__main__":
    # measure_strides()
    measure_strides_constant_work()
    # measure_cache_bandwidths()
    # find_associativity()
    # plot_associativity("assoc_result.dat", "assoc.pdf")
    # plot_associativity("assoc_result_sandy.dat", "assoc-sandy.pdf")
