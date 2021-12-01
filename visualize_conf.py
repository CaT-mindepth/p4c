import sys

container_type_dic = {
        '01' : '2B',
        '10' : '4B',
        '11' : '6B'
        }

opcode_dir = {
        '0001' : 'add',
        '1011' : 'load',
        '0111' : 'loadd',
        '1000' : 'store',
        '0010' : 'sub',
        '1001' : 'addi',
        '1010' : 'subi',
        '1110' : 'set'
        }

operation_group_1  = ['add', 'load', 'loadd', 'store', 'sub']
operation_group_2 = ['addi', 'subi', 'set']

''' turn a binary code to int'''
def str_bit_to_decimal(alloc_str):
    val = 0
    for i in range(len(alloc_str)):
        val = val * 2 + int(alloc_str[i])
    return val

''' 3-bit (op_6B_1) + 3-bit (op_6B_2) + 3-bit (op_4B_1) + 3-bit (op_4B_2)
    + 3-bit (op_2B_1) + 3-bit (op_2B_2) + 22-bit'''
def parse_keyextract_content(content):
    op_6B_1 = content[:3]
    op_6B_2 = content[3:6]
    op_4B_1 = content[6:9]
    op_4B_2 = content[9:12]
    op_2B_1 = content[12:15]
    op_2B_2 = content[15:18]
    print('6B_1 for ALU:', op_6B_1 != '000', '6B_2 for ALU:', op_6B_2 != '000', '4B_1 for ALU:', op_4B_1 != '000', '4B_2 for ALU:', op_4B_2 != '000',
            '2B_1 for ALU:', op_2B_1 != '000', '2B_2 for ALU:', op_2B_2 != '000')
    return

'''16-bit * 10
3-bit (000) + 7-bit(byte_num_from_0) + 2-bit(container type) + 3-bit (container idx) + 1-bit'''
def parse_parser_content(content):
    beg_idx = 0
    for i in range(10):
        parser_act = content[beg_idx : beg_idx + 16]
        if parser_act == '0000000000000000':
            break
        byte_number = str_bit_to_decimal(parser_act[3:10])
        container_type = container_type_dic[parser_act[10:12]]
        container_idx = str_bit_to_decimal(parser_act[12:15])
        print('byte_number =', byte_number, 'container_type =', container_type, 'container_idx =', container_idx)
        beg_idx = beg_idx + 16
    return

'''48-bit + 48-bit + 32-bit + 32-bit + 16-bit + 16-bit + 1-bit(1) + 7-bit(0000000)
'''
def parse_cammask_content(content):
    match_6B_1 = content[0:48]
    match_on_6B1 = (match_6B_1 == '000000000000000000000000000000000000000000000000')
    match_6B_2 = content[48:96]
    match_on_6B2 = (match_6B_2 == '000000000000000000000000000000000000000000000000')
    
    match_4B_1 = content[96:128]
    match_on_4B1 = (match_4B_1 == '00000000000000000000000000000000')
    match_4B_2 = content[128:160]
    match_on_4B2 = (match_4B_2 == '00000000000000000000000000000000')

    match_2B_1 = content[160:176]
    match_on_2B1 = (match_2B_1 == '0000000000000000')
    match_2B_2 = content[176:192]
    match_on_2B2 = (match_2B_2 == '0000000000000000')

    print('match_6B_1:', match_on_6B1, 'match_6B_2:', match_on_6B2, 'match_4B_1:', match_on_4B1, 'match_4B_2:', match_on_4B2,
            'match_2B_1:', match_on_2B1, 'match_2B_2:', match_on_2B2)
    return

'''12-bit(vid) + 48-bit (op_6B_1) + 48-bit (op_6B_2) + 32-bit (op_4B_1) + 
   32-bit (op_4B_2) + 16-bit (op_2B_1) + 16-bit (op_2B_2)'''
