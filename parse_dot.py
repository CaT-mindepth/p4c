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

def parse_dot_file():
    '''
    This function is used to parse .dot file and get path information within the dot file
    '''
    node_map = {} # key: node, val: table_name
    edge_map = {} # key: edge, val: words written in the edge
    direct_edge = {} # key: start_node of an edge, val: all end_nodes of a start_node
    start_node_list = [] # used to determine which node is the starting point of the whole graph
    path_list = {}

    dot_filename = "/home/xiangyug/p4c/build/ingress.dot"
    gv = pgv.AGraph(dot_filename, strict=False, directed=True)    
    
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
    print("node_map = ", node_map)
    print("edge_map = ", edge_map)
    print("direct_edge = ", direct_edge)
    print("start_node_list = ", start_node_list)
    path_list = get_path(direct_edge, start_node_list)
    print("path_list = ", path_list)
    return node_map, edge_map, direct_edge, path_list

def main():
    parse_dot_file()

if __name__=="__main__":
    main()
