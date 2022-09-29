import sys
import os
import time

def main():
    if not os.path.isdir('map_data'):
        print('No map_data found')
        return
    start_time = time.time()

    argv = sys.argv
    try:
        index = argv.index("--") + 1
    except ValueError:
        index = len(argv)
    argv = argv[index:]
    if argv and argv[0]:
        func_to_run = argv[0]
        if 'terrain' in func_to_run.lower():
            from scripts.map.map_generator_terrain import main
            main()
        elif 'water' in func_to_run.lower():
            from scripts.map.map_generator_water import main
            main()
        else:
            print('function not found')
    else:
        print('Try calling one of the available functions')

    end_time = time.time()
    sec = end_time - start_time
    print(f'\nCompleted in {sec} seconds.\n')
    return


if __name__ == "__main__":
    # print(f"{__file__} is being run directly")
    sys.path.append(os.path.abspath("."))
    main()
else:
    # print(f"{__file__} is being imported")
    sys.path.append(os.path.abspath("."))

