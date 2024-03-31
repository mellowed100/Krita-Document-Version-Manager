from krita import (DockWidgetFactory,
                   DockWidgetFactoryBase)

# from .version_manager_gui import VersionManagerGui
from .qt_docker_widget import QtDocker

doc_widget_factory = DockWidgetFactory(
    "document_version_manager",
    DockWidgetFactoryBase.DockRight,
    QtDocker)

Krita.instance().addDockWidgetFactory(doc_widget_factory)
