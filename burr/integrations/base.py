def require_plugin(import_error: ImportError, libraries: list[str], plugin_name: str):
    raise ImportError(
        f"Missing plugin {plugin_name}! To use the {plugin_name} plugin, you must install the following libraries: {libraries}."
        f"You can install this with burr[{plugin_name}] or pip install {' '.join(libraries)} (replace with your "
        f"package manager of choice)."
    ) from import_error
