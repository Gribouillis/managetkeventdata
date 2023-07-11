#!/usr/bin/env python
# SPDX-FileCopyrightText: 2023 Eric Ringeisen
# SPDX-License-Identifier: MIT

"""Manage virtual events carrying arbitrary data in tkinter

This module 'managetkeventdata' offers the following features

1) Generate virtual events in tkinter carrying any Python
object as client data (which tkinter cannot do natively).

2) Bind virtual events to event handler in order to receive
these virtual events and their client data.

3) Create proxies of Python objects which methods can
be called from any thread but are executed in tkinter's
main thread. Two kinds of proxies can be created:
    * 'mute' proxies which methods have no return values (like procedures)
    * 'ordinary' proxies which methods have a return value (like functions)
The advantage of mute proxies is that the calling thread
doesn't have to wait for the return value when calling a
method.

The virtual events can be generated in any thread, the
event handlers are always executed by tkinter's main thread.

In particular, this allows threads to update widgets by
defining event handlers that manipulate the widgets.

Usage example with event generation:

    # create root widget
    root = Tk()

    # Define an event handler for the example
    def handle_it(event):
        print(event.widget)
        print(event.data)

    # Use the instance to bind a virtual event to the handler
    bind(root, '<<test>>', handle_it)

    # Later in code, generate virtual event with client data.
    # The event generation can be done in another thread,
    # The client data can be an arbitrary Python object.
    ...
    event_generate(root, '<<test>>', ['a', ['b', 'c']]))

Usage example with object proxy:

    class Spam:
        def ham(self, foo, bar=''):
            return bar + foo + bar

    root = Tk()
    pb = ProxyBuilder(root)
    proxy = pb.proxy(Spam())

    def work():
        # method call in other thread
        # actual execution of object method in main thread
        s = proxy.ham('oof', bar='--') # returns '--oof--'

    def start_work():
        threading.Thread(target=work).start()

    Button(root,text="Start Work",command=start_work).pack()
    root.main_loop()
"""


# Developed starting from FabienAndre's reply in this thread
# https://stackoverflow.com/questions/16369947/python-tkinterhow-can-i-fetch-the-value-of-data-which-was-set-in-function-eve
# Also inspired by https://pypi.org/project/wxAnyThread/

__version__ = '2023.07.09'

import abc
from functools import partial
from collections import deque, namedtuple
import itertools
import threading
from typing import Any, Callable, Optional

