# Experiment 3 - Haystack tag/ref classification + validation, Qwen via Ollama.
# Run from the project root:   .\experiments\run_exp3.ps1
param(
    [string]$Model   = "qwen3.5:4b",
    [string]$Data    = "data\experiment3.json",
    [int]$MaxTokens  = 1200,
    [string]$OutDir  = "out"
)

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false

try {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $records = Get-Content -Path $Data -Raw -Encoding UTF8

    $prompt = @"
You are validating Project Haystack records. Use ONLY the records below. Do not invent entities, tags or relationships.

Definitions:
- marker tag: value is "m:"
- reference tag: name ends in "Ref" and the value is the id of another record
- value tag: any other tag (strings, numbers, units). The "id" tag is identity and must NOT be listed.
- kind: "site", "equip" or "point", taken from which of those marker tags is present.
- A reference is "resolved" only if the target id exists in the records; otherwise "unresolved".
- A point with no equipRef tag at all is a missing relationship (it is NOT an unresolved reference).
- A reference tag only states an association; do not rename it or infer extra semantics.

Records:
$records

Return ONLY one JSON object with exactly this shape:
{
  "entities": [ { "id": "", "kind": "", "marker_tags": [], "value_tags": [], "ref_tags": [] } ],
  "relationships": [ { "from": "", "tag": "", "to": "", "status": "resolved|unresolved" } ],
  "missing_relationships": [ { "entity": "", "expected_tag": "" } ]
}
"@

    $body = @{
        model    = $Model
        stream   = $false
        think    = $false          # remove this line if your Ollama build rejects it
        format   = "json"
        messages = @( @{ role = "user"; content = $prompt } )
        options  = @{ temperature = 0; seed = 0; num_predict = $MaxTokens }
    } | ConvertTo-Json -Depth 10

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
    $sw.Stop()

    $content = $resp.message.content
    [System.IO.File]::WriteAllText((Join-Path $OutDir "exp3_content.txt"), $content, $utf8)
    [System.IO.File]::WriteAllText((Join-Path $OutDir "exp3_response.json"), ($resp | ConvertTo-Json -Depth 10), $utf8)

    $tps = if ($resp.eval_duration) { [math]::Round($resp.eval_count / ($resp.eval_duration / 1e9), 2) } else { 0 }
    Write-Host ""
    Write-Host "Model:            $($resp.model)"
    Write-Host "Prompt tokens:    $($resp.prompt_eval_count)"
    Write-Host "Generated tokens: $($resp.eval_count)  (cap $MaxTokens)"
    Write-Host "Speed:            $tps tokens/sec"
    Write-Host "Model total:      $([math]::Round($resp.total_duration / 1e9, 2)) s"
    Write-Host "Wall clock:       $([math]::Round($sw.Elapsed.TotalSeconds, 2)) s"
    Write-Host "Done reason:      $($resp.done_reason)"
    if ($resp.done_reason -eq "length") {
        Write-Warning "Output hit the token cap - JSON is probably truncated. Re-run with -MaxTokens 2500."
    }

    Write-Host "`n--- Scoring against deterministic engine ---"
    python experiments\score_exp3.py (Join-Path $OutDir "exp3_content.txt") $Data
}
catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
    exit 1
}
