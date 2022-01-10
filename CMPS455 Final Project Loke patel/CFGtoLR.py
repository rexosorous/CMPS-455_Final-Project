# global variables
CURSOR = '!!CURSOR!!'



class Grammar:
    def __init__(self, CFG: [[str, [str]]]):
        self.CFG = CFG
        self.nonterminals = self.get_nonterminals()
        self.terminals = self.get_terminals()
        self.FIRST = self.blank_table()
        self.FOLLOW = self.blank_table()
        self.populate_first()
        self.populate_follow()



    def get_nonterminals(self) -> [str]:
        '''Scans the CFG for all of the nonterminals

        Returns:
            [str]: each element is a different nonterminal
        '''
        return list(dict.fromkeys([x[0] for x in self.CFG]))



    def get_terminals(self) -> [str]:
        '''Scans the CFG for all of the terminals

        Returns:
            [str]: each element is a different terminal
        '''
        t = []
        for rule in self.CFG:
            for right_side in rule[1]:
                if right_side not in self.nonterminals and right_side not in t:
                    t.append(right_side)
        return t + ['$']



    def blank_table(self):
        '''Generates a blank FIRST or FOLLOW table

        Returns:
            {str: list}: keys are nonterminals
        '''
        table = dict()
        for name in self.nonterminals:
            table[name] = list()
        return table



    def populate_first(self):
        for line in self.CFG:
            self.first_of(line[0], [line])



    def first_of(self, key, lines):
        '''A recursive function to get one nonterminal's FIRST set

        Args:
            key (str): the nonterminal's FIRST set to add to
            lines ([[str, [str]]]): a list of each CFG line to iterate through
        '''
        for rule in lines:
            left = rule[0]
            right = rule[1][0]
            if right in self.terminals and right not in self.FIRST[key]: # add FIRST(terminal)
                self.FIRST[key].append(right)
            elif right in self.nonterminals: # add FIRST(nonterminal) which requires recursion
                if left == right: # don't get caught in an infinite loop
                    continue
                self.first_of(key, [x for x in self.CFG if x[0] == right]) # recursion



    def populate_follow(self):
        for key in self.FOLLOW:
            self.FOLLOW[key] = self.follow_of(key)



    def follow_of(self, key) -> [str]:
        '''A recursive function to get one nonterminal's FOLLOW set

        Args:
            key (str): the nonterminal's FOLLOW set to add to

        Returns:
            [str]: each element is a different terminal in the FOLLOW set
        '''
        value = []
        if key == '<prog>': # special case
            value.append('$')

        for rule in [x for x in self.CFG if key in x[1]]:
            if rule[1][-1] == key:  # implying FOLLOW(nonterminal) is in FOLLOW(key) which requires recursion
                if rule[0] == key:
                    continue
                value += [x for x in self.follow_of(rule[0]) if x not in value] # recursion
                continue

            after = rule[1][rule[1].index(key)+1] # implying FIRST(terminal) is in FOLLOW(key). no recursion necessary
            if after in self.terminals:
                if after not in value:
                    value.append(after)
                continue

            value += [x for x in self.FIRST[after] if x not in value] # implying FIRST(nonterminal) is in FOLLOW(key). no recursion necessary
        return value





class Node:
    def __init__(self, CFG: Grammar, head: [[str, [str]]]):
        '''FA Nodes

        Note:
            self.body may not be accurate. the body is only used to generate the next nodes in the FA,
            but aren't needed to generate the LR Parsing Table, so the accuracy of the body doesn't matter
            after the FA is generated and as such, there is no effort being made to preserve the body.
        '''
        self.CFG = CFG
        self.head = head
        self.body = list()
        self.paths = dict()
        for ele in head:
            self.body.append([ele[0], [x for x in ele[1]]]) # this essentially deep copies the ele. without this, editing the body also edits the head
            self.generate_body(ele)



    def generate_body(self, next_: [str, [str]]):
        '''Recursively generates productions based on the head

        Attributes:
            next_ ([str, [str]]): the production line with which to attempt to create more productions
        '''
        cur = next_[1].index(CURSOR)

        if cur == len(next_[1])-1: # if the cursor is at the end of the line, ignore it (this only happens if it's part of the head)
            return

        after_cur = next_[1][cur+1]
        if after_cur[0] == '<':
            # determine if there are any more productions to create. ie. if the element after the cursor starts with '<'
            # ex:   CURSOR <indentifier> creates more productions
            #       CURSOR "value=" does not create any more productions
            new_productions = [[x[0], [CURSOR] + x[1]] for x in self.CFG.CFG if x[0] == after_cur] # find all the new productions that are made. ex: <identifier> has 3 separate productions
            for prod in new_productions:
                if prod in self.body: # make sure not to create duplicates
                    continue
                self.body.append(prod)
                self.generate_body(prod) # recursion



    def __eq__(self, compare) -> bool:
        '''For all intents and purposes, a Node object is really defined by its head.

        This allows us to compare heads ([[str, [str]]]) with Node objects to determine equivalency.

        Returns:
            bool: True if they are equal, False if otherwise
        '''
        if self.head == compare:
            return True
        return False



    def __repr__(self):
        '''Just for printing during debugging
        '''
        printme = ''
        for line in self.head:
            printme += f'{line[0]} --> {" ".join(line[1])}\n\t'
        return printme





