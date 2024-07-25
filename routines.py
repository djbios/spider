import asyncio


class BaseRoutine:
    async def tick(self):
        """Routine main method, expected to be ran in a while true loop"""
        raise NotImplementedError


class RoutinesRegistry:
    routines_classes: list[type[BaseRoutine]] = []
    routines_instances: list[BaseRoutine] = []

    @classmethod
    def register(cls):
        def decorator(klass):
            cls.routines_classes.append(klass)
            return klass

        return decorator

    @classmethod
    def initialise(cls):
        cls.routines_instances = [routine() for routine in cls.routines_classes]

    @classmethod
    async def tick(cls):
        while True:
            for routine in cls.routines_instances:
                await routine.tick()
                await asyncio.sleep(0.01)


