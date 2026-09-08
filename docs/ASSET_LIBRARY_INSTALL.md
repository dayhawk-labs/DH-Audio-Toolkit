# DH Audio Toolkit {{VERSION}}

## Install the asset library

You do not need to run Python or install an add-on. Use the downloaded ZIP as
a ready-to-use Blender Asset Library.

1. Download `DH-Audio-Toolkit-{{VERSION}}.zip` from the GitHub Release page.
2. Extract the ZIP. Keep the folder named `DH Audio Toolkit {{VERSION}}` together.
3. Open Blender 5.2 or newer.
4. Go to **Edit → Preferences → File Paths**.
5. Find **Asset Libraries** and click the **+** button.
6. Select the extracted `DH Audio Toolkit {{VERSION}}` folder itself. Do not select
   the ZIP file or a parent folder.
7. Click **Save Preferences**.
8. In the 3D Viewport, open the **Asset Shelf** or press **Shift+A** and choose
   the **Asset Browser**.
9. Choose **DH Audio Toolkit {{VERSION}}** from the asset-library selector.
10. Open the **DH Audio** catalog, choose a node group, and drag it into your
    Geometry Nodes editor.

The folder should contain these files side by side:

```text
DH Audio Toolkit {{VERSION}}/
├── DH Audio Toolkit {{VERSION}}.blend
├── blender_assets.cats.txt
└── README.md
```

Keep the folder in a permanent location. If you move it later, update the
Asset Library path in Blender Preferences. The `.blend` file is the actual
asset library; `blender_assets.cats.txt` preserves the catalog organization.

## Troubleshooting

- **The library does not appear:** confirm that Blender is pointed at the
  extracted version folder, not at the ZIP or its parent directory.
- **The catalog is empty or assets are uncategorized:** keep the `.blend` and
  `blender_assets.cats.txt` in the same asset-library folder, then restart
  Blender or refresh the Asset Browser.
- **You only see an older version:** remove the old library entry or select
  the new version in the Asset Browser library selector.

For recipes and examples, see the project’s `docs/RECIPES.md`.
