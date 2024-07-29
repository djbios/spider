import asyncio


class BaseRoutine:
    async def tick(self):
        """Routine main method, expected to be ran in a while true loop"""
        raise NotImplementedError


class RoutinesRegistry:
    routines_classes: list[type[BaseRoutine]] = []
    routines_instances: list[BaseRoutine] = []
    routines_coroutine: asyncio.Task

    @classmethod
    def register(cls):
        def decorator(klass):
            cls.routines_classes.append(klass)
            return klass

        return decorator

    @classmethod
    async def initialise(cls):
        assert not cls.routines_instances, "Routines already initialised"
        cls.routines_instances = [routine() for routine in cls.routines_classes]
        routines_tasks = []
        for routine in cls.routines_instances:
            async def run_routine(routine):
                while True:
                    await routine.tick()
                    await asyncio.sleep(0.00001)  # TODO get rid of it
            routines_tasks.append(run_routine(routine))

        
        cls.routines_coroutine = asyncio.gather(*routines_tasks)

    # @classmethod
    # async def tick(cls):
    #     while True:
    #         for routine in cls.routines_instances:
    #             await routine.tick()
    #             await asyncio.sleep(0.00001)


