import pygraphviz as pgv
import networkx as nx
import re

def get_path(direct_edge, start_node_list):
    # print("------------------------------")
    path_list = {}
    while (len(start_node_list) > 0):
        key = start_node_list[0]
        # print("# should be 0 key = ", key)
        if key not in direct_edge:
            start_node_list.pop(0)
            continue
        add_map = []
        linked_list = []
        for i in range(len(direct_edge[key])):
            linked_list.append(direct_edge[key][i])
            add_map.append(direct_edge[key][i])
            if direct_edge[key][i] not in start_node_list and direct_edge[key][i] not in path_list:
                start_node_list.append(direct_edge[key][i])
        # print("# should be [0,2] start_node_list = ", start_node_list)
        # print("# should be [2] linked_list = ", linked_list)
        while(len(linked_list) > 0):
            curr_len = len(linked_list)
            for i in range(curr_len):
                curr_node = linked_list[i]
                # print("curr_node = ", curr_node)
                if curr_node in direct_edge:
                    for j in range(len(direct_edge[curr_node])):
                         end_path_node = direct_edge[curr_node][j]
                         if key in path_list:
                              if end_path_node not in path_list[key]:
                                  path_list[key].append(end_path_node)
                         else:
                              path_list[key] = [end_path_node]
                         if end_path_node not in add_map:
                              linked_list.append(end_path_node)
                              add_map.append(end_path_node)
            for i in range(curr_len):
                linked_list.pop(0)
        start_node_list.pop(0)
    return path_list

def parse_dot_file(input_file):
    '''
    This function is used to parse .dot file and get path information within the dot file
    '''
    node_map = {} # key: node, val: table_name
    edge_map = {} # key: edge, val: words written in the edge
    direct_edge = {} # key: start_node of an edge, val: all end_nodes of a start_node
    start_node_list = [] # used to determine which node is the starting point of the whole graph
    path_list = {}
    
    gv = pgv.AGraph(input_file, strict=False, directed=True)    
    
    G = nx.DiGraph(gv)
    # reference website: https://networkx.org/documentation/stable/tutorial.html
    for item in gv:
        # set up the node_map
        node = gv.get_node(item)
        table_name = G.nodes[item]['label']
        node_map[node] = table_name
        # add node into start_node_list
        start_node_list.append(item)
    for item in gv.edges():
        start_node = item[0]
        end_node = item[1]
        if end_node in start_node_list:
            start_node_list.remove(end_node)
        # set the direct_edge first
        if start_node in direct_edge:
            direct_edge[start_node].append(end_node)
        else:
            direct_edge[start_node] = [end_node]
        try:
            edge_map[item] = G.edges[start_node,end_node]['label']
        except:
            edge_map[item] = "none"
    path_list = get_path(direct_edge, start_node_list)
    return node_map, edge_map, direct_edge, path_list

def shortest_path(key, v, direct_edge):
    tmp_list = []
    for x in direct_edge[key]:
        tmp_list.append([x])

    # stop until we find our taget
    jump_while = 0
    shortest_list = []
    while 1:
        if jump_while == 1:
            break

        curr_len = len(tmp_list)
        remove_list = []
        for i in range(curr_len):
            curr_list = list(tmp_list[i]) # assignment by value; curr_list = tmp_list[i] this is assignment by reference
            curr_node = curr_list[-1]
            # Case1: curr_node does not have direct_edge
            if curr_node not in direct_edge:
                remove_list.append(curr_list)
            elif len(direct_edge[curr_node]) == 1:
                tmp_list[i].append(direct_edge[curr_node][0])
                if direct_edge[curr_node][0] == v:
                    shortest_list = tmp_list[i]
                    jump_while = 1
            else:
                assert len(direct_edge[curr_node]) > 1
                for j in range(len(direct_edge[curr_node])):
                    if j == 0:
                        tmp_list[i].append(direct_edge[curr_node][j])
                        if direct_edge[curr_node][j] == v:
                            jump_while = 1
                            shortest_list = tmp_list[i]
                            break
                    else:
                        copy_list = curr_list + [direct_edge[curr_node][j]]
                        tmp_list.append(copy_list)
                        if direct_edge[curr_node][j] == v:
                            jump_while = 1
                            shortest_list = tmp_list[-1]
                            break
        for x in remove_list:
            tmp_list.remove(x)
    # path list is the list we return
    path_list = []
    path_list.append(key)
    for item in shortest_list:
        path_list.append(item)
    return path_list

