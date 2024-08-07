def require_plugin(import_error: ImportError, plugin_name: str):
    raise ImportError(
        f"Missing plugin {plugin_name}! To use the {plugin_name} plugin, you must install the 'extras' target [{plugin_name}] with burr[{plugin_name}] "
        f"(replace with your package manager of choice). Note that, if you're using poetry, you cannot install burr with burr[start], so "
        f"you'll have to install the components individually. See https://burr.dagworks.io/getting_started/install/ "
        f"for more details."
    ) from import_error
