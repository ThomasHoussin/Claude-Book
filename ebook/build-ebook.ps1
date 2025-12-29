<#
.SYNOPSIS
    Genere un ebook (EPUB/PDF/MOBI) a partir des chapitres markdown.

.DESCRIPTION
    Ce script lit la configuration book.yaml, assemble tous les chapitres
    avec les pages liminaires, et genere des ebooks via Pandoc.

.PARAMETER Config
    Chemin du fichier de configuration. Defaut: config/book.yaml

.PARAMETER Format
    Format(s) de sortie: epub, pdf, mobi, all. Defaut: epub

.PARAMETER Clean
    Nettoie le dossier build avant la generation.

.PARAMETER DryRun
    Affiche les commandes sans les executer.

.EXAMPLE
    .\build-ebook.ps1
    Genere un EPUB avec la configuration par defaut.

.EXAMPLE
    .\build-ebook.ps1 -Format all
    Genere tous les formats actives.

.EXAMPLE
    .\build-ebook.ps1 -Format pdf -Verbose
    Genere un PDF avec sortie detaillee.
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Config = "config\book.yaml",

    [Parameter(Position = 1)]
    [ValidateSet("epub", "pdf", "mobi", "all")]
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
# FONCTIONS UTILITAIRES
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
    Write-Host "[ERREUR] $Message" -ForegroundColor Red
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
        throw "Fichier de configuration introuvable: $Path"
    }

    # Verifier si le module powershell-yaml est disponible
    if (-not (Get-Module -ListAvailable -Name powershell-yaml)) {
        Write-Warn "Le module powershell-yaml n'est pas installe."
        Write-Host "  Installez-le avec: Install-Module powershell-yaml -Scope CurrentUser"
        Write-Host "  Utilisation de la configuration par defaut..."

        # Configuration par defaut
        return @{
            metadata = @{
                title = "Le Club des Cinq et le Phare Abandonne"
                author = "[Auteur]"
                language = "fr-FR"
                date = (Get-Date).Year.ToString()
                rights = "Tous droits reserves"
                description = ""
            }
            cover = @{ enabled = $true; image = "assets/images/cover.jpg" }
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
                    pdf = @{ enabled = $false }
                    mobi = @{ enabled = $false }
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
        throw "Dossier des chapitres introuvable: $fullPath"
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

    # Page de titre
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

    # Page de copyright
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
            $content += "Editeur: $($metadata.publisher)"
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

    # Dedicace
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

    # Epigraphe
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

    Write-Step "Assemblage du document..."

    $chapters = Get-ConfigValue $Config "chapters"
    $headerImages = Get-ConfigValue $chapters "header_images"

    $document = @()

    # Bloc de metadonnees YAML pour Pandoc
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

    # Pages liminaires
    if (Get-ConfigValue $Config "front_matter.enabled" $true) {
        $frontMatter = New-FrontMatter $Config
        if ($frontMatter) {
            $document += $frontMatter
        }
    }

    # Chapitres
    $sourceDir = Get-ConfigValue $chapters "source_dir" "..\story\chapters"
    $pattern = Get-ConfigValue $chapters "pattern" "chapitre-*.md"

    $chapterFiles = Get-ChapterFiles -SourceDir $sourceDir -Pattern $pattern

    if ($chapterFiles.Count -eq 0) {
        throw "Aucun fichier de chapitre trouve avec le pattern: $pattern"
    }

    Write-Host "  $($chapterFiles.Count) chapitre(s) trouve(s)"

    foreach ($file in $chapterFiles) {
        $chapterName = $file.BaseName
        $chapterContent = Get-Content $file.FullName -Raw -Encoding UTF8

        # Ajouter l'image d'en-tete si configuree
        if (Get-ConfigValue $headerImages "enabled" $false) {
            $imagePath = Get-ConfigValue $headerImages "mapping.$chapterName"
            if (-not $imagePath) {
                $imagePath = Get-ConfigValue $headerImages "default"
            }
            if ($imagePath -and (Test-Path (Join-Path $ScriptDir $imagePath))) {
                $chapterContent = "![$chapterName]($imagePath)`n`n" + $chapterContent
            } elseif ($imagePath) {
                Write-Warn "Image d'en-tete introuvable pour $chapterName`: $imagePath"
            }
        }

        $document += $chapterContent
        $document += ""

        Write-Verbose "  Ajoute: $chapterName"
    }

    # Ecrire le document assemble
    $document -join "`n" | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Success "Document assemble: $OutputPath"

    return $OutputPath
}

function Build-Epub {
    param(
        [hashtable]$Config,
        [string]$SourceFile,
        [string]$OutputFile
    )

    Write-Step "Generation de l'EPUB..."

    $epubConfig = Get-ConfigValue $Config "output.formats.epub"
    $coverConfig = Get-ConfigValue $Config "cover"
    $pandocConfig = Get-ConfigValue $Config "pandoc"

    $args = @(
        $SourceFile,
        "-o", $OutputFile,
        "--toc",
        "--toc-depth", (Get-ConfigValue $epubConfig "options.toc_depth" 2)
    )

    # Version EPUB
    $epubVersion = Get-ConfigValue $epubConfig "version" 3
    if ($epubVersion -eq 2) {
        $args += "--epub-version=2"
    }

    # Image de couverture
    if (Get-ConfigValue $coverConfig "enabled" $true) {
        $coverImage = Get-ConfigValue $coverConfig "image"
        $coverPath = Join-Path $ScriptDir $coverImage
        if ($coverImage -and (Test-Path $coverPath)) {
            $args += "--epub-cover-image=$coverPath"
            Write-Host "  Couverture: $coverImage"
        } else {
            Write-Warn "Image de couverture introuvable: $coverImage"
            Write-Host "  L'EPUB sera genere sans couverture."
        }
    }

    # Feuille de styles
    $stylesheet = Get-ConfigValue $epubConfig "stylesheet"
    $stylePath = Join-Path $ScriptDir $stylesheet
    if ($stylesheet -and (Test-Path $stylePath)) {
        $args += "--css=$stylePath"
    }

    # Typographie intelligente (guillemets, tirets)
    if (Get-ConfigValue $pandocConfig "smart" $true) {
        # Pandoc 2.0+ utilise +smart dans l'extension
        # Pour les versions anterieures, on utiliserait --smart
    }

    # Niveau de decoupe
    $splitLevel = Get-ConfigValue $epubConfig "options.split_level" 1
    $args += "--split-level=$splitLevel"

    # Execution de Pandoc
    $argString = $args -join ' '
    Write-Verbose "Commande: pandoc $argString"

    if (-not $DryRun) {
        & pandoc $args 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Pandoc a echoue avec le code $LASTEXITCODE"
        }

        Write-Success "EPUB cree: $OutputFile"
        $size = [math]::Round((Get-Item $OutputFile).Length / 1KB, 2)
        Write-Host "  Taille: $size KB"
    } else {
        Write-Host "  [DRY RUN] pandoc $argString"
    }
}

