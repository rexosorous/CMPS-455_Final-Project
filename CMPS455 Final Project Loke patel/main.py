# standard libraries
import json

# local modules
import compiler
import translator



if __name__ in '__main__':
    with open('CFG.json', 'r') as file:
        CFG = json.load(file)

    words_list = translator.translate('finalp1.txt', 'finalp2.txt')
    code = compiler.Compiler(CFG, words_list)
    file = code.compile()
    if file:
        code.run(file)