```jsonl
{"op": "scaffold_noun", "target": "MediaTranscriptionAnalysis", "description": "Automated workflow for identifying, transcribing, and categorizing recent media files."}
{"op": "scaffold_verb", "noun": "MediaTranscriptionAnalysis", "verb": "scan", "shape": "Source", "type": "FileMetadata", "description": "Identify webm/mp4 files created in the last 7 hours."}
{"op": "scaffold_verb", "noun": "MediaTranscriptionAnalysis", "verb": "convert", "shape": "Pipe", "type": "AudioMetadata", "description": "Extract or convert video files to mp3 format."}
{"op": "scaffold_verb", "noun": "MediaTranscriptionAnalysis", "verb": "transcribe", "shape": "Pipe", "type": "Transcript", "description": "Generate text transcripts from audio files using Speech-to-Text."}
{"op": "scaffold_verb", "noun": "MediaTranscriptionAnalysis", "verb": "categorize", "shape": "Sink", "type": "ClassificationResult", "description": "Analyze transcripts and categorize into Financial, AI, or Geo-political segments."}
```