# Gather — backend

Backend aplikacji Gather jest zbudowany w FastAPI. Rejestracja endpointów, walidacja danych, logika aplikacji i dostęp do danych są rozdzielone na osobne moduły.

## Uruchomienie lokalne

Wszystkie endpointy API poza `GET /api/health` wymagają prawidłowego access tokenu Cognito. Skopiuj przykładowy plik środowiskowy:

```bash
cp -n .env.example .env
```

Uzupełnij `COGNITO_REGION`, `COGNITO_USER_POOL_ID` i `COGNITO_USER_POOL_CLIENT_ID` wartościami z `terraform output`. `COGNITO_USER_POOL_CLIENT_ID` musi wskazywać klienta Cognito przeznaczonego dla frontendu. Klient nie ma sekretu; backend weryfikuje podpis, issuer, czas ważności, typ tokenu (`access`) i client ID.

Plik `.env` jest ignorowany przez Git. Następnie uruchom API z katalogu `backend/`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --env-file .env
```

API będzie dostępne pod `http://localhost:8000`, a interaktywna dokumentacja pod `http://localhost:8000/docs`.

## Docker

W głównym katalogu projektu Docker Compose ładuje `backend/.env` do obu kontenerów:

```bash
docker compose up --build
```

Po pierwszym buildzie wystarczy `docker compose up`. Frontend pobiera identyfikatory Cognito jako konfigurację runtime, nie są one wbudowywane w obraz.

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

Jedynym publicznym endpointem jest `GET /api/health`. Pozostałe ścieżki `/api` odrzucają brakujący lub nieprawidłowy token (401). Jeśli zmienne Cognito nie są skonfigurowane, endpointy chronione zwracają 503 i nie otwierają dostępu bez uwierzytelnienia. CORS origins można ustawić zmienną `CORS_ORIGINS` (lista originów rozdzielona przecinkami).

Tworzenie pokoju przyjmuje JSON, np.:

```json
{
  "name": "general",
  "topic": "Wszystko, co warto omówić"
}
```

Wiadomość przyjmuje JSON z polami `text` i opcjonalnym `media_id`. Pole `author` jest nadpisywane przez backend nazwą użytkownika z zweryfikowanego access tokenu, więc klient nie może podszyć się pod innego autora. Upload używa `multipart/form-data` z polem `file`; zwrócone `id` można przekazać jako `media_id` podczas tworzenia wiadomości.

## Struktura

```text
app/
  api/           # Endpointy i rejestracja routerów
  auth.py        # Weryfikacja podpisu i claims tokenów Cognito
  schemas/       # Walidacja danych wejściowych i wyjściowych
  services/      # Logika pokoi, wiadomości i multimediów
  repositories/  # Implementacja dostępu do danych
  errors.py      # Błędy domenowe i mapowanie na odpowiedzi HTTP
  main.py        # Aplikacja FastAPI, middleware i routery
```

Obecny magazyn w `app/repositories/memory_store.py` jest tymczasowy. Docelowo repozytorium można zastąpić integracją z AWS RDS, a zapis plików w `app/services/media.py` — integracją z S3. Uwierzytelnianie Cognito jest już wymagane dla wszystkich endpointów API poza `/api/health`.
