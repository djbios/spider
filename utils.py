from logging import log


# Define the rainbow colors
rainbow_colors = [
    (255, 0, 0),  # Red
    (255, 127, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (75, 0, 130),  # Indigo    (148, 0, 211)   # Violet
]


# Function to interpolate between two colors
def interpolate_color(color1, color2, factor):
    return (
        int(color1[0] + (color2[0] - color1[0]) * factor),
        int(color1[1] + (color2[1] - color1[1]) * factor),
        int(color1[2] + (color2[2] - color1[2]) * factor),
    )


async def run_callable_async_or_not(callable, *args, **kwargs):
    """Run a callable that may be async or not."""
    try:
        await callable(*args, **kwargs)
    except AttributeError as e:  # The only way I found to identify its not async
        if "__await__" in str(e):
            try:
                callable(*args, **kwargs)
            except Exception as e:
                log(f"❌ Command failed: {e}")
        else:
            log(f"❌ Command failed: {e}")
