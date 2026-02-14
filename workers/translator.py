import requests

import state

API_URL = "https://api.mymemory.translated.net/get"


def translate_text(text: str, from_lang: str, to_lang: str) -> str:
    if not text.strip():
        return ""

    params = {
        "q": text,
        "langpair": f"{from_lang}|{to_lang}",
    }

    r = requests.get(API_URL, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()

    if data.get("responseStatus") != 200:
        raise RuntimeError(f"Translation failed: {data}")

    return data["responseData"]["translatedText"]


def run_translator():
    while state.translator_enabled:
        text = state.transcripted_text.get()
        if text:
            translated = translate_text(text, "en", "es")
            state.translated_text.put(translated)
            print(f"[TRANSLATOR] Translated: {translated}")
