# **Zadanie zaliczeniowe 2 (termin 31.05.2026) (zaawansowany)**

## **OCR/VLM RAG API: odczyt dokumentów i wyszukiwanie informacji**

### **Kontekst**

Twoim zadaniem jest zaprojektowanie i zaimplementowanie aplikacji typu REST API w FastAPI, która przyjmuje obrazy dokumentów, odczytuje ich zawartość za pomocą modelu OCR lub modelu vision-language, a następnie pozwala wyszukiwać informacje w uzyskanych tekstach z wykorzystaniem podejścia RAG.

W projekcie należy wykorzystać zbiór danych:

[https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v1](https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v1)

Aplikacja powinna symulować system, który przyjmuje dokument, odczytuje jego treść, zapisuje tekst lub strukturę JSON, a następnie umożliwia zadawanie pytań do zgromadzonych dokumentów.

---

## **Cel projektu**

Celem projektu jest stworzenie aplikacji API, która realizuje następujący przepływ:

obraz dokumentu \-\> OCR/VLM \-\> tekst lub JSON \-\> embedding \-\> baza wektorowa \-\> wyszukiwanie / odpowiedź RAG

Projekt powinien pokazać umiejętność pracy z:

FastAPI  
Pydantic  
REST API  
HTTP  
uploadem obrazów  
Dockerem  
OCR lub VLM  
bazą wektorową  
RAG  
---

## **Wymagania funkcjonalne**

Aplikacja powinna umożliwiać:

1. przesłanie obrazu dokumentu do API,  
2. uruchomienie procesu OCR lub VLM w tle,  
3. sprawdzenie statusu przetwarzania dokumentu,  
4. zapisanie odczytanego tekstu,  
5. opcjonalne zapisanie danych strukturalnych w formacie JSON,  
6. zbudowanie indeksu semantycznego na podstawie odczytanych dokumentów,  
7. wyszukiwanie dokumentów po treści,  
8. zadawanie pytań do dokumentów,  
9. zwracanie odpowiedzi wraz ze źródłami,  
10. uruchomienie aplikacji w kontenerze Docker.

---

## **Minimalne endpointy**

Aplikacja powinna udostępniać co najmniej następujące endpointy:

GET  /health  
POST /documents/upload  
GET  /documents/{document\_id}  
POST /documents/{document\_id}/index  
POST /rag/search  
POST /rag/answer  
---

## **Opis endpointów**

### **`GET /health`**

Endpoint sprawdzający stan aplikacji.

Powinien informować, czy aplikacja działa poprawnie.

---

### **`POST /documents/upload`**

Endpoint służący do przesłania obrazu dokumentu.

Dozwolone formaty:

.jpg  
.jpeg  
.png

Po otrzymaniu pliku aplikacja powinna utworzyć zadanie przetwarzania i uruchomić OCR lub VLM w tle.

Endpoint powinien zwrócić:

identyfikator dokumentu  
status przetwarzania  
---

### **`GET /documents/{document_id}`**

Endpoint służący do sprawdzenia statusu przetwarzania dokumentu.

Możliwe statusy:

queued  
processing  
completed  
failed

Po zakończeniu przetwarzania endpoint powinien zwracać:

odczytany tekst  
opcjonalnie dane strukturalne  
informacje o błędach, jeżeli wystąpiły  
---

### **`POST /documents/{document_id}/index`**

Endpoint służący do dodania odczytanego dokumentu do indeksu RAG.

Aplikacja powinna podzielić tekst na fragmenty, utworzyć embeddingi i zapisać je w bazie wektorowej lub innym indeksie semantycznym.

---

### **`POST /rag/search`**

Endpoint służący do wyszukiwania dokumentów lub fragmentów dokumentów na podstawie zapytania tekstowego.

Użytkownik podaje zapytanie, a API zwraca najbardziej pasujące fragmenty dokumentów.

---

### **`POST /rag/answer`**

Endpoint służący do zadawania pytań do dokumentów.

Aplikacja powinna:

wyszukać odpowiednie fragmenty dokumentów  
zbudować kontekst dla odpowiedzi  
wygenerować odpowiedź  
zwrócić źródła użyte do odpowiedzi  
---

## **Przykładowe pytania do systemu**

Dla paragonów:

Jaka jest kwota końcowa?  
Jakie produkty znajdują się na paragonie?  
Z jakiego sklepu pochodzi dokument?  
Czy na dokumencie występuje podatek?  
Który dokument ma najwyższą kwotę?

Dla faktur:

Kto jest sprzedawcą?  
Kto jest nabywcą?  
Jaki jest numer faktury?  
Jaka jest kwota netto?  
Jaka jest kwota brutto?  
Jaka jest stawka VAT?

Dla formularzy:

Jakie pola znajdują się w formularzu?  
Jakie odpowiedzi są przypisane do pytań?  
Kto wypełnił formularz?  
Jaka data występuje w dokumencie?  
---

## **Wymagania dotyczące OCR/VLM**

Student może użyć jednego z podejść:

klasyczny OCR, np. Tesseract, EasyOCR, PaddleOCR  
model typu Donut  
model vision-language, np. GLM, Qwen-VL, LLaVA, PaliGemma

Wynikiem przetwarzania powinien być co najmniej tekst dokumentu.

Wersja rozszerzona może zwracać dane strukturalne, np.:

nazwa sklepu  
data  
kwota końcowa  
lista produktów  
numer faktury  
sprzedawca  
nabywca  
kwota netto  
kwota brutto  
VAT  
---

## **Wymagania techniczne**

Projekt powinien zawierać:

FastAPI  
Pydantic schemas  
obsługę uploadu plików graficznych  
obsługę statusów HTTP  
bazę wektorową lub prosty indeks embeddingów  
Dockerfile  
.dockerignore  
README  
---

## **Wymagania dotyczące HTTP**

Aplikacja powinna poprawnie używać statusów HTTP, np.:

200 OK — poprawne pobranie danych  
202 Accepted — dokument przyjęty do przetwarzania  
400 Bad Request — niepoprawny plik  
404 Not Found — brak dokumentu o podanym ID  
409 Conflict — próba indeksowania dokumentu, który nie został jeszcze przetworzony  
422 Unprocessable Entity — błędne dane wejściowe  
500 Internal Server Error — błąd OCR lub VLM  
---

## **Wymagania dotyczące Dockera**

Aplikacja musi być możliwa do uruchomienia w kontenerze Docker.

Student powinien dostarczyć:

Dockerfile  
.dockerignore  
instrukcję budowania obrazu  
instrukcję uruchamiania kontenera

W README należy wyjaśnić:

czym jest Dockerfile  
czym jest .dockerignore  
czym jest docker context  
jak działają warstwy obrazu  
jak zoptymalizować czas budowy obrazu  
dlaczego kolejność instrukcji w Dockerfile ma znaczenie  
---

## **Kryteria oceny**

| Obszar | Punkty |
| ----- | ----- |
| Poprawna struktura API w FastAPI | 20 |
| Upload i obsługa obrazów | 10 |
| OCR lub VLM | 20 |
| Dane tekstowe lub strukturalne | 10 |
| Wyszukiwanie semantyczne / RAG | 20 |
| Pydantic i walidacja danych | 5 |
| Docker i `.dockerignore` | 15 |
| **Razem** | **100** |

