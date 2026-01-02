<#
.SYNOPSIS
    Generates an ebook (EPUB/MOBI/AZW3) from markdown chapters.

.DESCRIPTION
    This script reads the book.yaml configuration, assembles all chapters
    with front matter pages, and generates ebooks via Pandoc.

.PARAMETER Config
    Path to the configuration file. Default: config/book.yaml

.PARAMETER Format
    Output format(s): epub, mobi, azw3, all. Default: epub

.PARAMETER Clean
    Cleans the build folder before generation.

.PARAMETER DryRun
    Displays commands without executing them.

.EXAMPLE
    .\build-ebook.ps1
    Generates an EPUB with default configuration.

.EXAMPLE
    .\build-ebook.ps1 -Format all
    Generates all enabled formats.

.EXAMPLE
    .\build-ebook.ps1 -Format azw3
    Generates an AZW3 for Kindle.
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Config = "config\book.yaml",

    [Parameter(Position = 1)]
    [ValidateSet("epub", "mobi", "azw3", "all")]
    [string]$Format = "epub",

    [switch]$Clean,

    [switch]$DryRun
)

# =============================================================================
# CONFIGURATION
# =============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n[*] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-ToolExists {
    param([string]$Tool)
    $null -ne (Get-Command $Tool -ErrorAction SilentlyContinue)
}

function Get-ConfigValue {
    param(
        [hashtable]$Config,
        [string]$Key,
        [object]$Default = $null
    )

    $keys = $Key -split '\.'
    $value = $Config

    foreach ($k in $keys) {
        if ($value -is [hashtable] -and $value.ContainsKey($k)) {
            $value = $value[$k]
        } elseif ($value -is [System.Collections.Specialized.OrderedDictionary] -and $value.Contains($k)) {
            $value = $value[$k]
        } else {
            return $Default
        }
    }

    return $value
}

function Read-YamlConfig {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Configuration file not found: $Path"
    }

    # Check if powershell-yaml module is available
    if (-not (Get-Module -ListAvailable -Name powershell-yaml)) {
        Write-Warn "The powershell-yaml module is not installed."
        Write-Host "  Install it with: Install-Module powershell-yaml -Scope CurrentUser"
        Write-Host "  Using default configuration..."

        # Default configuration
        return @{
            metadata = @{
                title = "Le Club des Cinq et le Phare Abandonne"
                author = "[Author]"
                language = "fr-FR"
                date = (Get-Date).Year.ToString()
                rights = "All rights reserved"
                description = ""
            }
            cover = @{ enabled = $true; image = "assets/images/cover.png" }
            chapters = @{
                source_dir = "..\story\chapters"
                pattern = "chapitre-*.md"
                header_images = @{ enabled = $false }
            }
            front_matter = @{
                enabled = $true
                include = @{
                    title_page = $true
                    copyright_page = $true
                    table_of_contents = $true
                }
            }
            back_matter = @{ enabled = $false }
            output = @{
                directory = "build"
                filename = "le-club-des-cinq-phare"
                formats = @{
                    epub = @{ enabled = $true; stylesheet = "templates/epub.css"; version = 3 }
                    mobi = @{ enabled = $false }
                    azw3 = @{ enabled = $false }
                }
            }
            pandoc = @{ smart = $true }
            build = @{ clean_before = $true; keep_intermediate = $false }
        }
    }

    Import-Module powershell-yaml
    $content = Get-Content $Path -Raw -Encoding UTF8
    return $content | ConvertFrom-Yaml
}

function Get-ChapterFiles {
    param(
        [string]$SourceDir,
        [string]$Pattern
    )

    $fullPath = Join-Path $ScriptDir $SourceDir

    if (-not (Test-Path $fullPath)) {
        throw "Chapters folder not found: $fullPath"
    }

    $files = Get-ChildItem -Path $fullPath -Filter $Pattern |
             Sort-Object { [int]($_.BaseName -replace '\D', '') }

    return $files
}

