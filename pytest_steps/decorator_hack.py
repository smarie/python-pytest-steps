from decorator import iscoroutinefunction, FunctionMaker


class MyFunctionMaker(FunctionMaker):
    """
    Overrides FunctionMaker so that additional arguments can be inserted in the resulting signature.
    """

    @classmethod
    def create(cls, obj, body, evaldict, defaults=None,
               doc=None, module=None, addsource=True, add_args=None, **attrs):
        """
        Create a function from the strings name, signature and body.
        evaldict is the evaluation dictionary. If addsource is true an
        attribute __source__ is added to the result. The attributes attrs
        are added, if any.
        """
        if isinstance(obj, str):  # "name(signature)"
            name, rest = obj.strip().split('(', 1)
            signature = rest[:-1]  # strip a right parens
            func = None
        else:  # a function
            name = None
            signature = None
            func = obj
        self = cls(func, name, signature, defaults, doc, module)
        ibody = '\n'.join('    ' + line for line in body.splitlines())
        caller = evaldict.get('_call_')  # when called from `decorate`
        if caller and iscoroutinefunction(caller):
            body = ('async def %(name)s(%(signature)s):\n' + ibody).replace(
                'return', 'return await')
        else:
            body = 'def %(name)s(%(signature)s):\n' + ibody

        # --- HACK is only here -----
        if add_args is not None:
            for arg in add_args:
                if arg not in self.args:
                    self.args = [arg] + self.args
                else:
                    # the argument already exists in the wrapped function, no problem.
                    pass

            # update signatures (this is a copy of the init code)
            allargs = list(self.args)
            allshortargs = list(self.args)
            if self.varargs:
                allargs.append('*' + self.varargs)
                allshortargs.append('*' + self.varargs)
            elif self.kwonlyargs:
                allargs.append('*')  # single star syntax
            for a in self.kwonlyargs:
                allargs.append('%s=None' % a)
                allshortargs.append('%s=%s' % (a, a))
            if self.varkw:
                allargs.append('**' + self.varkw)
                allshortargs.append('**' + self.varkw)
            self.signature = ', '.join(allargs)
            self.shortsignature = ', '.join(allshortargs)
        # ---------------------------

        func = self.make(body, evaldict, addsource, **attrs)

        # ----- another hack
        if add_args is not None:
            # we have to delete this annotation otherwise the inspect.signature method misinterpretes the signature
            del func.__wrapped__

        return func


def my_decorate(func, caller, extras=(), additional_args=None):
    """
    A clone of 'decorate' with the possibility to add additional args to the function signature.
    """
    evaldict = dict(_call_=caller, _func_=func)
    es = ''
    for i, extra in enumerate(extras):
        ex = '_e%d_' % i
        evaldict[ex] = extra
        es += ex + ', '
    fun = MyFunctionMaker.create(
        func, "return _call_(_func_, %s%%(shortsignature)s)" % es,
        evaldict, add_args=additional_args, __wrapped__=func)
    if hasattr(func, '__qualname__'):
        fun.__qualname__ = func.__qualname__
    return fun
