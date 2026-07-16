class BaseEvents:
    def __init__(self):
        # A list to keep track of any function using @dec
        self.instances = {}
        self.registered_functions = []

    def bind(self, instance): 
        cls = instance.__class__.__name__
        self.instances[cls] = instance
# 
    def __call__(self, arg):
        # 1. If Python passes a function, we treat it as a decorator setup
        if callable(arg):
            self.registered_functions.append(arg)
            return arg  # Return the function unmodified

        # 2. If you pass a number/string, we execute the saved functions
        else:
            for func in self.registered_functions:
                parent = func.__qualname__.split(".")[0]
                cls = self.instances[parent]
                func(cls , arg)


on_ready = BaseEvents()
on_start = BaseEvents()
on_end = BaseEvents()
on_play = BaseEvents()
on_pause = BaseEvents()
on_pos = BaseEvents()
on_duration = BaseEvents()
on_volume = BaseEvents()
on_speed = BaseEvents()
on_buffering = BaseEvents()
on_error = BaseEvents()
on_log = BaseEvents()


# tests
# class D:
#     def __init__(self):
#         self.registered_functions = []
#         self.instance = None

#     def bind(self, instance):
#         self.instance = instance
#         print(self , instance)

#     def __call__(self, arg):
#         if callable(arg):
#             self.registered_functions.append(arg)
#             return arg

#         for func in self.registered_functions:
#             func(self.instance, arg)
    
# on_d = D()

# class B:
#     hugg = 90
#     def __init__(self,*args , **kwargs):
#         on_error.bind(self)
#     @on_error
#     def gg(self,*a): print('from class : ',self,a , self.hugg)

# class C:
#     hugg = 91
#     def __init__(self,*args , **kwargs):
#         on_error.bind(self)
#     @on_error
#     def gg(self,*a): print('from class : ',self,a , self.hugg)


# B()
# import time ; time.sleep(1.1)
# C()
# on_error(5)
# on_error(1,)

