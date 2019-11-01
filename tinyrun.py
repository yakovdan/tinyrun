
import inspect
import types
import dis
import sys
import imp
# Frame class handles frames. each frame contains a block stack and a data stack of it's own
# each frame also contains it's own code


class Frame():
    def __init__(self, code_obj, global_names, local_names, prev_frame):
        self.f_block_stack = []
        self.f_data_stack = []
        
        self.f_code_obj = code_obj
        self.f_global_names = global_names 
        self.f_local_names = local_names
        self.f_prev_frame = prev_frame
        
        if prev_frame:
            self.f_builtin_names = prev_frame.f_builtin_names
        else:
            self.f_builtin_names = local_names['__builtins__']
            if hasattr(self.f_builtin_names, '__dict__'):
                self.f_builtin_names = self.f_builtin_names.__dict__

        self.f_last_instruction = 0


class AFunction():
   
    # store function metadata. this is essentially a wrapper around a python function object. 
    def __init__(self, name, code, globs, defaults, vm):
        
        self.vm = vm
        self.func_code = code
        self.func_name = code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self.vm.cur_frame.f_local_names
               
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        
        kw = { 'argdefs': tuple(defaults)}
       
        self._func = types.FunctionType(code, globs, **kw)

    def __call__(self, *args, **kwargs):
        """When calling a AFunction, make a new frame and run it."""
        callargs = inspect.getcallargs(self._func, *args, **kwargs)
        # Use callargs to provide a mapping of arguments: values to pass into the new 
        # frame.
        frame = self.vm.make_new_frame(self.func_code, callargs, self.func_globals, {})
        return self.vm.execute_frame(frame)






