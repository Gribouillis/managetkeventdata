# Manage virtual events carrying arbitrary data in tkinter!

[![License: MIT](https://img.shields.io/github/license/Gribouillis/managetkeventdata)](https://opensource.org/licenses/MIT)
[![stars](https://img.shields.io/github/stars/Gribouillis/managetkeventdata)]()
[![Github All Releases](https://img.shields.io/github/downloads/Gribouillis/managetkeventdata/total.svg)]()
[![PyPI](https://img.shields.io/pypi/v/managetkeventdata)](https://pypi.org/project/managetkeventdata/)
[![python](https://img.shields.io/github/languages/top/Gribouillis/managetkeventdata)]()

[![Build Status](https://scrutinizer-ci.com/g/Gribouillis/managetkeventdata/badges/build.png?b=main)](https://scrutinizer-ci.com/g/Gribouillis/managetkeventdata/build-status/main)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/Gribouillis/managetkeventdata/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/Gribouillis/managetkeventdata/?branch=main)
[![Release date](https://img.shields.io/github/release-date/Gribouillis/managetkeventdata)]()
[![Latest Stable Version](https://img.shields.io/github/v/release/Gribouillis/managetkeventdata)]()

[![tweet](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2FGribouillis%2Fmanagetkeventdata)](https://twitter.com/intent/tweet?text=I%20found%20this%20awesome%20repo%20on%20GitHub%20%26%20PyPI%20that%20simplifies%20life%20of%20developers%20so%20much!&url=https%3A%2F%2Fgithub.com%2FGribouillis%2Fmanagetkeventdata)

## Install from main branch
```
python -m pip install git+https://github.com/Gribouillis/managetkeventdata.git
```

# Usage

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

```
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
```
Usage example with object proxy:
```
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
```

[Github-flavored Markdown](https://guides.github.com/features/mastering-markdown/)