def parse_cam_content(content):
    vid = str_bit_to_decimal(content[:12])
    op_6B_1 = str_bit_to_decimal(content[12:60])
    op_6B_2 = str_bit_to_decimal(content[60:108])
    op_4B_1 = str_bit_to_decimal(content[108:140])
    op_4B_2 = str_bit_to_decimal(content[140:172])
    op_2B_1 = str_bit_to_decimal(content[172:188])
    op_2B_2 = str_bit_to_decimal(content[188:204])
    print("match value op_6B_1:", op_6B_1, "op_6B_2:", op_6B_2,
          "op_4B_1:", op_4B_1, "op_4B_2:", op_4B_2,
          "op_2B_1:", op_2B_1, "op_2B_2:", op_2B_2)
    return
'''25-bit * 25 + 7-bit(0000000)'''
def parse_ram_content(content):
    beg_idx = 0
    for i in range(25):
        ram_action = content[beg_idx : beg_idx + 25]
        if ram_action[:4] not in list(opcode_dir.keys()):
            beg_idx = beg_idx + 25
            continue
        opcode = opcode_dir[ram_action[:4]]
        if opcode in operation_group_1:
            '4b + 5b(type(2)+index(3)) + 5b + 11b (reserve)'
            op_type = container_type_dic[ram_action[4:6]] 
            operand1 = str_bit_to_decimal(ram_action[6:9])
            operand2 = str_bit_to_decimal(ram_action[9:14])
            print('ALU index:', i, 'operation:', opcode, 'op_type:', op_type, 'index:', operand1, 'operand2:', operand2)
        elif opcode in operation_group_2:
            '4b + 5b + 16b'
            operand1 = str_bit_to_decimal(ram_action[4:9])
            immediate = str_bit_to_decimal(ram_action[9:25])
            print('ALU index:', i, 'operation:', opcode, 'operand1:', operand1, 'immediate:', immediate)
        else:
            beg_idx = beg_idx + 25
            continue
        beg_idx = beg_idx + 25

def main(argv):
    if len(argv) != 2:
        print("Usage: python3 " + argv[0] + " <configuration filename>")
        sys.exit(1)
    conf_filename = argv[1]
    file_content = open(conf_filename)
    data = file_content.readlines()
    for l in data:
        line_cont = l.split(' ')
        if line_cont[0] == 'Parser':
            module_name = 'Parser'
            parser_content = line_cont[1]
            deparser_content = line_cont[2]
            parser_stage = str_bit_to_decimal(parser_content[:5])
            print("Parser stage:", parser_stage)
            deparser_stage = str_bit_to_decimal(parser_content[:5])
            print("Deparser stage:", parser_stage)
        elif line_cont[0] == 'KeyExtractConf':
            module_name = 'KeyExtractConf'
            keyextract_content = line_cont[1]
            keyextractconf_stage = str_bit_to_decimal(keyextract_content[:5])
            print("KeyExtractConf stage:", keyextractconf_stage)
        elif line_cont[0] == 'CAMMaskConf':
            module_name = 'CAMMaskConf'
            cammask_content = line_cont[1]
            cammask_stage = str_bit_to_decimal(cammask_content[:5])
            print("CAMMaskConf stage:", cammask_stage)
        elif line_cont[0] == 'CAMConf':
            module_name = 'CAMConf'
            camconf_content = line_cont[1]
            camconf_stage = str_bit_to_decimal(camconf_content[:5])
            print("CAMConf stage:", camconf_stage)
        elif line_cont[0] == 'RAMConf':
            module_name = 'RAMConf'
            ramconf_content = line_cont[1]
            ramconf_stage = str_bit_to_decimal(ramconf_content[:5])
            print("RAMConf stage:", ramconf_stage)
        else:
            content = line_cont[0][:-1]
            if module_name == 'Parser':
                parse_parser_content(content)
            elif module_name == 'KeyExtractConf':
                parse_keyextract_content(content)
            elif module_name == 'CAMMaskConf':
                parse_cammask_content(content)
            elif module_name == 'CAMConf':
                parse_cam_content(content)
            else:
                assert module_name == 'RAMConf', 'not supported module'
                parse_ram_content(content)
                continue
                
    file_content.close()

if __name__ == '__main__':
    main(sys.argv)
