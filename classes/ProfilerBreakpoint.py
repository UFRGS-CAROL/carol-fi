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
        self.__kernel_list_index = kwargs.pop('list_index') if 'list_index' in kwargs else None
        self.__kernel_info_list = kwargs.pop('kernel_info_list') if 'kernel_info_list' in kwargs else None
        self.__kernel_line = kwargs.get('spec')

        super(ProfilerBreakpoint, self).__init__(*args, **kwargs)

    def stop(self):
        if cp.DEBUG_PROFILER:
            print("IT IS IN STOP METHOD")
        if self.__kludge:
            return True

        # for kernel_info in self.__kernel_info_list:
        #     if kernel_info["breakpoint"].__kernel_line == self.__kernel_line:
        #         if cp.DEBUG_PROFILER:
        print("FOUND A KERNEL LINE {}".format(self.__kernel_line))

        self.__generate_source_ass_list()

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
            print(l)

        last_not_zero_size = None
        ret_source = []
        for l, ass_line in source_list:

            # I have to merge with
            if len(ass_line) is not 0:
                last_not_zero_size = l
                self.__ret_source.append([l, ass_line])
            else:
                last_not_zero_size.append(l)

        self.__kernel_info_list[self.__kernel_list_index]['addresses'] = ret_source
