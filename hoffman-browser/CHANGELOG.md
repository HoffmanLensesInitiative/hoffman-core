# Hoffman Browser - Changelog

## v0.1.0 -- 2026-03-28

### First working build

**Model:** Switched from Phi-3 Mini to Llama 3.2 3B Instruct (Q4_K_M, ~2.2GB)
- Phi-3 Mini ignored JSON instructions and wrote prose
- Llama 3.2 3B follows structured output instructions reliably
- First successful analysis: Fox News flagged outrage_engineering + war_framing on "WAR WITH IRAN"

**Architecture:**
- Electron main process extracts page text via webContents.executeJavaScript
- Local model runs entirely on CPU (gpu: false) -- no VRAM required
- Context recreated between analyses to prevent "no sequences left" error
- JSON-first parsing with natural language fallback

**Analyzer:**
- System prompt instructs model to return JSON matching flags schema
- extractJson() finds { } in any response and parses it
- parseNaturalResponse() fallback reads prose output and infers results
- 1200 char page text limit to fit within 2048 context window

**Known limitations:**
- Image text not analyzed -- OCR is next priority
- Occupy Democrats came back clean because manipulation is in meme images
- CodePink did not render fully -- user agent may need spoofing
- Analysis takes 5-12 minutes on CPU -- GPU support future work
- Context window (2048) limits page text to ~1200 chars

**Next:** OCR for image text analysis
