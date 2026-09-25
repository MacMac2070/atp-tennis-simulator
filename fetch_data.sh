#!/usr/bin/env bash
# Downloads the ATP match data this project trains on.
#
# NOTE: the original source, github.com/JeffSackmann/tennis_atp, was taken down
# some time before August 2026 and now returns 404. We use an archival mirror.
# Data is CC BY-NC-SA 4.0, originally compiled by Jeff Sackmann (Tennis Abstract).
# Non-commercial use only, attribution required, share-alike.
set -euo pipefail

DEST="$(cd "$(dirname "$0")" && pwd)/data/tennis_atp"
# Pinned to the mirror commit this project was built and verified on (June 2026).
REF="83733587353df8a41f2fd4f516147d5aa83f5a8d"
MIRROR="https://codeload.github.com/Aneeshers/tennis-sackmann-archive/tar.gz/$REF"
SRC="tennis-sackmann-archive-$REF"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading archival mirror (~138MB)..."
curl -fsSL -o "$TMP/archive.tgz" "$MIRROR"

echo "Extracting ATP singles files..."
tar -xzf "$TMP/archive.tgz" -C "$TMP" "$SRC/atp" "$SRC/LICENSE"

mkdir -p "$DEST"
cp "$TMP/$SRC"/atp/atp_matches_[12]*.csv "$DEST/"
cp "$TMP/$SRC"/atp/atp_players.csv "$DEST/"
cp "$TMP/$SRC"/atp/atp_rankings_*.csv "$DEST/"
cp "$TMP/$SRC"/atp/UPSTREAM_README.md "$DEST/" 2>/dev/null || true
cp "$TMP/$SRC"/LICENSE "$DEST/"

echo "Done. $(ls "$DEST"/atp_matches_[12]*.csv | wc -l | tr -d ' ') season files in $DEST"
