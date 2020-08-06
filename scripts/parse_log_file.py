"""
This parser will parse all information created on
CAROL-FI CUDA
"""

from sys import argv

MAX_REGISTER_NUMBER = 255


def main():
    """
    Main function
    :param: none
    :return: none
    """
    assert len(argv) < 3, "usage: {}.py <csv_path>".format(argv[0])
    csv_path = argv[1]


if __name__ == '__main__':
    main()
