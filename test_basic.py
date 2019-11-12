import imp
import tinyrun

prog_basic_test = r"""
def blah(t):
    x = t
    y = 3
    z = x + y
    return z

a=blah(9)
print(a)

"""
code_basic_test = compile(prog_basic_test,"","exec")






main_mod = imp.new_module('__main__')
tr = tinyrun.TinyRun_VM()
tr.exec_code(code_basic_test,main_mod.__dict__)

print("done")