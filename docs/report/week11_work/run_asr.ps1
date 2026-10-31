Add-Type -AssemblyName System.Speech
$kit = 'C:\Users\DucAnh\Desktop\Hanu\MLA\report\week11_work\listen_kit'
$rows = Get-Content (Join-Path $kit 'listen_times.json') -Raw | ConvertFrom-Json
$out = @()
foreach ($r in $rows) {
    $rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $rec.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
    $rec.InitialSilenceTimeout = [TimeSpan]::FromSeconds(1)
    $rec.BabbleTimeout = [TimeSpan]::FromSeconds(2)
    $rec.EndSilenceTimeout = [TimeSpan]::FromMilliseconds(500)
    $rec.SetInputToWaveFile((Join-Path $kit $r.file))
    $texts = @()
    for ($i = 0; $i -lt 6; $i++) {
        $res = $rec.Recognize()
        if ($null -eq $res) { break }
        if ($res.Text.Trim().Length -gt 0) {
            $texts += ('{0} [{1:P0}]' -f $res.Text.Trim(), $res.Confidence)
        }
    }
    $rec.Dispose()
    $line = '{0}. {1} | may nghe: {2}' -f $r.order, $r.id, ($(if ($texts.Count) { $texts -join ' / ' } else { '(khong nhan dang duoc)' }))
    Write-Host $line
    $out += [pscustomobject]@{ order = $r.order; id = $r.id; asr = ($(if ($texts.Count) { $texts -join ' / ' } else { '' })) }
}
$out | ConvertTo-Json | Set-Content (Join-Path $kit 'asr_windows.json') -Encoding UTF8
