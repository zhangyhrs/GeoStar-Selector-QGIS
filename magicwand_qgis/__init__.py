"""
Magic Wand QGIS Plugin
A tool for selecting similar pixels in raster layers using flood fill algorithm
Support multiple feature creation with export to SHP/JSON formats
"""

def classFactory(iface):
    """
    Load MagicWandPlugin class from file magicwand.py
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    try:
        from .magicwand import MagicWandPlugin
        return MagicWandPlugin(iface)
    except ImportError as e:
        # 记录错误但不阻止插件加载
        from qgis.core import QgsMessageLog, Qgis
        QgsMessageLog.logMessage(
            "Error importing Magic Wand Plugin: {}".format(str(e)), 
            "Magic Wand", 
            Qgis.Critical
        )
        raise