function Build-Pdf {
    param(
        [hashtable]$Config,
        [string]$SourceFile,
        [string]$OutputFile
    )

    Write-Step "Generation du PDF..."

    $pdfConfig = Get-ConfigValue $Config "output.formats.pdf"
    $engine = Get-ConfigValue $pdfConfig "engine" "xelatex"

    # Verifier que le moteur PDF est disponible
    if (-not (Test-ToolExists $engine)) {
        Write-Warn "$engine n'est pas installe. Generation PDF ignoree."
        Write-Host "  Installez MiKTeX: https://miktex.org/"
        return
    }

    $args = @(
        $SourceFile,
        "-o", $OutputFile,
        "--pdf-engine=$engine"
    )

    # Configuration de page
    $paperSize = Get-ConfigValue $pdfConfig "paper_size" "a5"
    $args += "-V", "papersize=$paperSize"

    $margin = Get-ConfigValue $pdfConfig "margin"
    if ($margin) {
        $top = Get-ConfigValue $margin "top" "2cm"
        $bottom = Get-ConfigValue $margin "bottom" "2cm"
        $left = Get-ConfigValue $margin "left" "2cm"
        $right = Get-ConfigValue $margin "right" "2cm"
        $args += "-V", "geometry:top=$top"
        $args += "-V", "geometry:bottom=$bottom"
        $args += "-V", "geometry:left=$left"
        $args += "-V", "geometry:right=$right"
    }

    # Typographie
    $font = Get-ConfigValue $pdfConfig "font"
    if ($font) {
        $mainFont = Get-ConfigValue $font "main" "Linux Libertine O"
        $fontSize = Get-ConfigValue $font "size" "11pt"
        $args += "-V", "mainfont=$mainFont"
        $args += "-V", "fontsize=$fontSize"
    }

    $lineSpacing = Get-ConfigValue $pdfConfig "line_spacing" 1.3
    $args += "-V", "linestretch=$lineSpacing"

    # Table des matieres
    if (Get-ConfigValue $pdfConfig "options.toc" $true) {
        $args += "--toc"
        $args += "--toc-depth", (Get-ConfigValue $pdfConfig "options.toc_depth" 2)
    }

    # Execution de Pandoc
    $argString = $args -join ' '
    Write-Verbose "Commande: pandoc $argString"

    if (-not $DryRun) {
        & pandoc $args 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Pandoc a echoue avec le code $LASTEXITCODE"
        }

        Write-Success "PDF cree: $OutputFile"
        $size = [math]::Round((Get-Item $OutputFile).Length / 1KB, 2)
        Write-Host "  Taille: $size KB"
    } else {
        Write-Host "  [DRY RUN] pandoc $argString"
    }
}

