"""
AsyncIO integration for the Effect library.

The most important functions here are :func:`perform`,
:func:`make_twisted_dispatcher`, and :func:`deferred_performer`.

Note that the core effect library does *not* depend on AsyncIO, but this module
does.
"""
import sys
from asyncio import Future, get_event_loop, sleep

from effect import (
    Delay,
    ParallelEffects,
    perform as base_perform,
    TypeDispatcher)
from effect._utils import wraps
from effect.async import perform_parallel_async


def future_to_box(fut, box):
    """
    Make a Future pass its success or fail events on to the given box.
    """
    def done_cb(fut):
        try:
            box.succeed(fut.result())
        except:
            box.fail(sys.exc_info())

    fut.add_done_callback(done_cb)
    box.asyncio_future = fut


def make_asyncio_dispatcher(loop=None):
    """
    Create a dispatcher that knows how to perform certain built-in Intents
    with asyncio-specific implementations.
    """
    return TypeDispatcher({
        ParallelEffects: perform_parallel_async,
        Delay: perform_delay,
    })


def performer(f):
    """
    A decorator for performers that returns a Future.

    The function being decorated is expected to take a dispatcher and an intent
    (and not a box), and must return a Future. The wrapper function
    that this decorator returns will accept a dispatcher, an intent, and a box
    (conforming to the performer interface). The wrapper deals with
    putting the Future's result into the box.

    Example::

        @performer
        async def perform_foo(dispatcher, foo):
            return await do_side_effecting_deferred_operation(foo)
    """

    @wraps(f)
    def asyncio_wrapper(*args, **kwargs):
        *pass_args, box = args
        task = get_event_loop().create_task(f(*pass_args, **kwargs))
        future_to_box(task, box)
    return asyncio_wrapper


@performer
def perform_delay(dispatcher, delay):
    """
    Perform a :obj:`effect.Delay` with asyncio's :func:`asyncio.sleep`.
    """
    return sleep(delay.delay)


def perform(dispatcher, effect):
    """
    Perform an effect, returning a Future that will fire with the effect's
    ultimate result.
    """
    fut = Future()
    eff = effect.on(success=fut.set_result, error=lambda e: fut.set_exception(e[1]))
    base_perform(dispatcher, eff)
    return fut


# async def perform(dispatcher, effect):
#     """
#     Perform an effect, returning a Future that will fire with the effect's
#     ultimate result.
#     """
#     performer = dispatcher(effect.intent)
#     if performer is None:
#         raise NoPerformerFoundError(effect.intent)
#     ret = performer(dispatcher, effect.intent)
#     if isinstance(ret, asyncio.Future):
#         ret = await ret
#     return ret


__author__ = 'Emmanuel Leblond'
__email__ = 'emmanuel.leblond@gmail.com'
__version__ = '1.0.0'
__all__ = (
    'future_to_box',
    'make_asyncio_dispatcher',
    'performer',
    'perform_delay',
    'perform'
)
