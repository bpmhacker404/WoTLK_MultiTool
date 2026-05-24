import asyncio


class AsyncManager:
    def __init__(self):
        self.loop = None
        self.task_group = None
        self._queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._tasks = {}

    async def start(self):
        self.loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()

        async with asyncio.TaskGroup() as tg:
            self.task_group = tg
            tg.create_task(self._worker())

            await self._stop_event.wait()

    def stop(self):
        if self.loop and self.loop.is_running() and self._stop_event:
            self.loop.call_soon_threadsafe(self._stop_event.set)

    def run_unique_task(self, coro):
        if self.loop and self.loop.is_running() and self.task_group:
            existing_task = self._tasks.get(coro.__name__)
            if existing_task and not existing_task.done():
                coro.close()
                return

            self.loop.call_soon_threadsafe(self._queue.put_nowait, coro)

    async def _worker(self):
        while not self._stop_event.is_set():
            coro = await self._queue.get()
            self._create_managed_task(coro)
            self._queue.task_done()

    def _create_managed_task(self, coro):
        task = asyncio.create_task(coro)
        self._tasks[coro.__name__] = task
        task.add_done_callback(lambda t: self._tasks.pop(coro.__name__, None))
        return task


async_manager = AsyncManager()


def run_async_thread():
    asyncio.run(async_manager.start())
