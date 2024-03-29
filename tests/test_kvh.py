from kvh.krita_history import KritaVersionHistory


kvh = KritaVersionHistory('test.kra')
kvh.init(force=True)
kvh.add_checkpoint()
kvh.add_checkpoint()
