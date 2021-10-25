import builtins
import subprocess

def convert(input, output, *args, **kwargs):
    def args_():
        yield "convert"
        for v in args:
            if type(v) in [tuple, builtins.list]:
                for x in v:
                    yield str(x)
            else:
                yield str(v)
        for k, v in kwargs.items():
            yield f"-{k}"
            if type(v) in [tuple, builtins.list]:
                for x in v:
                    yield str(x)
            else:
                yield str(v)

    if type(input) is tuple:
        res = subprocess.run([*args_(), input[0], output], input=input[1], capture_output=True)
    else:
        res = subprocess.run([*args_(), input, output], capture_output=True)
    return res.stdout

def list(*args):
    res = subprocess.run(["convert", "-list", *args], capture_output=True)
    return res.stdout