TableDict = {}
HeaderDict = {}
StructDict = {}
ActionDict = {}

f =  open("/tmp/example.txt", "r")
# key is table name and value is a list of list including 
# action list; match portion

#Header name = hop_metadata_t
#Header members:vrf;ipv6_prefix;next_hop_index;mcast_grp;urpf_fail;drop_reason; 

#Struct name = headers
#Struct members:

# Successor dependency:Table A’s match result determines whether Table B should be executed or not

# whether there is common member in both list1 and list2
def overlap(list1, list2):
    for x in list1:
        if x in list2:
            return True
    return False

# output one of the previous four dependencies
def output_relationship(tableA, tableB, TableDict, ActionDict):
    # Match dependencies
    modify_fields_tableA = []
    modify_fields_tableB = []
    for i in range(len(TableDict[tableA][1])):
        action_name = TableDict[tableA][1][i]
        for j in range(len(ActionDict[action_name])):
            modify_fields_tableA.append(ActionDict[action_name][j])

    for i in range(len(TableDict[tableB][1])):
        action_name = TableDict[tableB][1][i]
        for j in range(len(ActionDict[action_name])):
            modify_fields_tableB.append(ActionDict[action_name][j])
    match_fields_tableA = TableDict[tableA][0]
    match_fields_tableB = TableDict[tableB][0]
    # Match dependency: Table A modifies a field Table B matches
    if overlap(modify_fields_tableA, match_fields_tableB):
        print(tableA, "has Match dependency relationship with", tableB)
    # Action dependency: Table A and B both change the same field, but the end-result should be that of the later Table B
    elif overlap(modify_fields_tableA, modify_fields_tableB):
        print(tableA, "has Action dependency relationship with", tableB)
    # Reverse dependency: Table A matches on a field that Table B modifies,
    elif overlap(match_fields_tableA, modify_fields_tableB):
        print(tableA, "has Reverse dependency relationship with", tableB)
    else:
        print(tableA, "has no dependency relationship with", tableB)

line_list = []

for x in f:
  line_list.append(x)

for i in range(len(line_list)):
  x = line_list[i]
  if x == "---------\n":
     continue
  elif x.find('Header name =') != -1:
     if x[len(x) - 1] == '\n':
         x = x[:len(x) - 2]
     header_name = x.split(' = ')[1]
     #print("header_name = ", header_name)
     y = line_list[i + 1]
     if y[len(y) - 1] == '\n':
         y = y[:len(y) - 1]
     if y[len(y) - 1] != ":":
         header_member = y[:len(y)-1].split(":")[1].split(";")
         #print("header_member", header_member)
     else:
         header_member = []
         #print("header_member is empty")
     HeaderDict[header_name] = header_member
     i = i + 1
  elif x.find("Struct name =") != -1:
     if x[len(x) - 1] == '\n':
         x = x[:len(x) - 2]
     struct_name = x.split(' = ')[1]
     #print("struct_name = ", struct_name)
     y = line_list[i + 1]
     if y[len(y) - 1] == '\n':
         y = y[:len(y) - 1]
     if y[len(y) - 1] != ":":
         struct_member = y[:len(y)-1].split(":")[1].split(";")
         #print("struct_member", struct_member)
     else:
         struct_member = []
         #print("struct_member is empty")
     StructDict[struct_name] = struct_member
     i = i + 1
  elif x.find("Table name =") != -1:
     # Table name = smac_vlan
     # Match portion:hdr.ethernet.srcAddr;standard_metadata.ingress_port;
     # Action portion:
     table_name = x.split(' = ')[1]
     if table_name[len(table_name) - 1] == '\n':
         table_name = table_name[:len(table_name) - 1]
     #print("table_name = ", table_name)
     match_portion = line_list[i + 1]
     action_portion = line_list[i + 2]
     i = i + 2
     if match_portion[len(match_portion) - 1] == '\n':
         match_portion = match_portion[:len(match_portion) - 1]
     if match_portion[len(match_portion) - 1] != ":":
         match_member = match_portion[:len(match_portion) - 1].split(":")[1].split(";")
         #print("match_member = ", match_member)
     else:
         match_member = []
         #print("match_member is empty")

     if action_portion[len(action_portion) - 1] == '\n':
         action_portion = action_portion[:len(action_portion) - 1]
     if action_portion[len(action_portion) - 1] != ":":
         action_member = action_portion[:len(action_portion) - 1].split(":")[1].split(";")
         #print("action_member = ", action_member)
     else:
         action_member = []
         #print("action_member is empty")

     TableDict[table_name] = [match_member, action_member]
  elif x.find("Action name =") != -1: 
     # Action name = set_egress_port
     # fields modified within an Action:standard_metadata.egress_spec;
     action_name = x.split(" = ")[1]
     if action_name[len(action_name) - 1] == '\n':
         action_name = action_name[:len(action_name) - 1]
     #print("action_name = ", action_name)
     fields_portion = line_list[i + 1]
     if fields_portion[len(fields_portion) - 1] == '\n':
         fields_portion = fields_portion[:len(fields_portion) - 1]
     if fields_portion[len(fields_portion) - 1] != ":":
         fields_list = fields_portion[:len(fields_portion) - 1].split(":")[1].split(";")
         #print("fields_list = ", fields_list)
     else:
         fields_list = []
         #print("field_list is empty")
     i = i + 1
     ActionDict[action_name] = fields_list

