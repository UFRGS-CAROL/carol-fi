import gdb
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

"""
ProfilerBreakpoint class
will manager the breakpoint event when gdb stops
"""


class ProfilerBreakpoint(gdb.Breakpoint):
    def __init__(self, *args, **kwargs):
        if cp.DEBUG_PROFILER:
            print("IT IS IN __INIT__ METHOD")
        self.__kludge = kwargs.pop('kludge') if 'kludge' in kwargs else False
        self.__kernel_name = kwargs.pop('kernel_name') if 'kernel_name' in kwargs else None
        self.__kernel_line = kwargs.pop('kernel_line') if 'kernel_line' in kwargs else None
        self.__kernel_end_line = kwargs.pop('kernel_end_line') if 'kernel_end_line' in kwargs else None
        self.__inf_file_path = kwargs.pop('inf_file_path') if 'inf_file_path' in kwargs else None

        self.__addresses = None
        self.__kernel_line = kwargs.get('spec')

        super(ProfilerBreakpoint, self).__init__(*args, **kwargs)

    def stop(self):
        if cp.DEBUG_PROFILER:
            print("IT IS IN STOP METHOD")
        if self.__kludge:
            return True

        print("FOUND A KERNEL LINE {}".format(self.__kernel_line))
        self.__generate_source_ass_list()
        self.__append_to_file()

    """
    inject faults only on the resources used at that source line
    """

    def __generate_source_ass_list(self):
        source_list = []
        assemble_lines = []
        disassemble_gdb = cf.execute_command(gdb, "disassemble /m")
        for l in disassemble_gdb:
            if '0x' in l:
                assemble_lines.append(l)
            else:
                source_list.append([[l], assemble_lines[:]])
                assemble_lines = []

        last_not_zero_size = None
        self.__addresses = []
        for l, ass_line in source_list:
            # I have to merge with
            if len(ass_line) is not 0:
                last_not_zero_size = l
                self.__addresses.append([l, ass_line])
            else:
                last_not_zero_size.append(l)


    """
    set kernel_info list
    """

    def __append_to_file(self):
        kernel_info = {
            'addresses': self.__addresses,
            'kernel_name': self.__kernel_name,
            'kernel_line': self.__kernel_line,
            'kernel_end_line': self.__kernel_end_line
        }
        cf.append_file(self.__file_path, kernel_info)