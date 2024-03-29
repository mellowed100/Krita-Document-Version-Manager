from krita import (DockWidgetFactory,
                   DockWidgetFactoryBase)
from .version_manager import VersionManagerDocker


doc_widget_factory = DockWidgetFactory(
    "document_version_manager",
    DockWidgetFactoryBase.DockRight,
    VersionManagerDocker)

Krita.instance().addDockWidgetFactory(doc_widget_factory)
