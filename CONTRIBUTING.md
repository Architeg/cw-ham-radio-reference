# Help improve the guide

Questions, corrections, clearer explanations, and practical examples are welcome. You don’t need Git or code: [open an issue](https://github.com/Architeg/cw-ham-radio-reference/issues), mention the edition and page, and describe the change in plain English. Include a source when possible; distinguish standardized procedure from local or club custom.

For a small pull request, edit `source/guide.md`. The checked-in `source/guide.html` is the PDF build input. `source/reference-data.json` is a companion reference, not an automatic manuscript generator. Keep placeholder call signs and identify third-party material and its terms. Original content contributions use CC BY 4.0; build code uses MIT. Font notices stay with the fonts.

## Rebuild

With Python 3, create a virtual environment and install `tools/requirements.txt`. After manuscript edits, regenerate HTML with Pandoc; `markdown-smart` keeps Morse hyphens literal:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r tools/requirements.txt
pandoc source/guide.md --from=markdown-smart --to=html5 --standalone -o source/guide.html
python3 tools/build_pdf.py
```

Skip Pandoc when rebuilding the checked-in HTML without manuscript changes. The build writes the current PDF to `book/` and temporary layout data to ignored `dist/`. Review changed pages, contents, links, Morse patterns, and the one-page desk card at A5 size.

## Versions and releases

Use patch versions such as **v1.0.1** for corrections, typos, broken links, or layout fixes; minor versions such as **v1.1.0** for new reference entries, examples, or useful sections; and major versions such as **v2.0.0** for a substantially revised edition or major reorganization.

Set `VERSION` in `tools/build_pdf.py` before rebuilding. Keep it consistent with the PDF edition notice, README, changelog, release tag, and uploaded asset. Add a dated, reader-facing entry at the top of `CHANGELOG.md`, using only relevant Added, Changed, or Fixed headings and describing changes actually made.

Keep only the current PDF in `book/`; older editions remain in GitHub Releases and Git history. Publish the matching versioned PDF asset. Keep the primary download link at `https://github.com/Architeg/cw-ham-radio-reference/releases/latest`, then update and verify the README’s direct asset and online-reading links. A changing filename cannot be assumed to work through `/releases/latest/download/`.
