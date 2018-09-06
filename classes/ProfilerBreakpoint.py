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
        self.__kernel_line = kwargs.get('spec')
        self.__kernel_info_list = None
        self.__first_pass = True
        super(ProfilerBreakpoint, self).__init__(*args, **kwargs)

    def set_kernel_info_list(self, kernel_info_list):
        # This list will contains all kernel info
        self.__kernel_info_list = kernel_info_list

    def stop(self):
        if cp.DEBUG_PROFILER:
            print("IT IS IN STOP METHOD")
        if self.__kludge:
            return True

        for kernel_info in self.__kernel_info_list:
            if kernel_info["breakpoint"].__kernel_line == self.__kernel_line:
                if cp.DEBUG_PROFILER:
                    print("FOUND A KERNEL LINE {}".format(kernel_info["breakpoint"].__kernel_line))
                #
                # kernel_info["threads"] = cf.execute_command(gdb, "info cuda threads")
                kernel_info["addresses"] = self.__generate_source_ass_list()

    """
    inject faults only on the resources used at that source line
    """
    @staticmethod
    def __generate_source_ass_list():
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
        ret_source = []
        for l, ass_line in source_list:

            # I have to merge with
            if len(ass_line) is not 0:
                last_not_zero_size = l
                ret_source.append([l, ass_line])
            else:
                last_not_zero_size.append(l)

        for t in ret_source:
            print(t[0])
        return source_list
