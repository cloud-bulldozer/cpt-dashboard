import asyncio

from typing import Coroutine, Callable, Any, List, TypeVar

import trio


async def trio_run_with_asyncio(trio_fn, *args):

    asyncio_loop = asyncio.get_running_loop()

    def run_sync_soon_threadsafe(fn):
        asyncio_loop.call_soon_threadsafe(fn)

    done_fut = asyncio.Future()

    def done_callback(trio_main_outcome):
        done_fut.set_result(trio_main_outcome)

    trio.lowlevel.start_guest_run(
        trio_fn, *args,
        run_sync_soon_threadsafe=run_sync_soon_threadsafe,
        done_callback=done_callback,
        host_uses_signal_set_wakeup_fd=True
    )
    trio_main_outcome = await done_fut
    return trio_main_outcome.unwrap()
