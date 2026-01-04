# Ebook Generation Guide

This guide explains how to generate ebooks (EPUB, MOBI) from the
"Le Club des Cinq et le Phare Abandonne" project.

## Prerequisites

### Required Software

1. **Pandoc** (required)
   - Download: https://pandoc.org/installing.html
   - Recommended version: 3.0 or higher
   - Verify installation: `pandoc --version`

2. **PowerShell** (included with Windows)
   - Version 5.1 or higher
   - Verify: `$PSVersionTable.PSVersion`

3. **powershell-yaml module** (recommended)
   ```powershell
   Install-Module powershell-yaml -Scope CurrentUser
   ```

4. **For MOBI/AZW3** (optional)
   - Calibre: https://calibre-ebook.com/
   - Provides `ebook-convert` for EPUB -> MOBI/AZW3 conversion

---

## File Structure

```
ebook/
├── config/
│   └── book.yaml          <- Main configuration
├── assets/
│   ├── images/
│   │   ├── cover.jpg      <- Cover image
│   │   └── headers/       <- Chapter header images
│   └── fonts/             <- Custom fonts (optional)
├── templates/
│   └── epub.css           <- EPUB styles
├── build/                 <- Generated files (gitignored)
└── build-ebook.ps1        <- Build script
```

---

## Quick Start

### Generate an EPUB

```powershell
cd "d:\code-workspace\Claude Book\ebook"
.\build-ebook.ps1
```

### Verbose mode (for debugging)

```powershell
.\build-ebook.ps1 -Verbose
```

### Clean and rebuild

```powershell
.\build-ebook.ps1 -Clean
```

### Dry run mode (without generating)

```powershell
.\build-ebook.ps1 -DryRun
```

---

## Cover Image Configuration

### Recommended Specifications

| Property | Recommended Value |
|----------|-------------------|
| Dimensions | 1600 x 2400 pixels |
| Ratio | 2:3 (portrait) |
| Format | JPEG or PNG |
| Max size | 5 MB |
| Resolution | 300 DPI (for print) |

### Steps

1. Create or obtain a cover image
2. Resize to recommended dimensions
3. Save to `ebook/assets/images/cover.jpg`
4. Verify that `book.yaml` contains:
   ```yaml
   cover:
     enabled: true
     image: "assets/images/cover.jpg"
   ```

### Recommended Tools

- **GIMP** (free): https://www.gimp.org/
- **Canva** (online): https://www.canva.com/
- **Photoshop** (paid)

### Design Tips

- Text readable at thumbnail size (title visible at 100px wide)
- High contrast between text and background
- Avoid fine details that disappear at small sizes
- Test on different devices (Kindle, phone, tablet)

---

## Chapter Header Images

### Activation

In `book.yaml`:

```yaml
chapters:
  header_images:
    enabled: true
    default: ""  # Default image for all chapters
    mapping:
      chapitre-01: "assets/images/headers/chapitre-01.jpg"
      chapitre-12: "assets/images/headers/climax.jpg"
```

### Specifications

| Property | Recommended Value |
|----------|-------------------|
| Dimensions | 800 x 300 pixels |
| Ratio | Wide (landscape) |
| Format | JPEG |
| Size | < 500 KB per image |

### File Structure

```
ebook/assets/images/headers/
├── chapitre-01.jpg
├── chapitre-02.jpg
├── ...
└── chapitre-18.jpg
```

### Tips

- Use evocative images matching chapter content
- Maintain visual consistency (same style, palette)
- Decorative images, not informative (accessibility)
- Test on e-ink readers (contrast is important)

---

## CSS Customization

### Stylesheet File

The `templates/epub.css` file controls the book's appearance.

### Common Modifications

#### Change the main font

```css
body {
    font-family: "Palatino Linotype", Palatino, Georgia, serif;
}
```

#### Adjust line height

```css
body {
    line-height: 1.8;  /* More space */
}
```

#### Chapter title style

```css
h1 {
    font-size: 2em;
    font-style: italic;
    border-bottom: 1px solid #333;
    padding-bottom: 0.5em;
}
```

#### Customize scene separators

```css
hr::before {
    content: "~ ~ ~";  /* Instead of * * * */
}
```

### Testing Styles

1. Generate the EPUB
2. Open in Calibre (F7 to view HTML)
3. Adjust the CSS
4. Regenerate and retest

---

## MOBI Generation (Kindle)

### Prerequisites

- Calibre installed
- EPUB generated first

### Process

1. The script first generates the EPUB
2. Then converts to MOBI via `ebook-convert`

### Activation

```yaml
output:
  formats:
    mobi:
      enabled: true
```

### Limitations

- MOBI is an obsolete format (Amazon now recommends KF8/AZW3)
- Some CSS styles are not supported
- Large images may be compressed

---

## Advanced Configuration

### Modify Metadata

In `book.yaml`, section `metadata`:

```yaml
metadata:
  title: "Le Club des Cinq et le Phare Abandonne"
  subtitle: "Une aventure en Bretagne"
  author: "Your Name"
  language: "fr-FR"
  publisher: "My Publishing House"
  date: "2024"
  rights: "All rights reserved"
  isbn: "978-X-XXXX-XXXX-X"
  description: |
    A description of your book for catalogs
    and e-readers.
```

### Change Output Filename

```yaml
output:
  filename: "my-book"  # Will produce my-book.epub
```

### Add a Dedication

```yaml
front_matter:
  include:
    dedication: true
  dedication_text: "To all adventure lovers"
```

### Add an Epigraph

```yaml
front_matter:
  include:
    epigraph: true
  epigraph:
    text: "Adventure is around the corner."
    attribution: "Unknown Author"
```

---

## Troubleshooting

### Error: "Pandoc is not installed"

```
Solution: Install Pandoc and restart PowerShell
Link: https://pandoc.org/installing.html
```

### Error: "powershell-yaml module not found"

```powershell
Install-Module powershell-yaml -Scope CurrentUser
```

The script will still work with a default configuration.

### Error: "No chapter files found"

```
Check:
1. The path in book.yaml (chapters.source_dir)
2. The file pattern (chapters.pattern)
3. That files exist in story/chapters/
```

### Error: "Cover image not found"

```
Check:
1. The file exists in ebook/assets/images/
2. The path in book.yaml is correct
3. The extension is correct (.jpg vs .jpeg)
```

The EPUB will be generated without a cover if the image is missing.

### EPUB doesn't display correctly

```
1. Test in Calibre (more tolerant)
2. Check CSS for syntax errors
```

### Script blocked by execution policy

```powershell
# Run as administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run the script with:
powershell -ExecutionPolicy Bypass -File build-ebook.ps1
```

---

## Best Practices

### Before Final Generation

- [ ] Proofread all chapters for typos
- [ ] Verify chapter title consistency
- [ ] Test on multiple devices/applications

### Important Metadata

- [ ] Exact title with correct spelling
- [ ] Correct author name
- [ ] Language defined (fr-FR)
- [ ] Description for catalogs

### Images

- [ ] High-quality cover
- [ ] All images optimized (size < 500 KB)
- [ ] Alt text for accessibility

---

## Additional Resources

- **Pandoc Documentation**: https://pandoc.org/MANUAL.html
- **EPUB 3 Specification**: https://www.w3.org/publishing/epub3/
- **Kindle Publishing Guidelines**: https://kdp.amazon.com/en_US/help/topic/G200645400
- **Calibre**: https://calibre-ebook.com/
