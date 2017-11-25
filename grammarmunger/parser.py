from nltk.parse.stanford import StanfordDependencyParser
import re

dependency_parser = StanfordDependencyParser(path_to_jar='stanford-parser/stanford-parser.jar',
                                             path_to_models_jar='stanford-parser/stanford-parser-3.8.0-models.jar',
                                             corenlp_options='-outputFormatOptions includePunctuationDependencies')


class TreeNode:
    def __str__(self):
        return "(" + \
               "dependency = " + self.relation + \
               ", value = (" + str(self.value) + \
               "), side = " + ("left" if self.left else "right") + \
               ", children = " + self.list_children() + \
               ")"

    def list_children(self):
        s = "["
        first = True
        for child in self.children:
            if not first:
                s = s + ", "
            s = s + str(child)
            first = False
        s = s + "]"
        return s

    def __init__(self, left, value, relation, children, parent):
        self.left = left
        self.value = value
        self.relation = relation
        self.children = children
        self.parent = parent


def flatten_tree(tree):
    nodes_in_order = []
    get_all_nodes(tree, nodes_in_order)
    string = ""
    no_space_next = True
    for node in nodes_in_order:

        if node.value[0].startswith("'") or node.value[0] == ')' or node.value[0] == ',' or node.value[0] == ';' \
                or node.value[0].startswith(":") or node.value[0] == '%' or node.value[0] == '?':
            no_space_next = True

        if not no_space_next:
            string = string + " "

        string = string + format_node(node)

        if node.value[0] == '(':
            no_space_next = True
        else:
            no_space_next = False

    return string


def get_all_nodes(tree, node_list):
    for child in tree.children:
        if child.left:
            get_all_nodes(child, node_list)
    node_list.append(tree)
    for child in tree.children:
        if not child.left:
            get_all_nodes(child, node_list)


# paraphrase_with_structure_maps
def paraphrase_with_structure_maps(sentence):
    sent = pre_process(sentence)
    if sent == "":
        return post_process(sent)
    result = dependency_parser.raw_parse(sent)
    graph = next(result)
    tree = node_to_tree(graph.root, graph, 0)
    re_plan_unit(tree)
    return post_process(flatten_tree(tree))


def get_node(id, graph):
    for nodeIndex in graph.nodes:
        if graph.nodes[nodeIndex]["address"] == id:
            return graph.nodes[nodeIndex]


# paraphrase_with_structure_maps
def node_to_tree(node, graph, parentIndex):
    children = []
    t = TreeNode(node["address"] < parentIndex, (node["word"], node["tag"]), node["rel"], children, None)
    for dep in node['deps']:
        for next_node_id in node["deps"][dep]:
            n = node_to_tree(get_node(next_node_id, graph), graph, node["address"])
            n.parent = t
            children.append(n)
    return t


def has_dependency(node, rel):
    has = False
    for child in node.children:
        if child.relation == rel:
            return True
    return has


def get_dependency(node, rel):
    for child in node.children:
        if child.relation == rel:
            return child
    return None


def get_dependency_from_pos(node, pos):
    for child in node.children:
        if child.value[1] == pos:
            return child
    return None


def re_plan_unit(node):
    for child in node.children:
        re_plan_unit(child)

    if has_dependency(node, "nmod:poss"):
        possessor = get_dependency(node, "nmod:poss")
        affix = get_dependency_from_pos(possessor, "POS")
        possessor.children.remove(affix)
        possessor.relation = 'nmod'
        possessor.left = False
        possessor.children.insert(0, TreeNode(True, ("of", "IN"), "case", [], possessor))
        node.children.insert(find_det_point(node), TreeNode(True, ("the", "DET"), "det", [], node))


def find_det_point(node):
    i = 0
    for child in node.children:
        if not child.left:
            continue
        if child.relation == 'case':
            i = i + 1
        else:
            break
    return i


def find_pos_point(node):
    i = 0
    for child in node.children:
        if child.left:
            continue
        if child.relation == 'case':
            i = i + 1
        else:
            break
    return i


def pre_process(text):
    if text.endswith("."):
        text = text[:-1]
    if text == "":
        return ""
    return text[0].lower() + text[1:]


def post_process(text):
    if text == "":
        return "."
    return text[0].upper() + text[1:] + "."


def format_node(node):
    return node.value[0]


# Read in file
f = open('../input/Emmas_essay.txt', mode='r')
essay = f.read()
f.close()

#Preprocessing
essay = essay.replace(".\"", "\".").replace("...", ".").replace("etc.", "etc").replace(" e.g.", ":").replace("i.e.", ":").replace("St.", "St")
essay = essay.replace("p.1", "p1").replace("p.2", "p2").replace("p.3", "p3").replace("p.4", "p4").replace("p.5", "p5").replace("p.6", "p6").replace("p.7", "p7").replace("p.8", "p8").replace("p.9", "p9")

# Split into sentences
sentences = re.compile("\.|\n").split(essay)

for sent in sentences:
    sent = sent.strip() + "."
    out = paraphrase_with_structure_maps(sent)
    if out != sent:
        print(sent)
        print(out)
        print("-")