"""
DSPy integration surface. ``Feedback.run`` in ``core.feedback.feedback`` stays stubbed;
call into this module when wiring real optimizers.
"""


def get_dspy():
    """Return the ``dspy`` module if installed, else ``None``."""
    try:
        import dspy

        return dspy
    except ImportError:
        return None


def dspy_available() -> bool:
    return get_dspy() is not None
