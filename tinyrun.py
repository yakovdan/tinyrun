
class TinyRun():
    
    def __init__(self):
        
        self.stack = [] 
        self.env = {}
        self.translation_dict = {'LN': 'load_name','SN': 'store_name','LV': 'load_value', #translate between opcode names and actual procedures to execute them
                                'ADD_TWO': 'add_two_vals','PRINT_ANS' : 'print_ans'} 

    def store_name(self,name):
        
        value = self.stack.pop()
        self.env[name] = value

    def load_name(self,name):
        
        value = self.env[name]
        self.stack.append(value)

    def load_value(self, number):
        self.stack.append(number)

    def print_ans(self):
        ans = self.stack.pop()
        print(ans)

    def add_two_vals(self):
        
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        total = first_num + second_num
        self.stack.append(total)

    def parse_arg(self, operation, arg, program):
        """ argument can be either a number of a variable name. understand this context specific type and return it's value"""
        value = None
        data = ["LV"]
        var_names = ["LN", "SN"]

        if operation in data:
            value = program["data"][arg]
        elif operation in var_names:
            value = program["vars"][arg]

        return value

    def run_code(self,program):
        
        code = program["code"]


        for instruction in code:
            operation,arg = instruction
            value = self.parse_arg(operation,arg, program)
            if operation in self.translation_dict:
                translate_op = self.translation_dict[operation]
            else:
                raise ValueError("Unsupported opcode")
            bytecode_procedure = getattr(self,translate_op)
            
            if value:
                bytecode_procedure(value)
            else:
                bytecode_procedure()



tr = TinyRun()
prog1 =  {
    "code": [("LV", 0),  # load first value
             ("SN", 0), # store in first variable, x
             ("LV", 1),  # load second value
             ("SN", 1),  # store in second variable, y
             ("LN", 0), # load value from first variable, x
             ("LN", 1), # load value from second variable, y
             ("ADD_TWO", None), # add two values
             ("PRINT_ANS", None)], # print
    "data": [19, 23], 
    "vars": ['x','y'] }

tr.run_code(prog1)



