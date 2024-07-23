class BaseRoutine:
    async def run(self):
        """Routine main method, expected to be ran in a while true loop"""
        raise NotImplementedError


class RoutinesRegistry:
    routines_classes = []
    routines_instances = []

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
    async def run(cls):
        for routine in cls.routines_instances:
            await routine.run()