print("TableDict", TableDict)
print("HeaderDict", HeaderDict)
print("StructDict", StructDict)
print("ActionDict", ActionDict)

input_file = "/home/xiangyug/p4c/build/ingress.dot" 
node_map, edge_map, direct_edge, path_list = parse_dot_file(input_file)
print("node_map = ", node_map)
print("edge_map = ", edge_map)
print("direct_edge = ", direct_edge)
print("path_list = ", path_list)

print("-----------------------------------")
# print("first of all, analyze the direct_edge")

successor_dep = []
# Analyze the dependency of direct edge
for key in direct_edge:
    for v in direct_edge[key]:
        # print("key = ", key)
        # print("v = ", v)
        tableA = node_map[key]
        tableB = node_map[v]
        # print("tableA = ", tableA)
        # print("tableB = ", tableB)
        if tableA == '__START__' or tableB == "__EXIT__":
            continue
        # turn format from ingress.smac_vlan to smac_vlan
        tableA = tableA.split('.')[1]
        tableB = tableB.split('.')[1]
        if edge_map[(key, v)] != 'none' and edge_map[(key, v)] != 'default':
            successor_dep.append(tuple({tableA, tableB}))
            print(tableA, "has successor dependency relationship with", tableB)
        else:
        # turn format from ingress.smac_vlan to smac_vlan
            output_relationship(tableA, tableB, TableDict, ActionDict)

# Anlyze the dependency of a path
for key in path_list:
    if node_map[key] == '__START__':
        continue
    for v in path_list[key]:
        # print("key = ", key)
        # print("node_map[v] = ", node_map[v])

        # This case means that it has been already processed by direct_edge
        if key in direct_edge and v in direct_edge[key]:
            continue
        if node_map[v] == "__EXIT__":
            continue
        path_table = shortest_path(key, v, direct_edge)
        # print(path_table)
        flag = 0
        # prove the correctness of Algo: if step 1 path does not have Successor dependency
        # then there must be no dependency
        tableA = node_map[path_table[0]].split('.')[1]
        tableB = node_map[path_table[1]].split('.')[1]
        if tuple({tableA, tableB}) in successor_dep:
            flag = 1
        tableA = node_map[key].split('.')[1]
        tableB = node_map[v].split('.')[1]
        if flag == 1:
            print(tableA, "has successor dependency relationship with", tableB)
        else:
            output_relationship(tableA, tableB, TableDict, ActionDict)
