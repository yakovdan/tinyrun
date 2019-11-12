import imp
import tinyrun

prog_fib=r"""

def fib(n):
    if n== 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)

a = fib(10)
print(a)


"""



code_fib = compile(prog_fib,"","exec")


main_mod = imp.new_module('__main__')
tr = tinyrun.TinyRun_VM()
tr.exec_code(code_fib,main_mod.__dict__)

print("done")