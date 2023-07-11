#!/usr/bin/env python
# SPDX-FileCopyrightText: 2023 Eric Ringeisen
# SPDX-License-Identifier: MIT

"""Example script for managetkeventdata
"""

from . import *

# Example Code
if __name__ == '__main__':
    import tkinter as tk
    import time
    print(tk)
    root = tk.Tk()

    # Set geometry
    root.geometry("400x400")

    # use threading
    def start_work():
        # Call work function
        t1 = threading. Thread(target=work)
        t1.start()

    # work function
    def work():
        name = threading.current_thread().name
        proxy.print(f"{name:16} starting work loop")

        for i in range(3):
            value = f'origin:{name}, loop:{i}'
            proxy.print(f"{name:16} calling proxy.eggs({value!r})")
            proxy.eggs(value)
            time.sleep(1)

        y = 13
        yy = foo_proxy.square(y)
        proxy.print(
            f"{name:16} foo_proxy.square({y!r}) returned {yy}")
        y = 11
        yy = foo_proxy.square(y)
        proxy.print(
            f"{name:16} foo_proxy.square({y!r}) returned {yy}")

        try:
            foo_proxy.boom()
        except ZeroDivisionError as exc:
            proxy.print(f"{name:16} correctly caught {exc!r}")

        proxyexc.bad()


        proxy.print(f"{name:16} work loop finished")

    # Create Button
    tk.Button(root,text="Start Work",command=start_work).pack()


    def handle_it(event):
        print(event)

    bind(root, '<<test>>', handle_it)

    root.after(100, lambda : event_generate(
        root, '<<test>>', ['a', ['b', 'c']]))
    root.after(100, lambda : event_generate(
        root, '<<test>>', "'hi there'"))
    root.after(100, lambda : event_generate(
        root, '<<test>>', {"content": "hi there"}))

    pb = ProxyBuilder(root)

    class Spam:
        def eggs(self, value):

            name = threading.current_thread().name
            print(f'{name:16} executing Spam.eggs({value!r})')

        def bad(self):
            [] + ()

        print = print

    proxy = pb.mute_proxy(Spam())

    def test_handler(exc):
        name = threading.current_thread().name
        print(f'{name:16} test_handler correctly handled the exception {exc!r}')

    proxyexc = pb.mute_proxy(Spam(), exc_handler=test_handler)

    class Foo:
        def square(self, x):
            name = threading.current_thread().name
            print(f'{name:16} executing Foo.square({x!r})')
            return x * x

        def boom(self):
            return 1 / 0

    foo_proxy = pb.proxy(Foo())

    # can call proxy methods in main thread too
    print(foo_proxy.square(5))

    root.mainloop()
