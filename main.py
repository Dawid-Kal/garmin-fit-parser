import fitparse
# ściągam bibliotekę, aby móc pracować z plikiem fit w pythonie
# ma ona też wbudowaną oficjalną bazę danych od garmina


nazwa = r"Trening.fit"
# ścieżka względna zapewnia przenośność - zadziała na każdym komputerze, który posiada plik Trening.fit

# literka r, szczególnie potrzebna przy ścieżkach bezwzględnych, np: "C:\trening...", oznacza że to będzie tzw. raw string
# daje gwarancję poprawnego zinterpretowania tytułu pliku -> \n oraz \t nie zostaną odczytane jako nowa linijka, tabulator


def wyswietl_wszystko():
    # wyświetli całą zawartość pliku fit

    try:
        # Defensywne programowanie (Defensive Programming): zabezpieczenie operacji I/O (Wejście/Wyjście)
        # przed niekontrolowanym przerwaniem działania aplikacji (Crash)

        fit_file = fitparse.FitFile(nazwa)
        # Służy do załadowania, odkodowania i przetłumaczenia (deserializacji) binarnego pliku z zegarka na czytelne dla Pythona obiekty

        # Dzięki temu fit_file to inteligentny obiekt klasy Fitfile, który trzyma dane
        # Daje on gotowe funkcje (metody) i można na nim działać

        for msg_idx, message in enumerate(fit_file.get_messages()):
            # Pętla produkująca obiekty w klasie FitMessage za pomocą metody .get_messages()

            # Dzięki enumarate dostajemy indeks (msg_idx) oraz jego zawartość (message)

            print(
                f"[KOMUNIKAT #{msg_idx}] TYP: {message.name.upper()} (ID: {message.header.local_mesg_num if hasattr(message, 'header') else 'brak'})"
                # Dostaję indeks oraz typ (dzięki .name, bez niego bym dostał np. <FitMessage: record>)
                # Za pomocą if hasattr sprawdzam czy message posiada atrybut obiektu - header (nagłówek) -> jeśli tak to wypisuję zapisaną w nim liczbę (lokalną), a jak nie to 'brak'
            )

            for data in message:
                # Data to obiekt klasy FieldData
                # Chodzę po wszystkich polach danej (jednej) instancji klasy FitMessage

                jednostka = f"{data.units}" if data.units else ""
                print(f"{data.name}: {data.value}{jednostka}")
                # Wypisuje atrybuty obiektu - nazwę, wartość oraz jednostkę (jeśli istnieje)
        print("-" * 50)
    except FileNotFoundError:
        # Pliku w ogóle nie ma

        print(f"[BŁĄD UŻYTKOWNIKA]: Nie znaleziono pliku '{nazwa}' w folderze.")

    except PermissionError:
        # Plik jest ale system go zablokował

        print(f"[BŁĄD SYSTEMOWY]: Brak uprawnień do pliku '{nazwa}'.")
        print("Upewnij się, że plik nie jest otwarty w innym programie!")

    except Exception as error:
        # Wszystkie inne awarie, błędy
        # Error to nazwa błędu

        print(f"[BŁĄD KRYTYCZNY]: Wystąpił błąd podczas zrzutu: {error}")


if __name__ == "__main__":
    # Punkt wejścia do aplikacji - kod poniżej wykona się tylko wtedy, gdy plik zostanie uruchomiony jako skrypt główny (bezpośrednio), np. przez Run
    # Jeśli np. w innym programie zaimportuję odczyt_garmina, to wykona się tylko to co powyżej oraz poniżej ifa (np. tu funkcję załaduje ale jej nie wykona)
    # Stosuj gdy kod będzie używany w innym programie, bądź przez inną osobę

    wyswietl_wszystko()

# produkuję obiekt klasy Fitfile (cały jakby przedeserializowany plik fit)
# potem, za pomocą pętli for, produkuję obiekty klasy FitMessage, nazwane u mnie jako message, a potem chodzę po nich pętlą for; a instancje klasy FieldData nazywam data
