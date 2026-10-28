<div align="center">

# Firefox Minimal Compact for Sine

A Sine-compatible distribution of [D3SOX's Firefox Minimal Compact theme](https://github.com/D3SOX/firefox-minimal-compact-css).

![Screenshot](./screenshot.png)
Used theme: [Dark Matched](https://github.com/serverwentdown/matched)

</div>

## Features

- Compact, rounded UI with more Icons
- Shows amount of tabs on the Sidebery icon
- Doesn't show tabs when there is only one tab
- Use Sidebery Icon or set a hotkey via addon settings for `Open/Close sidebar panel` to switch between horizontal and vertical tabs
- Menu highlights matching to my KDE Plasma theme
- Bouncing indicator line while page is loading
- Move menu icon to the left
- Resizable Sidebar with minimal splitter that only shows on hover
- Use `SF Pro Display` font if installed

## Installation

### Sine (Firefox)

1. Install [Sine](https://github.com/CosmoCreeper/Sine#installation) for your Firefox installation and restart Firefox.
2. Open Firefox Settings and select **Sine**. In its custom repository installer, enter
   `millerjryan/firefox-minimal-compact-sine/tree/master` and install the mod.
   The explicit branch is required because this repository uses `master`, not `main`.
   For an unpublished fork or development branch, use `OWNER/REPO/tree/BRANCH` instead.
3. Complete the **Shared Firefox and Sidebery setup** below, then restart Firefox.

Sine manages both browser UI and content styles. The committed `sine/` directory
includes the required submodule CSS and icons, so no Git clone or manual CSS imports
are needed. Sidebery settings and Firefox preferences are still configured manually;
the mod does not overwrite your preferences.

If migrating from the manual installation, back up your profile's existing
`chrome/userChrome.css` and `chrome/userContent.css`, then remove this theme's old
imports/rules from those files so the theme is not loaded twice. Keep unrelated
customizations and Sine's own files. Disable other full browser themes that conflict
with this mod. You can disable or remove this mod from Sine.

### Manual installation

1. Complete the **Shared Firefox and Sidebery setup** below.
2. Go to `about:support` and click on `Open Directory` under `Profile Directory`.
3. In that directory, run `git clone --recursive https://github.com/millerjryan/firefox-minimal-compact-sine.git chrome`.
   Back up any existing `chrome` directory first; this command expects it not to exist.
4. Restart Firefox.

### Shared Firefox and Sidebery setup

1. Open Firefox and go to `about:config`
2. Set `toolkit.legacyUserProfileCustomizations.stylesheets` and `svg.context-properties.content.enabled` to `true`
3. Set `browser.compactmode.show` to `true`
4. Install [Sidebery](https://addons.mozilla.org/firefox/addon/sidebery/)
5. If you have used Sidebery before, you should use the minimal config otherwise use the full config

   **Minimal Config**
   - In Sidebery settings, enable `Add preface to the browser window's title if Sidebery sidebar is active`
   - Set the preface value to the invisible character between these markers: **`​`**
   - In the Styles editor, paste the contents of [sidebery.css](./sidebery.css)

   **Full Config**
   - In Sidebery settings, click on Help
   - Select Import addon data
   - Import the file [sidebery-data.json](./sidebery-data.json)
6. Open the menu then click on `More tools` -> `Customize toolbar...`. On the bottom left set the `Density` to `Compact`
7. Then depending on your preference put in the following items in the top bar
    (Links are addons, you have to install and pin them first, the theme replaces the icons of these addons)
    - [Close Tab Button](https://addons.mozilla.org/firefox/addon/close-the-tab-button/)
    - [Sidebery](https://addons.mozilla.org/firefox/addon/sidebery/)
    - [Simple New Tab Button](https://addons.mozilla.org/firefox/addon/simple-new-tab-button/)
    - Back, Forward, Reload
    - [Reload Skip Cache Button](https://addons.mozilla.org/firefox/addon/reload-skip-cache-button/)
    - Downloads (right click and uncheck `Hide Button When Empty` if you want that)
    - URL Bar, Addon-specific Icons, Extensions icon

The theme is designed for Firefox's horizontal tabs with Sidebery providing vertical
tabs. Turn off Firefox's built-in vertical tabs when using this setup. Window-control
styling was originally designed for Linux; native titlebar controls on Windows and
macOS may require additional customization.

## Maintaining the Sine package

Edit the original `userChrome.css`, `userContent.css`, `custom/`, and `icons/`
files, not their generated copies in `sine/`. After changing those files or updating
submodules, run the following from the repository root with Python 3.9 or newer:

```shell
git submodule update --init --recursive
python scripts/build-sine.py
python -m unittest discover -s tests
python scripts/build-sine.py --check
```

Commit the regenerated `sine/` files alongside the source changes. The packager
copies only active CSS dependencies and referenced local assets, retaining separate
stylesheets so namespace rules and import order behave like the manual installation.
Upstream license texts and source comments are included. CI rejects stale packages,
and the automated submodule updater rebuilds the package before committing.

`theme.json` uses relative Sine entry points and a stable mod ID. Its homepage and
update timestamp are intentionally inferred by Sine from the installation repository,
so forks and branch installs are not redirected to upstream.

## Optional: Smooth Scrolling

I also like to configure smooth scrolling similar to Zen.
To do that, go to `about:config` and set

- `general.smoothScroll.msdPhysics.continousMotionMaxDeltaMS` to `12`
- `general.smoothScroll.msdPhysics.enabled` to `true`
- `general.smoothScroll.msdPhysics.motionBeginSpringConstant` to `600`
- `general.smoothScroll.msdPhysics.regularSpringConstant` to `650`
- `general.smoothScroll.msdPhysics.slowdownMinDeltaMS` to `25`
- `general.smoothScroll.msdPhysics.slowdownSpringConstant` to `250`

## Credits

- Partially based on [ArcWTF](https://github.com/KiKaraage/ArcWTF)
- Uses CSS from [firefox-csshacks](https://github.com/MrOtherGuy/firefox-csshacks) and [CustomCSSForFx](https://github.com/Aris-t2/CustomCSSForFx)
