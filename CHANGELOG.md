# Changelog

## 2.5.0

**✦ orient** — a new camera-group button. It rigidly rotates the current layout to
the angle whose bounding box best fills the viewport, so links don't fly off-screen and
the graph sits in-frame. Rotation is an isometry: `ring` stays `ring`, every layout's
non-crossings and intrinsic structure are preserved; only the orientation changes. The
button reports the real fill it achieved (base → best) — no cosmetic claim.

**Example gallery** — five runnable example vaults (campaign, homelab, italian, reading,
trip) with screenshots, so you can see the detectors and layouts on real-shaped notes
before pointing the tool at your own vault.

Also folds in the prior refine pass: `--data` accepts a ready-made graph JSON, the
session detector handles vaults living in a repo subdirectory (`--relative`), localized
preset toasts, a template/generator version handshake, and assorted layout fixes.
