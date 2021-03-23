import pickle
from tqdm import tqdm
from copy import deepcopy
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
        for offspring in node_a.next:
            if offspring.name not in node_b.next:
                node_b.next[offspring.name] = offspring
            else:
                node_b.next[offspring.name] = self.merge(offspring, node_b.next[offspring.name])
        del node_a
        return node_b

    def cut_tree(self, to_cut, tree=None, min_support=None):
        """
        update support of prefixes, cut to_cut, cut lack-of-supports
        :param tree: tree to make conditional FP-tree
        :param to_cut: the name of the nodes to cut
        :param min_support: minimum support to be a frequent item
        :return:
        """
        tree = tree if tree else self
        min_support = min_support if min_support else self.min_support

        # create conditional FP-tree
        cond_tree = deepcopy(tree)
        cond_tree.support_list = defaultdict(int)
        cond_tree.item_list = defaultdict(list)
        cond_tree.root = self.Node('_root')

        if tree.support_list[to_cut] < min_support:
            # to_cut is not a frequent item itself
            print(tree.support_list[to_cut], min_support)
            return

        # attach all path ending with to_cut to conditional FP-tree
        for node in tree.item_list[to_cut]:
            print()
            print(node.name, node.count)
            path_weight = node.count  # count(support of this path is provided by the cutoff node)
            cond_tree.support_list[node.name] += path_weight
            cond_tree.item_list[to_cut].append(node)
            print(node.path)
            while node.parent.name != '_root':
                node = node.parent
                print(node.name)
                cond_tree.support_list[node.name] += path_weight
                cond_tree.item_list[node.name].append(node)
            # attach to new cond_tree
            node.parent = cond_tree.root
            cond_tree.root.next[node.name] = node.parent  # not repetitive
        del cond_tree.support_list[to_cut]
        del cond_tree.item_list[to_cut]

        # test
        return cond_tree






        # update prefix
        for cur in cond_tree.item_list[to_cut]:
            node = cur
            while cur.parent and cur.parent.name != '_root':
                cond_tree.support_list[cur.parent.name] -= (cur.parent.count - cur.count)
                cur.parent.count = cur.count
                cur = cur.parent

            # cut to_cut nodes
            print(node.name)
            del node.parent.next[node.name]
        del cond_tree.item_list[node.name]

        # remove lack-supports
        for key in cond_tree.support_list:
            if cond_tree.support_list[key] < min_support:
                del(cond_tree.support_list[key])

                # cut nodes
                for node in cond_tree.item_list:
                    for offspring in node.next:
                        if offspring.name not in node.parent.next:
                            node.parent.next[offspring.name] = offspring
                        else:
                            node.parent.next[offspring.name] = self.merge(offspring, node.parent.next[offspring.name])
                del cond_tree.item_list[key]

        return cond_tree


if __name__ == "__main__":
    data_file = open('./data.pkl', 'rb')
    dataset = pickle.load(data_file)

    # tree = FPTree(dataset, 1)
    # fptree = tree.grow()
    # with open('./fptree.pkl', 'wb') as ftree:
    #     pickle.dump(fptree, ftree)

    testset = [[1, 2, 3], [1, 2, 4], [1, 4], [2, 3, 5], [1, 3, 4, 5], [3, 4, 5], [3, 4, 5]]
    tree = FPTree(testset, 2)
    fptree = tree.grow()

    cf = tree.cut_tree(5)
    print(cf.support_list)
    # cfcf = cf.cut_tree(4, min_support=1)
