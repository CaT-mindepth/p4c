import subprocess
import sys
import os
import time

from os import path

BASE_PATH = path.abspath(path.dirname(__file__))

BINARY_CODE_DIR = path.join(BASE_PATH, './build')
P4_FILE_DIR = path.join(BASE_PATH, './sample_input_output/testfile_for_table_dep')

filename_list = ['test_action.p4', 'test_match.p4', 'test_reverse.p4', 'test_successor.p4']

for i in range(len(filename_list)):
    # Run p4c-graphs
    args = path.join(BINARY_CODE_DIR, 'p4c-graphs') + ' ' +  path.join(P4_FILE_DIR, filename_list[i])
    os.popen(args)

    # Sleep for some time to wait until dot file is generated
    time.sleep(2)

    # run get table dependency
    cmd_line_table_dep = 'python3 ' + path.join(BASE_PATH, './get_table_dep.py')
    (ret_code2, output) = subprocess.getstatusoutput(cmd_line_table_dep)

    if ret_code2 != 0:
        print('Fail to run get_table_dep script')
        sys.exit(1)
    if filename_list[i] == 'test_action.p4':
        assert output.find('smac_vlan has Action dependency relationship with dmac_vlan') != -1, 'Test does not pass for ' + filename_list[i]
    if filename_list[i] == 'test_match.p4':
        assert output.find('smac_vlan has Match dependency relationship with dmac_vlan') != -1, 'Test does not pass for ' + filename_list[i]
    if filename_list[i] == 'test_reverse.p4':
        assert output.find('smac_vlan has Reverse dependency relationship with dmac_vlan') != -1, 'Test does not pass for ' + filename_list[i]
    if filename_list[i] == 'test_successor.p4':
        assert output.find('dmac_vlan has Successor dependency relationship with sample') != -1, 'Test does not pass for ' + filename_list[i]

print('Test passes!!')
