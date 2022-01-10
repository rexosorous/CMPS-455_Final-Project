def get_words(contents: str) -> [str]:
    '''Splits up a string into alphanumeric words and special characters

    Example:
        input_string = 'lorem ipsum;dolor 100 sit*amet200'
        output_list = get_words(input_)
        print(output_list)
        > ['lorem', 'ipsum', ';', 'dolor', '100', 'sit', '*', 'amet200']

    Args:
        contents (str): the string to split up

    Returns:
        [str]: a list of every word in the contents
    '''
    words = []
    word = ''
    for char in contents:
        if char.isalnum():
            word += char
            continue
        if word:
            words.append(word)
        if char != ' ' and char != '\t':
            words.append(char)
        word = ''
    return words



def char_combiner(char: str, list_: list, ) -> [str]:
    '''Combines two consecutive characters in a list into one element

    Example:
        input_list = ['lorem', '*', '*', '*', 'ipsum']
        output_list = char_combiner('*', input_list)
        print(output_list)
        > ['lorem', '**', '*', 'ipsum']

    Args:
        char (str): the character or string phrase to combine into
        list_ ([str]): the list to search

    Returns:
        [str]: the updated list
    '''
    return_me = []
    skip = False
    for index in range(len(list_)):
        if index == len(list_)-1:
            if not skip:
                return_me.append(list_[index])
            break
        if list_[index] == '*' and list_[index+1] == '*':
            return_me.append('**')
            skip = True
        elif skip:
            skip = False
            continue
        else:
            return_me.append(list_[index])
    return return_me



def comment_remover(words_list: list) -> [str]:
    '''Removes comments from the words list

    Removes every list element between two '**' as well as the '**' themselves

    Args:
        words_list ([str]): the words list to remove comments from

    Returns:
        [str]: the updated list
    '''
    while '**' in words_list:
        if len([x for x in words_list if x == '**']) > 1: # makes sure there's an ending '**' for the comment
            del words_list[words_list.index('**'):words_list.index('**', words_list.index('**')+1)+1]
        else:
            del words_list[words_list.index('**'):] # if there is no ending '**', then assume everything after the first '**' is a comment
    return words_list



def rm_cons_dupes(char: str, words_list: list) -> [str]:
    '''Removes any consecutive duplicates of a character in a list

    Example:
        input_list = ['lorem', 'ipsum', 'ipsum', 'ipsum', 'dolor', 'dolor']
        output_list = rm_cons_dupes('ipsum', input_list)
        print(output_list)
        > ['lorem', 'ipsum', 'dolor', 'dolor']

    Args:
        char (str): the character or string phrase to remove duplicates of
        words_list ([str]): the list to edit

    Returns:
        [str]: the updated list
    '''
    return [value for index, value in enumerate(words_list) if index == 0 or value != words_list[index-1]]



def special_case_fixer(words_list: list) -> [str]:
    '''There are two entries in particular that need to fixed.

    "value=" gets expanded into [\u201c, value, =, \u201d]
    end. gets expanded into [end, .]

    Args:
        words_list ([str])

    Returns:
        [str]
    '''
    if '\u201c' in words_list:
        # fix "value="
        index = words_list.index('\u201c')
        if words_list[index:index+4] == ['\u201c', 'value', '=', '\u201d']:
            words_list = words_list[:index] + words_list[index+4:]
            words_list.insert(index, '"value="')

    if '"' in words_list:
        # fix "value="
        while '"' in words_list:
            index = words_list.index('"')
            if words_list[index:index+4] == ['"', 'value', '=', '"']:
                words_list = words_list[:index] + words_list[index+4:]
                words_list.insert(index, '"value="')

    if 'end' in words_list:
        # fix end.
        index = words_list.index('end')
        if words_list[index+1] == '.':
            words_list = words_list[:index] + words_list[index+2:]
            words_list.insert(index, 'end.')

    return words_list




def translate(input_file: str, output_file: str) -> [str]:
    '''Translates the contents of a file into a list of words that the compiler can better understand

    1. separates the text into words
    2. removes white space
    3. removes comments
    4. removes empty lines

    Args:
        input_file (str): the filename of the file to read from
        output_file (str): the filename of the file to write to

    Returns:
        [str]: a list of words translated from the input file
    '''
    print(f'reading {input_file}...', end=' ')
    with open(input_file, 'r', encoding='utf8') as file:
        contents = file.read()
    print('ok')

    print(f'translating {input_file}...', end=' ')
    words = get_words(contents)
    words = char_combiner('*', words)
    words = comment_remover(words)
    words = rm_cons_dupes('\n', words)
    words = special_case_fixer(words)
    print('ok')

    print(f'output to {output_file}...', end=' ')
    with open(output_file, 'w+') as file:
        file.write('\n'.join(' '.join(words).split(' \n ')))
    print('ok')

    return [w for w in words if w != '\n'] + ['$']



def translate_lines(input_file: str) -> {int: [str]}:
    '''Translates the contents of a file into a list of words split by lines

    Used only for outputing more precise error messages

    Args:
        input_file (str)

    Returns:
        {int: [str]}: keys are line numbers, values are lists whose elements are the words for that line
    '''
    with open(input_file, 'r', encoding='utf8') as file:
        lines = [x for x in file]

    fixed_lines = dict()
    for index in range(len(lines)):
            contents = lines[index]
            words = get_words(contents)
            words = char_combiner('*', words)
            fixed_lines[index] = [w for w in words if w != '\n']

    # remove multi-line comments
    multi_line = False
    for key in fixed_lines:
        line = fixed_lines[key]
        if multi_line:
            if '**' in line:
                fixed_lines[key] = fixed_lines[key][line.index('**')+1:]
                multi_line = False
            else:
                fixed_lines[key] = []

        line = fixed_lines[key]
        if len([x for x in line if x == '**']) % 2 == 1: # if there's an odd frequency of '**', then there's a multi-line comment
            multi_line = True
            last_pos = len(line) - line[::-1].index('**') - 1 # last position of '**'
            fixed_lines[key] = fixed_lines[key][:last_pos]

    for key in fixed_lines:
        fixed_lines[key] = comment_remover(fixed_lines[key])
        fixed_lines[key] = special_case_fixer(fixed_lines[key])

    return fixed_lines