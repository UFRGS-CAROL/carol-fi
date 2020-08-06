"""
This parser will parse all information created on
CAROL-FI CUDA
"""

from sys import argv
import pandas as pd

MAX_REGISTER_NUMBER = 255


def main():
    """
    Main function
    :param: none
    :return: none
    """
    assert len(argv) >= 2, "usage: {}.py <csv_path> [output path for xlsx optional]".format(argv[0])
    csv_path = argv[1]
    avf_log_df = pd.read_csv(csv_path)
    histogram = avf_log_df[['sdc', 'hang', 'crash', 'register', 'instruction']]
    inst_histogram = histogram['instruction'].value_counts(normalize=True)
    rf_histogram = histogram['register'].value_counts(normalize=True)
    avf = histogram[['sdc', 'hang', 'crash']].astype(int)
    avf['sdc'] = avf['sdc'].value_counts()
    avf['hang'] = avf['hang'].value_counts()
    avf['crash'] = avf['crash'].value_counts()
    avf = avf.dropna(how='all')
    avf = avf.transpose().rename(columns={0: "Negative", 1: "Positive"})

    output_path = 'output.xlsx'
    if len(argv) == 3:
        output_path = argv[2]

    with pd.ExcelWriter(output_path) as writer:
        inst_histogram.to_excel(writer, sheet_name='INST histogram')
        rf_histogram.to_excel(writer, sheet_name='RF histogram')
        avf.to_excel(writer, sheet_name='AVF')


if __name__ == '__main__':
    main()
