"""
This parser will parse all information created on
bug fixes on darknet
"""

import os

INDIR = "/tmp/double_fi/logs/{}"
OUTDIR = "/tmp/double_fi/sdc_logs/{}"


def insert_sdc_in_errors(file_data):
    sdc_not_mapped = []
    i = 0
    lines_mapped = 0
    for line in file_data:
        if 'SDC' in line:
            lines_mapped += 1

        try:
            if 'ERR' in line and 'ERR' not in file_data[i + 1] and 'SDC' not in file_data[i + 1]:
                sdc_not_mapped.append(i)
        except:
            sdc_not_mapped.append(i)

        i += 1

    sdc_line = "#SDC Ite:{} KerTime:3.928865 AccTime:10.571838 KerErr:1 AccErr:1\n"
    for ll in sdc_not_mapped:
        lines_mapped += 1
        file_data.insert(ll + 1, sdc_line.format(lines_mapped))

    return file_data


all_files = [f for f in os.listdir(INDIR.format(''))]

for log_file in all_files:
    with open(INDIR.format(log_file), "r") as fp:
        file_data_full = fp.readlines()

    err_in_file = False
    sdc_in_file = False
    for dt in file_data_full:
        if 'ERR' in dt:
            err_in_file = True

        if 'SDC' in dt:
            sdc_in_file = True

    if sdc_in_file is False and err_in_file is True:
        # wrong file
        output = insert_sdc_in_errors(file_data=file_data_full)

        with open(OUTDIR.format(log_file), "w") as fo:
            fo.writelines(output)
