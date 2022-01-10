# local modules
import CFGtoLR
import translator


class Compiler:
    def __init__(self, CFG: [[str, [str]]], words: [str]):
        '''A class that checks the legality of the custom coding language and compiles it into python

        Args:
            words ([str]): a cleaned up list of words from the source code. should be obtained from translator.translate()

        Attributes:
            words ([str]): see args
            RULES ([str, [str]]): the CFG with lambdas removed
            LR_TABLE ({str: {str: str}}): the LR parsing table derived from the given grammar
            variables ([str]): the variables the program declares. used to check if the code tries to assign values to an undeclared variable
        '''
        self.words = words
        self.RULES = CFG
        self.LR_TABLE = CFGtoLR.convert(CFG)
        self.TERMINALS = CFGtoLR.terminals(CFG)
        self.variables = []



    def test(self) -> bool:
        '''Checks for errors in the code by using the LR parsing table method

        Returns:
            bool: True if there are no errors. False otherwise.
        '''
        print('testing input against LR Parsing Table...', end=' ')

        stack = ['0'] # push 0
        input_list = self.words
        word_index = 0
        index_cooldown = 0
        in_vars = False

        try:
            while True:
                # abstract variables
                read_value = input_list[0]                  # read input string
                state = stack[-1]                           # read stack

                if read_value == 'program':
                    in_program_name = True
                    # in_vars = True

                if read_value == 'var':
                    in_program_name = False
                    in_vars = True

                if read_value == 'begin':   # used for determining which variables have been declared
                    in_vars = False

                if in_program_name:
                    # pass
                    self.variables.append(read_value)

                if read_value in self.variables:
                    in_vars = True

                if in_vars:
                    self.variables.append(read_value)
                    if read_value not in self.TERMINALS:        # if the word is not a terminal, try it as a variable name
                        index_cooldown += len(read_value)
                        input_list = list(read_value) + input_list[1:]   # splits up the word into each of its characters and pushes it to the front of the words list
                        read_value = input_list[0]

                table_value = self.LR_TABLE[state][read_value]   # find [k, X] or [k, t]

                stack = stack[:-1]                               # pop stack

                # logic
                if table_value.isdigit(): # boxes with number entries
                    stack.append(state)             # push k
                    stack.append(read_value)        # push X
                    stack.append(table_value)       # push n

                elif table_value[0] == 'S': # boxes with Sn
                    stack.append(state)             # push k
                    stack.append(read_value)        # push t
                    stack.append(table_value[1:])   # push n
                    input_list = input_list[1:]     # pop input string
                    if index_cooldown > 0:
                        index_cooldown -= 1
                    if index_cooldown == 0:
                        word_index += 1


                elif table_value[0] == 'R': # boxes with Rn
                    stack.append(state)             # push k

                    # abstract variables
                    rule_value = self.RULES[int(table_value[1:])-1]
                    rule_left = rule_value[0]
                    rule_right = rule_value[1]

                    stack = stack[:-len(rule_right)*2] # pop twice the length of rule #n's right side
                    state_new = stack[-1]           # read stack
                    stack = stack[:-1]              # pop stack
                    stack.append(state_new)         # push m
                    stack.append(rule_left)         # push A
                    stack.append(self.LR_TABLE[state_new][rule_left]) # push [m, A]

                elif table_value == 'ACC': # accept state
                    break

            print('ok')
            return True
        except KeyError:
            '''print an error message that tells you what line the mistake was found on, what the expected value is, and what was gotten instead
            '''
            # this section is able to find the line that the error occurred on so it can be printed for more detailed error messages
            print(self.variables)
            print(self.LR_TABLE[state])

            with open('finalp1.txt', 'r', encoding='utf-8') as file:
                raw_lines = [x for x in file]

            lines = translator.translate_lines('finalp1.txt')
            search = self.words[word_index-1:word_index+2]
            line_num = int()
            for k, v in lines.items():
                if search[1] in v:
                    index = v.index(search[1])
                    if len(v) == 1:
                        line_num = k
                        break
                    if index == 0 and v[1] == search[2]:
                        line_num = k
                        break
                    if index == len(v)-1 and v[len(v)-2] == search[0]:
                        line_num = k
                        break
                    if v[index-1] == search[0] and v[index+1] == search[2]:
                        line_num = k
                        break

            row = stack[-1]
            col = self.LR_TABLE[row].keys()
            acceptable_inputs = [x for x in col if x[0] != "<"]
            print(f'\n\nERROR on line {line_num+1}:\n{raw_lines[line_num]}REASON: expected one of {acceptable_inputs}, but got "{self.words[word_index]}" instead.')
            return False



    def test_vars(self):
        '''Checks for errors with undeclared variable names by changing the CFG and reloading the LR_TABLE and TERMINALS

        The normal LR table (produced from the handout) is unable to determine if variables in <stat-list> were declared in <dec-list> or not.
        As a solution, after we've tested the input once and collected the declared variables, we change the CFG and LR table.
        The CFG is changed such that all <identifier> productions are replaced with <identifier> --> variable.
        This means that the variables are now terminals and the LR table generated from the new CFG will now be able to determine if variables
        in <dec-list> were declared in <stat-list> or not.

        Additionally, we slightly change <prog> production to <prog> --> program <program-name> ; ...
        because otherwise this would falsely allow the program name in the <stat-list> section even though it was never declared in
        the <dec-list> section.
        '''
        print('testing variable names...')
        print('constructing new CFG...', end=' ')

        # replace <identifier> in <prog> with <program-name>
        start_index = self.RULES.index([x for x in self.RULES if x[0] == '<prog>'][0])
        ident_index = self.RULES[start_index][1].index('<identifier>')
        self.RULES[start_index][1].pop(ident_index)
        self.RULES[start_index][1].insert(ident_index, '<program-name>')
        self.RULES.append(['<program-name>', [self.variables[0]]]) # add <program-name> --> program_name_variable

        for line in [x for x in self.RULES if x[0] == '<identifier>']: # remove old <identifier> productions
            self.RULES.remove(line)

        self.RULES += [['<identifier>' , [x]] for x in self.variables[1:]] # add in the new identifiers with variables
        print('ok')

        print('generating new LR Parsing Table...')
        self.LR_TABLE = CFGtoLR.convert(self.RULES) # get new LR table
        self.TERMINALS = CFGtoLR.terminals(self.RULES) # get the new terminals
        return self.test()



    def compile(self) -> str:
        '''Checks for errors in the code and if it's good, then compiles the code into python

        Returns:
            str: the code's filename. returns None if a file was not created
        '''
        if self.test() and self.test_vars():
            print('generating python file...', end=' ')

            # collect information
            filename = self.words[self.words.index('program')+1] + '.py'
            var_list = [x + ' = int()\n' for x in self.words[self.words.index('var')+1 : self.words.index('begin')-3] if x != ',']
            instructions = ' '.join(self.words[self.words.index('begin')+1 : self.words.index('end.')-1]).split(';')

            # fix instructions
            for index in range(len(instructions)):
                statement = instructions[index]
                if statement[0] == ' ':
                    statement = statement[1:]
                statement = statement.replace('write', 'print')
                statement += '\n'
                instructions[index] = statement

            # create output string
            output_string = '# declare variables\n# although not necessary for python, i thought it would be nice to mimic the input\n'
            for var in var_list:
                output_string += (var)

            output_string += '\n# logic\n'
            for statement in instructions:
                output_string += statement

            # write to file
            with open(filename, 'w+') as file:
                file.write(output_string)

            print('ok')
            return filename
        return None



    def run(self, filename):
        '''Runs the program created by compile()
        '''
        print('running program...')
        print('\nall text printed below this line is generated by the code segment being run!!')
        print('-------------------------------------------------------------------------------------')
        exec(open(filename).read())