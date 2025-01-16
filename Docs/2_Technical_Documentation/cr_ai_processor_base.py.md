### Filepath/filename: backend/src/python/congressgov/bill_summary/ai_processor_base.py
#### Issues:
1. The use of an abstract base class (ABC) is appropriate for defining a common interface for AI processors.
2. The abstract methods are clearly defined, specifying expected input and output types.
3. The docstrings are clear; consider expanding them to include information about potential exceptions.
4. Type hinting is well-implemented, providing clarity on expected input and output types for methods.
5. The design allows for easy extensibility by adding new AI processors that adhere to the defined interface.