def init_module():

    # hide global objects
    datastream = deque()
    count = itertools.count()
    generation_lock = threading.RLock()
    local = threading.local()
    dequeue = datastream.popleft
    enqueue = datastream.append
    virtual_event = '<<managetkeventdata-call>>'

    def bind(
        widget: 'tkinter.Misc',
        sequence: str,
        func: Callable[["SmallEvent"], Optional[str]],
        add: bool = False):
        """Bind to this widget at event SEQUENCE a call to function FUNC.

        See the documentation of tkinter.Misc.bind() for a description
        of the arguments"""
        def _substitute(*args):
            index = int(args[0])
            while True:
                n, data = dequeue()
                if n >= index:
                    break
            assert n == index
            return (SmallEvent(data, widget),)

        funcid = widget._register(func, _substitute, needcleanup=1)
        cmd = f'{"+" if add else ""}if {{"[{funcid} %d]" == "break"}} break\n'
        widget.tk.call('bind', widget._w, sequence, cmd)

    def event_generate(
        widget: "tkinter.Misc",
        sequence: str,
        data: Any=None):
        """Generate an event SEQUENCE. Additional argument DATA
        specifies a field .data in the generated event."""
        with generation_lock:
            index = next(count)
            enqueue((index, data))
            # when='tail': place the event on Tcl's event queue
            # behind any events already queued for this application.
            # This is necessary so that events are processed by the
            # main thread and not by the current thread, and also
            # it ensures that events are handled in the same order
            # that the datastream is enqueued
            widget.event_generate(
                sequence, data=str(index), when='tail')

    class ReturnCell:
        """Object used to pass a return value between threads.

        One such cell is created for every thread
        that call ordinary proxy methods returning values.
        The cell is used by the main thread that actually
        executes the method to hold the method's return value
        or exception. The calling thread then reads these values
        in the cell."""
        def __init__(self):
            # This member holds the return value of a method call
            self._value: Any = None
            # This flag indicates that a method call raised an exception
            self.err_flag: bool = False
            # This waitable event indicates that the cell is ready
            # to be read after a method call has been executed
            self.bell = threading.Event()

        def set_return(self, value):
            old_value, self._value = self._value, value
            return old_value

    main_cell_set = False

    def return_cell():
        '''Return a thread-local return cell

        In the main thread, return None'''
        nonlocal main_cell_set
        try:
            c = local.return_cell
        except AttributeError:
            if main_cell_set or (
                threading.current_thread() is not threading.main_thread()):
                c = ReturnCell()
            else:
                c = None
                main_cell_set = True
            local.return_cell = c
        return c

    # if we are initializing in the main thread,
    # set main thread's cell to None immediately to avoid later checks
    if threading.current_thread() is threading.main_thread():
        return_cell()

    # General event handler that receives all proxy method call events.
    def handle_call(event):
        # dispatch the event to its own specific handler.
        event.data.handler(event)

    class Handler(abc.ABC):
        """Base class of callable objects that handle virtual events"""
        @abc.abstractmethod
        def __call__(self, event):
            ...

    class ProcHandler(Handler):
        """Èvent handler for mute proxy method calls"""
        def __call__(self, event):
            event.data.func()

    class ProcExcHandler(Handler):
        """Event handler for mute proxy method calls with exception handling"""
        def __init__(self, exc_handler: Callable[[Exception], Any]):
            super().__init__()
            self._exc_handler = exc_handler

        def __call__(self, event):
            func = event.data.func
            try:
                func()
            except Exception as exc:
                self._exc_handler(exc)

    class FuncHandler:
        """Event handler for ordinary proxy method calls with return and exception"""
        def __call__(self, event):
            _, cell, func = event.data
            try:
                result = func()
            except Exception as exc:
                err_flag = True
                result = exc
            else:
                err_flag = False
            cell.err_flag = err_flag
            cell.set_return(result)
            cell.bell.set()

    class Generator(abc.ABC):
        """Base class of callable objects that generate a virtual event when a proxy method is called."""
        def __init__(self, handler):
            self._handler = handler

        @abc.abstractmethod
        def __call__(self, widget, func):
            ...

    class ProcGenerator(Generator):
        """Generate an event when a mute proxy method is called"""
        EventData = namedtuple('EventData', 'handler func')

        def __call__(self, widget, func):
            event_generate(
                widget, virtual_event, self.EventData(self._handler, func))

    class FuncGenerator(Generator):
        """Generate an event when an ordinary proxy's method is called"""
        EventData = namedtuple('EventData', 'handler cell func')

        def __call__(self, widget, func):
            if not (cell := return_cell()):
                # if in main thread, call the method directly
                result = func()
            else:
                cell.bell.clear()
                event_generate(
                    widget,
                    virtual_event,
                    self.EventData(self._handler, cell, func))
                # wait until the main thread handles the event
                cell.bell.wait()
                # read the return value or exception
                result = cell.set_return(None)
                if cell.err_flag:
                    raise result
            return result

    def make_proxy(
        generator: Generator, widget: "tkinter.Misc", obj: Any):
        """Internal function to create a Proxy object wrapping
        OBJ and using GENERATOR to send events to WIDGET when
        the proxy's methods are called."""

        def method(func, *args, **kwargs):
            return generator(widget, partial(func, *args, **kwargs))

        def _getattr(name):
            return partial(method, getattr(obj, name))

        return Proxy(_getattr)


    class ProxyBuilder:
        """Helper object to build proxies"""
        def __init__(self, widget):
            bind(widget, virtual_event, handle_call)
            self._widget = widget

        def mute_proxy(self, obj: object, exc_handler: [[Exception], None]=None):
            """Create a mute proxy wrapping OBJ and using the optional exception handler EXC_HANDLER.

            Calls on mute proxies methods do not return values nor do they
            raise exceptions. If EXC_HANDLER is not None, it is a function
            that will be called if the object wrapped by the proxy raises
            an exception in one of its method calls.
            """
            handler = ProcExcHandler(exc_handler) if exc_handler else ProcHandler()
            return make_proxy(ProcGenerator(handler), self._widget, obj)

        def proxy(self, obj):
            """Create an ordinary proxy wrapping OBJ.

            Method calls on these proxies transmit values returned
            or exceptions raised to the calling thread."""
            return make_proxy(FuncGenerator(FuncHandler()), self._widget, obj)


    # Only a few names are made available in the module's global
    # namespace. They constitute the public interface of this module.
    v = vars()
    globals().update(
        {name: v[name] for name in
            ['bind', 'event_generate', 'ProxyBuilder']})

init_module()
del init_module

SmallEvent = namedtuple('SmallEvent', 'data widget')

class Proxy:
    def __init__(self, getattr):
        self._getattr = getattr

    def __getattr__(self, name):
        return self._getattr(name)
