import os

texture_directory_relative = '..\\..\\textures\\'


def fix_all_texture_dirs(root_dir):
    print('\n\n\n')
    print('walk begin')
    for dirpath, dirnames, files in os.walk(root_dir):
        for name in files:
            if '.dae' in files:
                dae_file_path = os.path.join(dirpath, name)
                if not has_fixed_texture_dir(dae_file_path):
                    print(name)
                    find_replace_image_dir(dae_file_path)


def has_fixed_texture_dir(dae_file_path):
    with open(dae_file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if 'png' in line and '<init_from>' in line:
                if 'textures' in line:
                    return True
                else:
                    return False
    return False


def find_replace_image_dir(dae_file_path):
    linesToWrite = []
    with open(dae_file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if 'png' in line:
                line = line.replace("<init_from>", "<init_from>"+texture_directory_relative)
                print(line)
            linesToWrite += [line]
    with open(dae_file_path, 'w') as file:
        file.writelines(linesToWrite)


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
else:
    print(f"{__file__} is being imported")
