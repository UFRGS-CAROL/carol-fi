"""
This parser will parse all information created on
bug fixes on darknet
"""
import csv
import os
import sys

INDIR = sys.argv[1] + "/log/{}"
CSV_FILE = sys.argv[2]
OUTDIR = sys.argv[1] + "/sdc_logs/{}"


def insert_sdc_in_errors(fname, file_data):
    lines_mapped = 6
    sdc_line = "#SDC Ite:{} KerTime:3.928865 AccTime:10.571838 KerErr:1 AccErr:1\n"

    for i, line in enumerate(file_data):
        if 'ERR' in line:
            try:
                if ('IT' in file_data[i + 1] or 'END' in file_data[i + 1]) and 'SDC' not in file_data[i + 1]:
                    lines_mapped += 1
                    file_data.insert(i + 1, sdc_line.format(lines_mapped))
            except:
                print fname
                lines_mapped += 1
                file_data.insert(i + 1, sdc_line.format(lines_mapped))

    return file_data

with open(CSV_FILE, "r") as fp:
    reader = csv.DictReader(fp)
    all_files = [f['log_file'] for f in reader]

for log_file in all_files:
    with open(INDIR.format(log_file), "r") as fp:
        file_data_full = fp.readlines()

    check_file = False
    for ll in file_data_full:
        if 'ERR' in ll:
            check_file = True
            break
    output = file_data_full
    # wrong file
    if check_file:
        output = insert_sdc_in_errors(fname=log_file, file_data=file_data_full)

    with open(OUTDIR.format(log_file), "w") as fo:
        fo.writelines(output)
