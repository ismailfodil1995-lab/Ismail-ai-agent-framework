# ==========================================
# Plugin Registry
# ==========================================

PLUGINS = {}


# ==========================================
# Register Plugin
# ==========================================

def register(name, function):

    PLUGINS[name] = function


# ==========================================
# Execute Plugin
# ==========================================

def execute(name, *args):

    if name not in PLUGINS:

        return None

    return PLUGINS[name](*args)


# ==========================================
# Check Plugin
# ==========================================

def exists(name):

    return name in PLUGINS


# ==========================================
# List Plugins
# ==========================================

def all_plugins():

    return list(
        PLUGINS.keys()
    )