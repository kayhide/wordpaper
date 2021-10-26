import io
import json
import os


class Callbacks:
    def __init__(self):
        self.__on_exist = []
        self.__on_create = []

    def on_exist(self, f):
        self.__on_exist.append(f)

    def on_create(self, f):
        self.__on_create.append(f)

    def fire_exist(self, path):
        for f in self.__on_exist:
             f(path)

    def fire_create(self, path):
        for f in self.__on_create:
             f(path)


class CacheEntry:
    def __init__(self, path, is_text=False, callbacks=Callbacks()):
        self.path = path
        self.is_text = is_text
        self.callbacks = callbacks

    def put(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        return self

    def content(self, force=False, quiet=False):
        binary_mode = "" if self.is_text else "b"
        if os.path.exists(self.path):
            if force:
                os.remove(self.path)
            else:
                if not quiet:
                    self.callbacks.fire_exist(self.path)
                with open(self.path, f"r{binary_mode}") as f:
                    return f.read()

        res = self.fn(*self.args, **self.kwargs)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, f"w{binary_mode}") as f:
            f.write(res)
        if not quiet:
            self.callbacks.fire_create(self.path)

        return res

    def file(self, force=False, **kwargs):
        if os.path.exists(self.path):
            if force:
                self.content(force=True, **kwargs)
            else:
                self.callbacks.fire_exist(self.path)
        else:
            self.content(**kwargs)
        return self.path

    def load(self, **kwargs):
        return json.loads(self.content(**kwargs))

def to_basename(word):
    return word.replace(' ', '_')

class Cache:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.__callbacks = Callbacks()

    @property
    def callbacks(self):
        return self.__callbacks

    def to_path(self, *args, ext=None):
        paths = [to_basename(x) for x in args]
        if ext:
            paths[-1] = f"{paths[-1]}.{ext}"
        return os.path.join(self.cache_dir, *paths)

    def json(self, *args):
        return CacheEntry(self.to_path(*args, ext="json"), is_text=True, callbacks=self.callbacks)

    def jpeg(self, *args):
        return CacheEntry(self.to_path(*args, ext="jpeg"), callbacks=self.callbacks)

    def png(self, *args):
        return CacheEntry(self.to_path(*args, ext="png"), callbacks=self.callbacks)

