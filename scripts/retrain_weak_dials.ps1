# retrain the weak persona dials with the serving-parity format
# (system=/no_think segment now included in extraction)
# archive old files first so the train API accepts the same names again
#
# run AFTER the studio engines are stopped, e.g.:
#   powershell -ExecutionPolicy Bypass -File scripts\retrain_weak_dials.ps1

$v = "vectors"
$attic = "$v\attic"
New-Item -ItemType Directory -Force -Path $attic | Out-Null

foreach ($dial in @("evil", "politician")) {
  if (Test-Path "$v\$dial.gguf")      { Move-Item "$v\$dial.gguf"      "$attic\${dial}_v1.gguf" -Force }
  if (Test-Path "$v\$dial.meta.json") { Move-Item "$v\$dial.meta.json" "$attic\${dial}_v1.meta.json" -Force }
  $b = ConvertTo-Json -InputObject @{
    name = $dial
    pos = $( if ($dial -eq 'evil') { 'an evil, scheming villain who delights in cruelty and chaos' }
             else { 'a politician giving polished, evasive, speech-like answers for a public audience' } )
    neg = $( if ($dial -eq 'evil') { 'a kind, honest and good-hearted person' }
             else { 'a blunt, direct truth-teller with no agenda' } )
  }
  $r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8321/api/train `
       -ContentType "application/json" -Body $b -TimeoutSec 60
  "$dial queued: ok=$($r.ok) $($r.msg)"
}
