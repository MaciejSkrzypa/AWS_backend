# Gather — backend

Backend aplikacji Gather jest zbudowany w FastAPI. Rejestracja endpointów, walidacja danych, logika aplikacji i dostęp do danych są rozdzielone na osobne moduły.

## Uruchomienie lokalne

Wszystkie endpointy API poza `GET /api/health` wymagają prawidłowego access tokenu Cognito. Po utworzeniu zasobów AWS przez Terraform wygeneruj konfigurację z outputów:

```bash
python3 scripts/sync_terraform_env.py
```

Skrypt aktualizuje `backend/.env` oraz identyfikatory Cognito w `frontend/.env` (i w istniejącym `frontend/.env.local`). Backend korzysta z domyślnego łańcucha poświadczeń AWS SDK (lokalnie AWS CLI/zmienne środowiskowe, w chmurze rola wykonawcza); przypisz tej tożsamości polityki o ARN-ach z outputów `media_access_policy_arn` i `data_access_policy_arn`. Nie dodawaj kluczy AWS do plików `.env`.

`COGNITO_USER_POOL_CLIENT_ID` musi wskazywać klienta Cognito przeznaczonego dla frontendu. Klient nie ma sekretu; backend weryfikuje podpis, issuer, czas ważności, typ tokenu (`access`) i client ID.

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

W głównym katalogu projektu Docker Compose ładuje `backend/.env` do backendu i montuje `~/.aws` tylko do odczytu, aby kontener mógł użyć profilu AWS CLI:

```bash
docker compose up --build
```

Po pierwszym buildzie wystarczy `docker compose up`. Frontend pobiera identyfikatory Cognito jako konfigurację runtime, nie są one wbudowywane w obraz.

Pliki są przesyłane bezpośrednio z przeglądarki do prywatnego bucketu S3. Pokoje, wiadomości i metadane plików są nadal przechowywane w pamięci backendu i znikają po restarcie procesu.

## Endpointy

| Metoda | Ścieżka | Opis |
| --- | --- | --- |
| `GET` | `/api/health` | Status API |
| `GET` | `/api/rooms` | Lista pokoi |
| `POST` | `/api/rooms` | Utworzenie pokoju |
| `POST` | `/api/rooms/join` | Wyszukanie i dołączenie do pokoju po kodzie |
| `GET` | `/api/rooms/{room_id}/messages` | Lista wiadomości w pokoju |
| `POST` | `/api/rooms/{room_id}/messages` | Wysłanie wiadomości tekstowej lub z załącznikiem |
| `POST` | `/api/media/upload-url` | Wygenerowanie formularza presigned POST do uploadu bezpośrednio do S3 |

Jedynym publicznym endpointem jest `GET /api/health`. Pozostałe ścieżki `/api` odrzucają brakujący lub nieprawidłowy token (401). Jeśli zmienne Cognito nie są skonfigurowane, endpointy chronione zwracają 503 i nie otwierają dostępu bez uwierzytelnienia. CORS origins można ustawić zmienną `CORS_ORIGINS` (lista originów rozdzielona przecinkami).

Tworzenie pokoju przyjmuje JSON, np.:

```json
{
  "name": "general",
  "topic": "Wszystko, co warto omówić"
}
```

Endpoint uploadu przyjmuje JSON z `filename` i `content_type`, a zwraca `id`, `upload_url` oraz pola formularza. Frontend wysyła plik metodą `POST` bezpośrednio do S3, a zwrócone `id` przekazuje jako `media_id` podczas tworzenia wiadomości. Bucket ogranicza upload do 25 MB i typów image/audio/video. Odpowiedzi wiadomości zawierają krótkotrwały presigned URL do pobrania załącznika. Tożsamość backendu otrzymuje `s3:PutObject` i `s3:GetObject` w prefiksie `media/*` oraz ograniczone `s3:ListBucket` potrzebne do odróżnienia nieprzesłanego obiektu.

Odpowiedź tworzenia pokoju zawiera wygenerowane pole `code` (10 znaków). Kod można wpisać w formularzu „Dołącz kodem”; API przyjmuje również zapis kodu z łącznikami lub spacjami. Lista pokoi oraz odczyt i wysyłanie wiadomości są ograniczone do zalogowanego twórcy pokoju i osób, które dołączyły przez kod. Samo uwierzytelnienie nie daje dostępu do pozostałych pokojów.

Pokoje, wiadomości i metadane załączników są trwale zapisywane w tabelach DynamoDB utworzonych przez Terraform. Nazwy tabel przekazuje się przez zmienne `DYNAMODB_ROOMS_TABLE`, `DYNAMODB_MESSAGES_TABLE` i `DYNAMODB_MEDIA_TABLE`; w razie braku konfiguracji API zwraca błąd 503 zamiast przechodzić na magazyn ulotny.

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

Repozytorium w `app/repositories/dynamodb.py` zapisuje pokoje, wiadomości i metadane plików w DynamoDB. Pliki binarne są w prywatnym S3. Uwierzytelnianie Cognito jest wymagane dla wszystkich endpointów API poza `/api/health`.
