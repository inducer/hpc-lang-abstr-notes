
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
    