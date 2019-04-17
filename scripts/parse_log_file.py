"""
This parser will parse all information created on
CAROL-FI CUDA
"""

from sys import argv
from csv import DictReader, DictWriter

MAX_REGISTER_NUMBER = 255


def check_sdc_and_crash(log_file, log_path):
    with open("{}/{}".format(log_path, log_file), "r") as fp:
        data = fp.read()
        # print log_file
        crash = False
        sdc = False
        if 'ERR' in data:
            sdc = True
        if 'END' not in data:
            crash = True
        return sdc, crash


def main(csv_path, log_path):
    """
    Main function
    :param csv_path: path to csv file
    :return: none
    """
    with open(csv_path, "r") as csv_file:
        csv_reader = DictReader(csv_file)
        csv_data = list(csv_reader)

    register_fi_histogram = {"R{}".format(r): [0, 0, 0] for r in range(0, MAX_REGISTER_NUMBER)}

    # only register histogram
    for reg in csv_data:
        register_fi_histogram[reg['register']][0] += 1
        if reg['log_file'] == '':
            continue
        sdc, crash = check_sdc_and_crash(log_file=reg['log_file'], log_path=log_path)
        register_fi_histogram[reg['register']][1] += int(sdc)
        register_fi_histogram[reg['register']][2] += int(crash)

    csv_output_path = csv_path.replace(".csv", "_output_parsed.csv")
    with open(csv_output_path, "w") as csv_output_file:
        fieldnames = ['register', 'count', 'sdc', 'crash']
        writer = DictWriter(csv_output_file, fieldnames=fieldnames)

        writer.writeheader()
        for reg in range(0, MAX_REGISTER_NUMBER):
            reg_key = "R{}".format(reg)
            writer.writerow(
                {'register': reg_key,
                 'count': register_fi_histogram[reg_key][0],
                 'sdc': register_fi_histogram[reg_key][1],
                 'crash': register_fi_histogram[reg_key][2]}
            )


if __name__ == '__main__':
    csv_path = argv[1]
    log_path = argv[2]
    main(csv_path=csv_path, log_path=log_path)
