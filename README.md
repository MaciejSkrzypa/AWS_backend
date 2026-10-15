# Gather — backend

Backend aplikacji Gather jest zbudowany w FastAPI. Rejestracja endpointów, walidacja danych, logika aplikacji i dostęp do danych są rozdzielone na osobne moduły.

## Uruchomienie lokalne

Polecenia wykonaj z katalogu `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API będzie dostępne pod `http://localhost:8000`, a interaktywna dokumentacja pod `http://localhost:8000/docs`.

## Docker

Obraz backendu można zbudować i uruchomić samodzielnie z katalogu głównego repozytorium:

```bash
docker build -t gather-backend ./backend
docker run --rm -p 8000:8000 -v gather_uploads:/app/uploads gather-backend
```

Wolumen `gather_uploads` zachowuje przesłane pliki po usunięciu kontenera. Backend nie udostępnia obecnie trwałego magazynu dla pokoi, wiadomości ani metadanych — te dane są przechowywane w pamięci i znikają po restarcie procesu.

## Endpointy

| Metoda | Ścieżka | Opis |
| --- | --- | --- |
| `GET` | `/api/health` | Status API |
| `GET` | `/api/rooms` | Lista pokoi |
| `POST` | `/api/rooms` | Utworzenie pokoju |
| `GET` | `/api/rooms/{room_id}/messages` | Lista wiadomości w pokoju |
| `POST` | `/api/rooms/{room_id}/messages` | Wysłanie wiadomości tekstowej lub z załącznikiem |
| `POST` | `/api/media` | Przesłanie pliku graficznego, audio lub wideo (do 25 MB) |
| `GET` | `/api/media/{media_id}` | Pobranie przesłanego pliku |

Tworzenie pokoju przyjmuje JSON, np.:

```json
{
  "name": "general",
  "topic": "Wszystko, co warto omówić"
}
```

Wiadomość przyjmuje JSON z polami `author`, `text` i opcjonalnym `media_id`. Upload używa `multipart/form-data` z polem `file`; zwrócone `id` można przekazać jako `media_id` podczas tworzenia wiadomości.

## Struktura

```text
app/
  api/           # Endpointy i rejestracja routerów
  schemas/       # Walidacja danych wejściowych i wyjściowych
  services/      # Logika pokoi, wiadomości i multimediów
  repositories/  # Implementacja dostępu do danych
  errors.py      # Błędy domenowe i mapowanie na odpowiedzi HTTP
  main.py        # Aplikacja FastAPI, middleware i routery
```

Obecny magazyn w `app/repositories/memory_store.py` jest tymczasowy. Docelowo repozytorium można zastąpić integracją z AWS RDS, a zapis plików w `app/services/media.py` — integracją z S3. Uwierzytelnianie użytkowników można dodać przez AWS Cognito.
