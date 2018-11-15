import csv
import os

"""
Class SummaryFile: this class will write the information
of each injection in a csv file to make easier data
parsing after fault injection
"""


class SummaryFile:
    # Filename
    __filename = ""
    # csv file
    __csv_file = None
    # Dict reader
    __dict_buff = None

    # Fieldnames
    __fieldnames = None

    # It will only open in a W mode for the first time
    def __init__(self, **kwargs):
        # Set arguments
        self.__filename = kwargs.get("filename")
        self.__fieldnames = kwargs.get("fieldnames")

        # Open and start csv file
        self.__open_csv(mode='w')
        self.__dict_buff.writeheader()
        self.__close_csv()

    """
    Open a file if it exists
    mode can be r or w
    default is r
    """

    def __open_csv(self, mode='a'):
        if os.path.isfile(self.__filename):
            self.__csv_file = open(self.__filename, mode)
        elif mode == 'w':
            self.__csv_file = open(self.__filename, mode)
        else:
            raise IOError(str(self.__filename) + " FILE NOT FOUND")

        # If file exists it is append or read
        if mode in ['w', 'a']:
            self.__dict_buff = csv.DictWriter(self.__csv_file, self.__fieldnames)
        elif mode == 'r':
            self.__dict_buff = csv.DictReader(self.__csv_file)

    """
    To not use __del__ method, close csv file
    """

    def __close_csv(self):
        if not self.__csv_file.closed:
            self.__csv_file.close()
        self.__dict_buff = None

    """
    Write a csv row, if __mode == w or a
    row must be a dict
    """

    def write_row(self, row):
        # If it is a list must convert first
        row_ready = {}
        if isinstance(row, list):
            for fields, data in zip(self.__fieldnames, row):
                row_ready[fields] = data
        else:
            row_ready = row

        # Open file first
        self.__open_csv()
        self.__dict_buff.writerow(row_ready)
        self.__close_csv()

    """
    Read rows
    return read rows from file in a list
    """

    def read_rows(self):
        self.__open_csv()
        rows = [row for row in self.__dict_buff]
        self.__close_csv()
        return rows

    """
    Write series of rows to csv
    """

    def write_rows(self, rows_list):
        self.__open_csv()
        for row in rows_list:
            row_ready = {}
            if isinstance(row, list):
                for fields, data in zip(self.__fieldnames, row):
                    row_ready[fields] = data
            else:
                row_ready = row
            self.__dict_buff.writerow(row_ready)
        self.__close_csv()