function New-FrontMatter {
    param([hashtable]$Config)

    $metadata = Get-ConfigValue $Config "metadata"
    $frontConfig = Get-ConfigValue $Config "front_matter"

    $content = @()

    # Title page
    if (Get-ConfigValue $frontConfig "include.title_page" $true) {
        $content += ""
        $content += "::: {.title-page}"
        $content += ""
        $content += "# $($metadata.title)"
        if ($metadata.subtitle) {
            $content += ""
            $content += "## $($metadata.subtitle)"
        }
        $content += ""
        $content += "**$($metadata.author)**"
        $content += ""
        $content += ":::"
        $content += ""
        $content += "\pagebreak"
        $content += ""
    }

    # Copyright page
    if (Get-ConfigValue $frontConfig "include.copyright_page" $true) {
        $content += "::: {.copyright-page}"
        $content += ""
        $content += "$($metadata.title)"
        $content += ""
        $content += "Copyright (C) $($metadata.date) $($metadata.author)"
        $content += ""
        $content += "$($metadata.rights)"
        $content += ""
        if ($metadata.publisher) {
            $content += "Publisher: $($metadata.publisher)"
            $content += ""
        }
        if ($metadata.isbn) {
            $content += "ISBN: $($metadata.isbn)"
            $content += ""
        }
        $content += ":::"
        $content += ""
        $content += "\pagebreak"
        $content += ""
    }

    # Dedication
    if (Get-ConfigValue $frontConfig "include.dedication" $false) {
        $dedication = Get-ConfigValue $frontConfig "dedication_text"
        if ($dedication) {
            $content += "::: {.dedication}"
            $content += ""
            $content += "*$dedication*"
            $content += ""
            $content += ":::"
            $content += ""
            $content += "\pagebreak"
            $content += ""
        }
    }

    # Epigraph
    if (Get-ConfigValue $frontConfig "include.epigraph" $false) {
        $epigraph = Get-ConfigValue $frontConfig "epigraph"
        if ($epigraph -and $epigraph.text) {
            $content += "::: {.epigraph}"
            $content += ""
            $content += "*$($epigraph.text)*"
            $content += ""
            if ($epigraph.attribution) {
                $content += "--- $($epigraph.attribution)"
            }
            $content += ""
            $content += ":::"
            $content += ""
            $content += "\pagebreak"
            $content += ""
        }
    }

    return $content -join "`n"
}

function Build-AssembledDocument {
    param(
        [hashtable]$Config,
        [string]$OutputPath
    )

    Write-Step "Assembling document..."

    $chapters = Get-ConfigValue $Config "chapters"
    $headerImages = Get-ConfigValue $chapters "header_images"

    $document = @()

    # YAML metadata block for Pandoc
    $metadata = Get-ConfigValue $Config "metadata"
    $document += "---"
    $document += "title: `"$($metadata.title)`""
    $document += "author: `"$($metadata.author)`""
    $document += "lang: $($metadata.language)"
    if ($metadata.date) {
        $document += "date: `"$($metadata.date)`""
    }
    if ($metadata.publisher) {
        $document += "publisher: `"$($metadata.publisher)`""
    }
    if ($metadata.rights) {
        $document += "rights: `"$($metadata.rights)`""
    }
    if ($metadata.description) {
        $desc = ($metadata.description -replace "`n", " ").Trim()
        $document += "description: `"$desc`""
    }
    $document += "---"
    $document += ""

    # Front matter pages
    if (Get-ConfigValue $Config "front_matter.enabled" $true) {
        $frontMatter = New-FrontMatter $Config
        if ($frontMatter) {
            $document += $frontMatter
        }
    }

    # Chapters
    $sourceDir = Get-ConfigValue $chapters "source_dir" "..\story\chapters"
    $pattern = Get-ConfigValue $chapters "pattern" "chapitre-*.md"

    $chapterFiles = Get-ChapterFiles -SourceDir $sourceDir -Pattern $pattern

    if ($chapterFiles.Count -eq 0) {
        throw "No chapter files found with pattern: $pattern"
    }

    Write-Host "  $($chapterFiles.Count) chapter(s) found"

    foreach ($file in $chapterFiles) {
        $chapterName = $file.BaseName
        $chapterContent = Get-Content $file.FullName -Raw -Encoding UTF8

        # Add header image if configured
        if (Get-ConfigValue $headerImages "enabled" $false) {
            $imagePath = Get-ConfigValue $headerImages "mapping.$chapterName"
            if (-not $imagePath) {
                $imagePath = Get-ConfigValue $headerImages "default"
            }
            if ($imagePath -and (Test-Path (Join-Path $ScriptDir $imagePath))) {
                $chapterContent = "![$chapterName]($imagePath)`n`n" + $chapterContent
            } elseif ($imagePath) {
                Write-Warn "Header image not found for $chapterName`: $imagePath"
            }
        }

        $document += $chapterContent
        $document += ""

        Write-Verbose "  Added: $chapterName"
    }

    # Write assembled document
    $document -join "`n" | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Success "Document assembled: $OutputPath"

    return $OutputPath
}

