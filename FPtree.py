# dont use copy tree.item_list, copied nodes in item_list points to nodes in original tree

import pickle
from tqdm import tqdm
from copy import deepcopy
from time import time
from collections import defaultdict
# from dataset import id2key


class FPTree:
    class Node:
        def __init__(self, name):
            self.name = name
            self.count = 0
            self.next = {}
            self.path = []
            self.parent = None

        # def __repr__(self):
        #     return f'Node({self.name})'

    def __init__(self, datalist, min_support):
        self.data = [sorted(item) for item in datalist]
        self.min_support = min_support
        self.root = self.Node('_root')
        self.support_list = defaultdict(int)
        self.item_list = defaultdict(list)

    def add_record(self, record, node=None):
        """
        add record under a node
        :param record: a list of int, as a list of ids of items
        :param node: under which node the record will be built
        :return: None
        """
        node = node if node else self.root
        node.count += 1
        self.support_list[node.name] += 1
        if len(record) == 0:
            return

        if record[0] not in node.next:
            node.next[record[0]] = self.Node(record[0])
            node.next[record[0]].parent = node
            node.next[record[0]].path = node.path + [record[0]]
            self.item_list[record[0]].append(node.next[record[0]])  # add to collection of nodes of the same name
        next_cur = node.next[record[0]]
        self.add_record(record[1:], next_cur)

    def grow(self):
        """
        grow the tree with the dataset of this tree
        :return: None
        """
        for record in tqdm(self.data):
            self.add_record(record)
        return self.root

    def merge(self, node_a, node_b):
        """
        merge node_a to node_b
        :param node_a: node
        :param node_b: node
        :return: new node_b
        """
        node_b.count += node_a.count
        for offspring in sorted(node_a.next):
            if offspring not in node_b.next:
                node_b.next[offspring] = node_a.next[offspring]
            else:
                node_b.next[offspring] = self.merge(node_a.next[offspring], node_b.next[offspring])
        node_a.parent.next[node_b.name] = node_b
        del node_a

        return node_b

    def filter_unsupported(self, node, tree):
        """
        filter unsupported nodes
        :param node:
        :param tree:
        :return:
        """
        # print(sorted(node.next), node.count)
        # for n in sorted(node.next):
        #     self.filter_unsupported(node.next[n], tree)
        min_support = tree.min_support
        filtered = set()

        # from small ids to big ids
        for key in sorted(node.next):
            # print(key)

            son = node.next[key]
            _, son = self.filter_unsupported(son, tree)
            if tree.support_list[key] < min_support:
                # print(f'lack of support: {key}')
                filtered.add(key)

                # attach all offspring to node
                for offspring in son.next:
                    if offspring in node.next:
                        node.next[offspring] = self.merge(son.next[offspring], node.next[offspring])
                    else:
                        son.next[offspring].parent = node
                        node.next[offspring] = son.next[offspring]
            else:
                continue

        # delete unsupported node
        for key in filtered:
            del node.next[key]

            # could be deleted when filtering other nodes
            if key in tree.support_list:
                del tree.support_list[key]
            if key in tree.item_list:
                del tree.item_list[key]

        return filtered, node

    def check_empty(self, node):
        """
        delete all nodes with count==0 under a node
        :param node:
        :return:
        """
        to_delete = []
        for key in node.next:
            if node.next[key].count == 0:
                to_delete.append(key)
            else:
                self.check_empty(node.next[key])

        for key in to_delete:
            del node.next[key]

        return node

    def cut_tree(self, to_cut, tree, min_support=None):
        """
        update support of prefixes, cut to_cut, cut lack-of-supports
        :param tree: tree to make conditional FP-tree
        :param to_cut: the name of the nodes to cut
        :param min_support: minimum support to be a frequent item
        :return:
        """

        min_support = min_support if min_support else self.min_support

        # create conditional FP-tree
        cond_tree = deepcopy(tree)
        cond_tree.support_list = defaultdict(int)
        cond_tree.item_list = defaultdict(list)
        cond_tree.root = deepcopy(tree.root)

        # clean count of conditional FP-tree
        cache = [cond_tree.root]

        while cache:
            to_clean = cache.pop(0)
            # print(to_clean)
            if to_clean.name != to_cut:
                to_clean.count = 0
            else:
                cond_tree.item_list[to_cut].append(to_clean)
            for key in to_clean.next:
                cache.append(to_clean.next[key])

        # update count of nodes along all paths ending with to_cut to conditional FP-tree
        for node in cond_tree.item_list[to_cut]:
            print(f"it's in {node.name}")
            path_weight = node.count  # count(support of this path is provided by the cutoff node)
            cond_tree.support_list[node.name] += path_weight
            # print(node.path)
            while node.parent.name != '_root':
                parent = node.parent
                parent.count += path_weight
                node = parent
                # print(node.name)
                cond_tree.support_list[node.name] += path_weight
                cond_tree.item_list[node.name].append(node)
            node.parent.count += path_weight  # root

            # attach to new cond_tree
            node.parent = cond_tree.root
            cond_tree.root.next[node.name] = node  # not repetitive

        # delete to_cut
        for node in cond_tree.item_list[to_cut]:
            del node.parent.next[to_cut]
        del cond_tree.item_list[to_cut]
        del cond_tree.support_list[to_cut]

        # clean empty-count nodes
        cond_tree.root = self.check_empty(cond_tree.root)

        # filter unsupported nodes
        cond_tree.filter_unsupported(cond_tree.root, cond_tree)

        return cond_tree

    def freq_item(self, tree, endwith=''):
        """
        get frequent items ending with a character or a string

        :param endwith:
        :return:
        """

        freq_items = []
        # for key in sorted([k for k in tree.support_list if k != '_root'], reverse=True):
        #     if tree.support_list[key] >= tree.min_support:  # if key is supported
        #         freq_items.append(str(key) + endwith)  # cond_tree is None
        #         print(self.support_list)
        #         tree_cp = deepcopy(tree)
        #         # FIXME: tree_cp.item_list's pointer point to nodes from original tree
                  # TODO: a valid way to make a copy
        #         cond_tree = self.cut_tree(key, tree_cp)
        #
        #         freq_items.extend(self.freq_item(cond_tree, str(key) + endwith))
        # return freq_items


if __name__ == "__main__":
    start = time()
    data_file = open('./data.pkl', 'rb')
    dataset = pickle.load(data_file)

    tree = FPTree(dataset, 7)
    fptree = tree.grow()
    with open('./fptree.pkl', 'wb') as ftree:
        pickle.dump(fptree, ftree)

    # testset = [[1, 2, 3, 4],
    #            [1, 2, 3, 5],
    #            [1, 2, 4, 6],
    #            [1, 2, 4, 5, 6],
    #            [1, 2, 5],
    #            [1, 2, 5, 6],
    #            [1, 2, 6],
    #            [2, 3],
    #            [2, 4, 5, 6],
    #            [3, 4, 5, 6],
    #            [3, 4, 6],
    #            [3, 5],
    #            [6]]
    tree = FPTree(dataset, 7)
    root = tree.grow()

    test_freq_items = tree.freq_item(tree)
    end = time()
    print(f'{float(end-start)/60}')
    # cfcf = cf.cut_tree(5)
    #
    # r = cfcf.root
    #
    # cfcfcf = cfcf.cut_tree(4)
    # r = cfcfcf.root

