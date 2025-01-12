
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
    