function Build-Epub {
    param(
        [hashtable]$Config,
        [string]$SourceFile,
        [string]$OutputFile
    )

    Write-Step "Generating EPUB..."

    $epubConfig = Get-ConfigValue $Config "output.formats.epub"
    $coverConfig = Get-ConfigValue $Config "cover"
    $pandocConfig = Get-ConfigValue $Config "pandoc"

    $args = @(
        $SourceFile,
        "-o", $OutputFile,
        "--toc",
        "--toc-depth", (Get-ConfigValue $epubConfig "options.toc_depth" 2)
    )

    # EPUB version
    $epubVersion = Get-ConfigValue $epubConfig "version" 3
    if ($epubVersion -eq 2) {
        $args += "--epub-version=2"
    }

    # Cover image
    if (Get-ConfigValue $coverConfig "enabled" $true) {
        $coverImage = Get-ConfigValue $coverConfig "image"
        $coverPath = Join-Path $ScriptDir $coverImage
        if ($coverImage -and (Test-Path $coverPath)) {
            $args += "--epub-cover-image=$coverPath"
            Write-Host "  Cover: $coverImage"
        } else {
            Write-Warn "Cover image not found: $coverImage"
            Write-Host "  EPUB will be generated without cover."
        }
    }

    # Stylesheet
    $stylesheet = Get-ConfigValue $epubConfig "stylesheet"
    $stylePath = Join-Path $ScriptDir $stylesheet
    if ($stylesheet -and (Test-Path $stylePath)) {
        $args += "--css=$stylePath"
    }

    # Smart typography (quotes, dashes)
    if (Get-ConfigValue $pandocConfig "smart" $true) {
        # Pandoc 2.0+ uses +smart in extensions
        # For earlier versions, --smart was used
    }

    # Split level
    $splitLevel = Get-ConfigValue $epubConfig "options.split_level" 1
    $args += "--split-level=$splitLevel"

    # Execute Pandoc
    $argString = $args -join ' '
    Write-Verbose "Command: pandoc $argString"

    if (-not $DryRun) {
        & pandoc $args 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Pandoc failed with code $LASTEXITCODE"
        }

        Write-Success "EPUB created: $OutputFile"
        $size = [math]::Round((Get-Item $OutputFile).Length / 1KB, 2)
        Write-Host "  Size: $size KB"
    } else {
        Write-Host "  [DRY RUN] pandoc $argString"
    }
}

function Build-Mobi {
    param(
        [string]$EpubFile,
        [string]$OutputFile
    )

    Write-Step "Generating MOBI..."

    if (-not (Test-ToolExists "ebook-convert")) {
        Write-Warn "ebook-convert (Calibre) is not installed. MOBI generation skipped."
        Write-Host "  Install Calibre: https://calibre-ebook.com/"
        return
    }

    if (-not (Test-Path $EpubFile)) {
        Write-Warn "EPUB file not found. Generate EPUB first."
        return
    }

    $args = @($EpubFile, $OutputFile)
    $argString = $args -join ' '

    Write-Verbose "Command: ebook-convert $argString"

    if (-not $DryRun) {
        & ebook-convert $args 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "ebook-convert failed with code $LASTEXITCODE"
        }

        Write-Success "MOBI created: $OutputFile"
        $size = [math]::Round((Get-Item $OutputFile).Length / 1KB, 2)
        Write-Host "  Size: $size KB"
    } else {
        Write-Host "  [DRY RUN] ebook-convert $argString"
    }
}

function Build-Azw3 {
    param(
        [string]$EpubFile,
        [string]$OutputFile
    )

    Write-Step "Generating AZW3 (Kindle)..."

    if (-not (Test-ToolExists "ebook-convert")) {
        Write-Warn "ebook-convert (Calibre) is not installed. AZW3 generation skipped."
        Write-Host "  Install Calibre: https://calibre-ebook.com/"
        return
    }

    if (-not (Test-Path $EpubFile)) {
        Write-Warn "EPUB file not found. Generate EPUB first."
        return
    }

    $args = @($EpubFile, $OutputFile)
    $argString = $args -join ' '

    Write-Verbose "Command: ebook-convert $argString"

    if (-not $DryRun) {
        & ebook-convert $args 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "ebook-convert failed with code $LASTEXITCODE"
        }

        Write-Success "AZW3 created: $OutputFile"
        $size = [math]::Round((Get-Item $OutputFile).Length / 1KB, 2)
        Write-Host "  Size: $size KB"
    } else {
        Write-Host "  [DRY RUN] ebook-convert $argString"
    }
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