class TinyRun_VM():
    
    def __init__(self):
        
        self.frames = []
        # current frame description
        self.cur_frame = None
        self.cur_return_value = None
        self.last_exception = None

        self.stack = [] 
      
        self.byte_method_dict = {101: self.load_name,124: self.load_fast,125: self.store_fast,90: self.store_name,100: self.load_const, #translate between opcode names and actual procedures to execute them
                                23: self.binary_add,83 : self.return_value, 132: self.make_function,131: self.call_function,1: self.pop_top} 

    ############ next are some functions to make access to the data stack of the current frame easy
    def top(self):
        return self.cur_frame.f_data_stack[-1]

    def pop(self):
        return self.cur_frame.f_data_stack.pop()

    def push(self, *vals):
        self.cur_frame.f_data_stack.extend(vals)

    def popn(self, n):
        """
        pop topmost n elements from the current frame's data stack
        if there are less than n elements, return every element
        """
        if n:
            ret = self.cur_frame.f_data_stack[-n:]
            self.cur_frame.f_data_stack[-n:] = []
            return ret
        else:
            return []

    ###### next are some functions to execute opcodes
    def pop_top(self):
        self.pop()
    
    def store_fast(self,name):
        
        value = self.pop()
        self.cur_frame.f_local_names[name] = value

    def store_name(self,name):
        value = self.pop()
        self.cur_frame.f_local_names[name] = value

    def load_name(self,name):
        if name in self.cur_frame.f_local_names:
            value = self.cur_frame.f_local_names[name]
        elif name in self.cur_frame.f_global_names:
            value = self.cur_frame.f_global_names[name]
        elif name in self.cur_frame.f_builtin_names:
            value = self.cur_frame.f_builtin_names[name]
        else:
            raise UnboundLocalError("local variable '%s' referenced before assignment" % name)
        self.push(value)

    def load_fast(self,name):
        
        if name in self.cur_frame.f_local_names:
            value = self.cur_frame.f_local_names[name]
        else:
            raise UnboundLocalError("local variable '%s' referenced before assignment" % name)
        self.push(value)

    def load_const(self, value):
        self.push(value)

    def return_value(self):
        self.cur_return_value = self.pop()
        return "return"

    def binary_add(self):
        
        first_num = self.pop()
        second_num = self.pop()
        total = first_num + second_num
        self.push(total)

    def make_function(self, argc):
        name = self.pop()
        code = self.pop()
        defaults = self.popn(argc)
        globs = self.cur_frame.f_global_names
        fn = AFunction(name, code, globs, defaults, self)
        self.push(fn)
    
    def call_function(self,arg):
        lenPos=arg
        posargs = self.popn(lenPos)

        func = self.pop()
        
        retval = func(*posargs)
        self.push(retval)

    ###### parse bytecode and get argument if any

    def parse_byte_and_args(self):
        f = self.cur_frame
        op_offset = f.f_last_instruction
        bytecode = list(f.f_code_obj.co_code)[op_offset]
        f.f_last_instruction += 2 # new in python ver >= 3.6, 16 bit wordcode
        
        if bytecode >= dis.HAVE_ARGUMENT:
            argument = []
            
            arg_bytecode = list(f.f_code_obj.co_code)[f.f_last_instruction-1]  
                
            if bytecode in dis.hasconst:   # Look up a constant
                argument = [f.f_code_obj.co_consts[arg_bytecode]]
            elif bytecode in dis.hasname:  # Look up a name
                argument = [f.f_code_obj.co_names[arg_bytecode]]
            elif bytecode in dis.haslocal: # Look up a local name
                argument = [f.f_code_obj.co_varnames[arg_bytecode]]
            elif bytecode in dis.hasjrel:  # Calculate a relative jump
                argument = [f.f_last_instruction + arg_bytecode]
            else:
                argument = [arg_bytecode]
        else:
            argument = []

        return bytecode, argument


    def make_new_frame(self,code,callargs = {},gl_names = None,loc_names = None):
        if gl_names is not None and loc_names is not None:
            loc_names = gl_names # global names are avialable inside a function, simplify lookup
        elif self.frames: # if there already is a frame on the callstack, inherit global namespace
            gl_names = self.cur_frame.global_names
            loc_names = {}
        else: # fresh start
            gl_names = loc_names = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__': None,
            }
        loc_names.update(callargs)
        return Frame(code, gl_names,loc_names,self.cur_frame)
    
    # execute code in a new frame.

    def dispatch(self, bytecode, argument):
        """ Dispatch by bytecode to the corresponding methods in byte_method_dict
        exceptions are caught and set on the virtual machine. 
        keep state info too
        
        """

        
        state = None
        try:
            bytecode_fn = None
            if bytecode in self.byte_method_dict:
                bytecode_fn = self.byte_method_dict[bytecode]
                state = bytecode_fn(*argument)
            
            else:
                raise ValueError("unsupported bytecode type: %d" % bytecode)
                    
            
        except:
            # deal with exceptions encountered while executing the op.
            self.last_exception = sys.exc_info()[:2] + (None,)
            state = 'exception'

        return state

   
    def push_frame(self, frame):
            self.frames.append(frame)
            self.cur_frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.cur_frame = self.frames[-1]
        else:
           self.frame = None

    def execute_frame(self, frame):
        
        self.push_frame(frame)
        while True:
            bytecode, arguments = self.parse_byte_and_args()
            state = self.dispatch(bytecode, arguments)
            
            if state:
                break

        self.pop_frame()

        if state == 'exception':
            exc, val, tb = self.last_exception
            e = exc(val)
            e.__traceback__ = tb
            raise e

        return self.cur_return_value
    ##### entry point
    def exec_code(self, code, global_names=None, local_names=None):
        """ An entry point to execute code using TinyVM."""
        frame = self.make_new_frame(code, gl_names=global_names, loc_names=local_names)
        return self.execute_frame(frame)





prog1 = 'def blah(t):\n\tx = t\n\ty = 3\n\tz = x + y\n\treturn z\na=blah(9)\nprint(a)\n\n'
code1 = compile(prog1,"","exec")

main_mod = imp.new_module('__main__')
    
tr = TinyRun_VM()

value  = tr.exec_code(code1,main_mod.__dict__)





