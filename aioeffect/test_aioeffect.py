import pytest
import asyncio
from functools import partial


from effect import (
    Constant, Delay, Effect,
    base_dispatcher, parallel,
    ComposedDispatcher, FirstError
)
from unittest.mock import patch
from effect.do import do
from . import (
    # deferred_performer,
    performer as asyncio_performer,
    # exc_info_to_failure,
    make_asyncio_dispatcher,
    perform as asyncio_perform
)


def func_dispatcher(intent):
    """
    Simple effect dispatcher that takes callables taking a box,
    and calls them with the given box.
    """
    def performer(dispatcher, intent, box):
        intent(box)
    return performer


@pytest.fixture
def dispatcher():
    return ComposedDispatcher([
        make_asyncio_dispatcher(),
        base_dispatcher
    ])


class TestParallel:
    """Tests for :func:`parallel`."""

    @pytest.mark.asyncio
    async def test_parallel(self, dispatcher):
        """
        'parallel' results in a list of results of the given effects, in the
        same order that they were passed to parallel.
        """
        d = await asyncio_perform(
            dispatcher,
            parallel([
                Effect(Constant('a')),
                Effect(Delay(0.01)).on(success=lambda _: Effect(Constant('...'))),
                Effect(Constant('b'))
            ])
        )
        assert d == ['a', '...', 'b']

    @pytest.mark.asyncio
    async def test_parallel_with_error(self, dispatcher):
        """
        'parallel' results in a list of results of the given effects, in the
        same order that they were passed to parallel.
        """
        @do
        def fail():
            yield Effect(Delay(0.01))
            raise RuntimeError('My error')

        future = asyncio_perform(
            dispatcher,
            parallel([
                Effect(Delay(1)),
                Effect(Delay(1)),
                fail(),
            ])
        )
        with pytest.raises(FirstError):
            await future


class TestDelay:
    """Tests for :class:`Delay`."""

    @pytest.mark.asyncio
    async def test_delay(self, event_loop):
        """
        Delay intents will cause time to pass with reactor.callLater, and
        result in None.
        """
        now = event_loop.time()

        def tick():
            nonlocal now
            now += 1

        def time():
            return now

        with patch.object(event_loop, 'time', new_callable=lambda: time):
            called = []
            eff = Effect(Delay(4)).on(called.append)
            fut = asyncio_perform(make_asyncio_dispatcher(), eff)
            for _ in range(5):
                assert not fut.done()
                assert not called
                event_loop.call_soon(tick)
                await asyncio.sleep(1)
            assert fut.done()
            assert called == [None]


class TestPerform:

    @pytest.mark.asyncio
    async def test_perform(self):
        """
        effect.twisted.perform returns a Deferred which fires with the ultimate
        result of the Effect.
        """
        boxes = []
        e = Effect(boxes.append)
        future = asyncio_perform(func_dispatcher, e)
        assert not future.done()
        boxes[0].succeed("foo")
        await future
        assert future.result() == 'foo'

    @pytest.mark.asyncio
    async def test_perform_failure(self):
        """
        effect.twisted.perform fails the Deferred it returns if the ultimate
        result of the Effect is an exception.
        """
        boxes = []
        e = Effect(boxes.append)
        future = asyncio_perform(func_dispatcher, e)
        assert not future.done()
        boxes[0].fail((ValueError, ValueError("oh dear"), None))
        with pytest.raises(ValueError):
            await future

    def test_promote_metadata(self):
        """
        The decorator copies metadata from the wrapped function onto the
        wrapper.
        """
        def original(dispatcher, intent):
            """Original!"""
            pass
        original.attr = 1
        wrapped = asyncio_performer(original)
        assert wrapped.__name__ == 'original'
        assert wrapped.attr == 1
        assert wrapped.__doc__ == 'Original!'

    def test_ignore_lack_of_metadata(self):
        """
        When the original callable is not a function, a new function is still
        returned.
        """
        def original(something, dispatcher, intent):
            """Original!"""
            pass
        new_func = partial(original, 'something')
        original.attr = 1
        wrapped = asyncio_performer(new_func)
        assert wrapped.__name__ == 'asyncio_wrapper'

    @pytest.mark.asyncio
    async def test_kwargs(self):
        """Additional kwargs are passed through."""
        @asyncio_performer
        async def p(dispatcher, intent, extra):
            return extra

        def dispatcher(_):
            return partial(p, extra='extra val')
        result = await asyncio_perform(dispatcher, Effect('foo'))
        assert result == 'extra val'