try {
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "   Ebook Generator - Claude Book" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta

    # Check required tools
    Write-Step "Checking prerequisites..."

    if (-not (Test-ToolExists "pandoc")) {
        throw "Pandoc is not installed. Download it: https://pandoc.org/installing.html"
    }

    $pandocVersion = & pandoc --version | Select-Object -First 1
    Write-Host "  $pandocVersion"

    # Load configuration
    Write-Step "Loading configuration..."

    $configPath = Join-Path $ScriptDir $Config
    $cfg = Read-YamlConfig -Path $configPath

    $title = Get-ConfigValue $cfg "metadata.title" "Untitled"
    $author = Get-ConfigValue $cfg "metadata.author" "[Author]"
    Write-Host "  Title: $title"
    Write-Host "  Author: $author"

    # Prepare build folder
    $buildDir = Join-Path $ScriptDir (Get-ConfigValue $cfg "output.directory" "build")

    if ($Clean -or (Get-ConfigValue $cfg "build.clean_before" $true)) {
        if (Test-Path $buildDir) {
            Write-Host "  Cleaning build folder..."
            Remove-Item -Path $buildDir -Recurse -Force
        }
    }

    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    # Assemble document
    $baseFilename = Get-ConfigValue $cfg "output.filename" "book"
    $assembledFile = Join-Path $buildDir "assembled.md"

    Build-AssembledDocument -Config $cfg -OutputPath $assembledFile

    # Generate requested formats
    $formats = @()
    if ($Format -eq "all") {
        if (Get-ConfigValue $cfg "output.formats.epub.enabled" $true) { $formats += "epub" }
        if (Get-ConfigValue $cfg "output.formats.mobi.enabled" $false) { $formats += "mobi" }
        if (Get-ConfigValue $cfg "output.formats.azw3.enabled" $false) { $formats += "azw3" }
    } else {
        $formats = @($Format)
    }

    if ($formats.Count -eq 0) {
        Write-Warn "No format enabled in configuration."
        $formats = @("epub")
    }

    $epubFile = $null

    foreach ($fmt in $formats) {
        switch ($fmt) {
            "epub" {
                $outputFile = Join-Path $buildDir "$baseFilename.epub"
                Build-Epub -Config $cfg -SourceFile $assembledFile -OutputFile $outputFile
                $epubFile = $outputFile
            }
            "mobi" {
                if (-not $epubFile) {
                    $epubFile = Join-Path $buildDir "$baseFilename.epub"
                    if (-not (Test-Path $epubFile)) {
                        Write-Warn "EPUB required for MOBI conversion. Generating EPUB..."
                        Build-Epub -Config $cfg -SourceFile $assembledFile -OutputFile $epubFile
                    }
                }
                $outputFile = Join-Path $buildDir "$baseFilename.mobi"
                Build-Mobi -EpubFile $epubFile -OutputFile $outputFile
            }
            "azw3" {
                if (-not $epubFile) {
                    $epubFile = Join-Path $buildDir "$baseFilename.epub"
                    if (-not (Test-Path $epubFile)) {
                        Write-Warn "EPUB required for AZW3 conversion. Generating EPUB..."
                        Build-Epub -Config $cfg -SourceFile $assembledFile -OutputFile $epubFile
                    }
                }
                $outputFile = Join-Path $buildDir "$baseFilename.azw3"
                Build-Azw3 -EpubFile $epubFile -OutputFile $outputFile
            }
        }
    }

    # Clean intermediate files
    if (-not (Get-ConfigValue $cfg "build.keep_intermediate" $false)) {
        if (Test-Path $assembledFile) {
            Remove-Item $assembledFile -Force
        }
    }

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "   Generation complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Output folder: $buildDir"

    Get-ChildItem $buildDir -File | ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  - $($_.Name) ($size KB)"
    }

} catch {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "   Generation failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Err $_.Exception.Message
    exit 1
}