function Build-Mobi {
    param(
        [string]$EpubFile,
        [string]$OutputFile
    )

    Write-Step "Generation du MOBI..."

    if (-not (Test-ToolExists "ebook-convert")) {
        Write-Warn "ebook-convert (Calibre) n'est pas installe. Generation MOBI ignoree."
        Write-Host "  Installez Calibre: https://calibre-ebook.com/"
        return
    }

    if (-not (Test-Path $EpubFile)) {
        Write-Warn "Fichier EPUB introuvable. Generez d'abord l'EPUB."
        return
    }

    $args = @($EpubFile, $OutputFile)
    $argString = $args -join ' '

    Write-Verbose "Commande: ebook-convert $argString"

    if (-not $DryRun) {
        & ebook-convert $args 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "ebook-convert a echoue avec le code $LASTEXITCODE"
        }

        Write-Success "MOBI cree: $OutputFile"
        $size = [math]::Round((Get-Item $OutputFile).Length / 1KB, 2)
        Write-Host "  Taille: $size KB"
    } else {
        Write-Host "  [DRY RUN] ebook-convert $argString"
    }
}

# =============================================================================
# EXECUTION PRINCIPALE
# =============================================================================

try {
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "   Generateur d'Ebook - Claude Book" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta

    # Verification des outils requis
    Write-Step "Verification des prerequis..."

    if (-not (Test-ToolExists "pandoc")) {
        throw "Pandoc n'est pas installe. Telechargez-le: https://pandoc.org/installing.html"
    }

    $pandocVersion = & pandoc --version | Select-Object -First 1
    Write-Host "  $pandocVersion"

    # Chargement de la configuration
    Write-Step "Chargement de la configuration..."

    $configPath = Join-Path $ScriptDir $Config
    $cfg = Read-YamlConfig -Path $configPath

    $title = Get-ConfigValue $cfg "metadata.title" "Sans titre"
    $author = Get-ConfigValue $cfg "metadata.author" "[Auteur]"
    Write-Host "  Titre: $title"
    Write-Host "  Auteur: $author"

    # Preparation du dossier de build
    $buildDir = Join-Path $ScriptDir (Get-ConfigValue $cfg "output.directory" "build")

    if ($Clean -or (Get-ConfigValue $cfg "build.clean_before" $true)) {
        if (Test-Path $buildDir) {
            Write-Host "  Nettoyage du dossier build..."
            Remove-Item -Path $buildDir -Recurse -Force
        }
    }

    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    # Assemblage du document
    $baseFilename = Get-ConfigValue $cfg "output.filename" "book"
    $assembledFile = Join-Path $buildDir "assembled.md"

    Build-AssembledDocument -Config $cfg -OutputPath $assembledFile

    # Generation des formats demandes
    $formats = @()
    if ($Format -eq "all") {
        if (Get-ConfigValue $cfg "output.formats.epub.enabled" $true) { $formats += "epub" }
        if (Get-ConfigValue $cfg "output.formats.pdf.enabled" $false) { $formats += "pdf" }
        if (Get-ConfigValue $cfg "output.formats.mobi.enabled" $false) { $formats += "mobi" }
    } else {
        $formats = @($Format)
    }

    if ($formats.Count -eq 0) {
        Write-Warn "Aucun format active dans la configuration."
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
            "pdf" {
                $outputFile = Join-Path $buildDir "$baseFilename.pdf"
                Build-Pdf -Config $cfg -SourceFile $assembledFile -OutputFile $outputFile
            }
            "mobi" {
                if (-not $epubFile) {
                    $epubFile = Join-Path $buildDir "$baseFilename.epub"
                    if (-not (Test-Path $epubFile)) {
                        Write-Warn "EPUB requis pour la conversion MOBI. Generation de l'EPUB..."
                        Build-Epub -Config $cfg -SourceFile $assembledFile -OutputFile $epubFile
                    }
                }
                $outputFile = Join-Path $buildDir "$baseFilename.mobi"
                Build-Mobi -EpubFile $epubFile -OutputFile $outputFile
            }
        }
    }

    # Nettoyage des fichiers intermediaires
    if (-not (Get-ConfigValue $cfg "build.keep_intermediate" $false)) {
        if (Test-Path $assembledFile) {
            Remove-Item $assembledFile -Force
        }
    }

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "   Generation terminee!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Dossier de sortie: $buildDir"

    Get-ChildItem $buildDir -File | ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  - $($_.Name) ($size KB)"
    }

} catch {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "   Echec de la generation!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Err $_.Exception.Message
    exit 1
}