class FiniteAutomata:
    def __init__(self, CFG: Grammar):
        self.CFG = CFG
        self.node_tree = list()
        self.node_queue = [Node(self.CFG, [['START', [CURSOR, '<prog>']]])]
        self.generate_FA()



    def move_cur(self, head: [[str, [str]]]) -> [[str, [str]]]:
        '''Moves the cursor forward in a line(s) from a parent's body

        Note:
            each part of the argument is deep copied as issues related to double moving arose

        Args:
            head ([[str, [str]]])

        Returns:
            [[str, [str]]]
        '''
        new_head = []
        for line in head:
            line_copy = [line[0], [x for x in line[1]]]
            index = line_copy[1].index(CURSOR) # find the cursor
            cur = line_copy[1].pop(index) # remove the cursor
            line_copy[1].insert(index+1, cur) # insert the cursor one space after
            new_head.append(line_copy)
        return new_head



    def take_paths(self, node: Node) -> [Node]:
        '''Creates new nodes (children) based on the body of an existing node.

        For each line(s) of the parent's body, move the cursor forward and create a new node with that line(s)
        Makes sure not to create a new node if that node already exists

        Args:
            node (Node): the parent node to create children off of

        Returns:
            [Node]: a list of the children
        '''
        paths = list(dict.fromkeys([x[1][x[1].index(CURSOR)+1] for x in node.body if x[1].index(CURSOR) < len(x[1])-1])) # find all the possible paths that can be made
        new_nodes = list()
        for p in paths:
            # the following line finds all the lines in the body whose cursor is one space behind the path
            # ex:   [CURSOR, path]          good
            #       [CURSOR, lorem, path]   bad: CURSOR is not one space behind path
            #       [CURSOR, lorem]         bad: path does not exist
            #       [lorem, CURSOR]         bad: CURSOR is at the end of the list
            head = [x for x in node.body if x[1].index(CURSOR) < len(x[1])-1 and x[1][x[1].index(CURSOR)+1] == p]
            head = self.move_cur(head)
            node.paths[p] = head
            # add children to the parent
            if head not in self.node_tree and head not in self.node_queue: # make sure not to submit duplicate entries
                new_nodes.append(Node(self.CFG, head))
        return new_nodes



    def generate_FA(self):
        '''The main logic to generate the entire FA
        '''
        while self.node_queue:
            node = self.node_queue.pop(0)
            self.node_tree.append(node)
            new_paths = self.take_paths(node)
            self.node_queue += new_paths





class LRParsingTable:
    def __init__(self, CFG: Grammar, FA: FiniteAutomata):
        self.CFG = CFG
        self.FA = FA
        self.table = self.blank_table()
        self.populate()



    def blank_table(self) -> {str: dict}:
        '''Generates a blank LR table

        Returns:
            {str: dict}: keys are stringified row integers
        '''
        table = dict()
        for num in range((len(self.FA.node_tree))):
            table[str(num)] = dict()
        return table



    def populate(self):
        '''Populates the LR Parsing Table following these rules:

            1. if there is a nonterminal path P that connects nodes m to n, cell (m, P) = n
            2. if there is a terminal path p that connects nodes m to n, cell (m, p) = Sn
            3. if there is a node n whose head contains a line with the CURSOR at the end,
               then for every member m of FOLLOW(line's left side), cell (n, m) = Rx ; where x is the CFG rule # of line
        '''
        for node in self.FA.node_tree:
            cur_index = str(self.FA.node_tree.index(node))
            if node == [['START', ['<prog>', CURSOR]]]: # special case for ACC block
                self.table[cur_index]['$'] = 'ACC'
                continue

            # rule 1 and 2 to generate cells with Sn and n
            for path, destination in node.paths.items():
                dest_index = str(self.FA.node_tree.index(destination))
                if path in self.CFG.nonterminals:   # n
                    self.table[cur_index][path] = dest_index
                elif path in self.CFG.terminals:    # Sn
                    self.table[cur_index][path] = 'S' + dest_index

            # rule 3 to genereate cells with Rx
            for line in node.head:
                if line[1][-1] == CURSOR:
                    for ele in self.CFG.FOLLOW[line[0]]:
                        self.table[cur_index][ele] = 'R' + str(self.CFG.CFG.index([line[0], line[1][:-1]])+1)
                    break





def convert(grammar: [[str, [str]]]) -> {str: {str: str}}:
    '''Converts a CFG to FA to LR Parsing Table

    Args:
        grammar ([[str, [str]]]): the CFG formatted in a very specific way

    Returns:
        {str: {str: str}}: The LR Parsing Table converted into a dictionary of dictionaries for ease of use

    Note:
        In order to access a cell in the LR Parsing Table (the return variable), use LR[row number][terminal or nonterminal]
    '''
    print('loading CFG...', end=' ')
    CFG = Grammar(grammar)
    print('ok')

    print('converting CFG to FA...', end=' ')
    FA = FiniteAutomata(CFG)
    print('ok')

    print('converting FA to LR Parsing Table...', end=' ')
    LR = LRParsingTable(CFG, FA)
    print('ok')

    return LR.table



def terminals(grammar: [[str, [str]]]) -> [str]:
    '''Gets a list of terminals from the CFG

    Args:
        grammar ([[str, [str]]]): the CFG formatted in a very specific way

    Rreturns:
        [str]: each element is a different terminal
    '''
    CFG = Grammar(grammar)
    return CFG.terminals