# -*- coding: utf-8 -*-


# put in function to import at runtime, avoiding db config/creation on import
def lazy_load_dev_server():
    from .serve import _dev_server
    return _dev_server
