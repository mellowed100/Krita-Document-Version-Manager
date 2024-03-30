from krita import (DockWidgetFactory,
                   DockWidgetFactoryBase)

from .version_manager_gui import VersionManagerGui

doc_widget_factory = DockWidgetFactory(
    "document_version_manager",
    DockWidgetFactoryBase.DockRight,
    VersionManagerGui)

Krita.instance().addDockWidgetFactory(doc_widget_factory)
