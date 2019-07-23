# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/fog/Documents/GitHub/YNAB_Sync-Norge'],
             binaries=[],
             datas=[('gui/content/*', 'gui/content/'), ('gui/icons/*', 'gui/icons/')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='YNAB_Sync-Norge',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='./gui/icons/YNAB-icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='YNAB_Sync-Norge')
app = BUNDLE(coll,
             name='YNAB_Sync-Norge.app',
             icon='./gui/icons/YNAB-icon.icns',
             bundle_identifier=None,
             info_plist={
                     'NSHighResolutionCapable': 'True'
                     },
             )
